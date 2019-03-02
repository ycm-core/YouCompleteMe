# coding: utf-8
#
# Copyright (C) 2015-2018 YouCompleteMe contributors
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

# Intentionally not importing unicode_literals!
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycm.tests import PathToTestFile
from ycm.tests.test_utils import ( CurrentWorkingDirectory, ExtendedMock,
                                   MockVimBuffers, MockVimModule, Version,
                                   VimBuffer, VimError )
MockVimModule()

from ycm import vimsupport
from nose.tools import eq_
from hamcrest import ( assert_that, calling, contains, empty, equal_to,
                       has_entry, raises )
from mock import MagicMock, call, patch
from ycmd.utils import ToBytes
import os
import json


@patch( 'vim.eval', new_callable = ExtendedMock )
def SetLocationListsForBuffer_Current_test( vim_eval ):
  diagnostics = [ {
    'bufnr': 3,
    'filename': 'some_filename',
    'lnum': 5,
    'col': 22,
    'type': 'E',
    'valid': 1
  } ]
  current_buffer = VimBuffer( '/test', number = 3 )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    vimsupport.SetLocationListsForBuffer( 3, diagnostics )

  vim_eval.assert_has_exact_calls( [
    call( 'setloclist( 1, {0} )'.format( json.dumps( diagnostics ) ) )
  ] )


@patch( 'vim.eval', new_callable = ExtendedMock )
def SetLocationListsForBuffer_NotCurrent_test( vim_eval ):
  diagnostics = [ {
    'bufnr': 3,
    'filename': 'some_filename',
    'lnum': 5,
    'col': 22,
    'type': 'E',
    'valid': 1
  } ]
  current_buffer = VimBuffer( '/test', number = 3 )
  other_buffer = VimBuffer( '/notcurrent', number = 1 )
  with MockVimBuffers( [ current_buffer, other_buffer ], [ current_buffer ] ):
    vimsupport.SetLocationListsForBuffer( 1, diagnostics )

  vim_eval.assert_not_called()


@patch( 'vim.eval', new_callable = ExtendedMock, side_effect = [ -1, 1 ] )
def SetLocationListsForBuffer_NotVisible_test( vim_eval ):
  diagnostics = [ {
    'bufnr': 3,
    'filename': 'some_filename',
    'lnum': 5,
    'col': 22,
    'type': 'E',
    'valid': 1
  } ]
  current_buffer = VimBuffer( '/test', number = 3 )
  other_buffer = VimBuffer( '/notcurrent', number = 1 )
  with MockVimBuffers( [ current_buffer, other_buffer ], [ current_buffer ] ):
    vimsupport.SetLocationListsForBuffer( 1, diagnostics )

  vim_eval.assert_not_called()


@patch( 'vim.eval', new_callable = ExtendedMock, side_effect = [ -1, 1 ] )
def SetLocationListsForBuffer_MultipleWindows_test( vim_eval ):
  diagnostics = [ {
    'bufnr': 3,
    'filename': 'some_filename',
    'lnum': 5,
    'col': 22,
    'type': 'E',
    'valid': 1
  } ]
  current_buffer = VimBuffer( '/test', number = 3 )
  other_buffer = VimBuffer( '/notcurrent', number = 1 )
  with MockVimBuffers( [ current_buffer, other_buffer ],
                       [ current_buffer, other_buffer ] ):
    vimsupport.SetLocationListsForBuffer( 1, diagnostics )

  vim_eval.assert_has_exact_calls( [
    call( 'setloclist( 2, {0} )'.format( json.dumps( diagnostics ) ) )
  ] )


@patch( 'vim.eval', new_callable = ExtendedMock )
def SetLocationList_test( vim_eval ):
  diagnostics = [ {
    'bufnr': 3,
    'filename': 'some_filename',
    'lnum': 5,
    'col': 22,
    'type': 'E',
    'valid': 1
  } ]
  current_buffer = VimBuffer( '/test', number = 3 )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 1 ) ):
    vimsupport.SetLocationList( diagnostics )

  vim_eval.assert_has_calls( [
    call( 'setloclist( 0, {0} )'.format( json.dumps( diagnostics ) ) ),
  ] )


@patch( 'vim.eval', new_callable = ExtendedMock )
def SetLocationList_NotCurrent_test( vim_eval ):
  diagnostics = [ {
    'bufnr': 3,
    'filename': 'some_filename',
    'lnum': 5,
    'col': 22,
    'type': 'E',
    'valid': 1
  } ]
  current_buffer = VimBuffer( '/test', number = 3 )
  other_buffer = VimBuffer( '/notcurrent', number = 1 )
  with MockVimBuffers( [ current_buffer, other_buffer ],
                       [ current_buffer, other_buffer ],
                       ( 1, 1 ) ):
    vimsupport.SetLocationList( diagnostics )

  # This version does not check the current buffer and just sets the current win
  vim_eval.assert_has_exact_calls( [
    call( 'setloclist( 0, {0} )'.format( json.dumps( diagnostics ) ) ),
  ] )


@patch( 'ycm.vimsupport.VariableExists', return_value = True )
@patch( 'ycm.vimsupport.SetFittingHeightForCurrentWindow' )
@patch( 'vim.command', new_callable = ExtendedMock )
def OpenLocationList_test( vim_command, fitting_height, variable_exists ):
  vimsupport.OpenLocationList( focus = False, autoclose = True )
  vim_command.assert_has_exact_calls( [
    call( 'lopen' ),
    call( 'augroup ycmlocation' ),
    call( 'autocmd! * <buffer>' ),
    call( 'autocmd WinLeave <buffer> '
          'if bufnr( "%" ) == expand( "<abuf>" ) | q | endif' ),
    call( 'augroup END' ),
    call( 'doautocmd User YcmLocationOpened' ),
    call( 'silent! wincmd p' )
  ] )
  fitting_height.assert_called_once_with()
  variable_exists.assert_called_once_with( '#User#YcmLocationOpened' )


@patch( 'vim.command' )
def SetFittingHeightForCurrentWindow_LineWrapOn_test( vim_command, *args ):
  # Create a two lines buffer whose first line is longer than the window width.
  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'a' * 140, 'b' * 80 ] )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ) as vim:
    vim.current.window.width = 120
    vim.current.window.options[ 'wrap' ] = True
    vimsupport.SetFittingHeightForCurrentWindow()
  vim_command.assert_called_once_with( '3wincmd _' )


@patch( 'vim.command' )
def SetFittingHeightForCurrentWindow_LineWrapOff_test( vim_command, *args ):
  # Create a two lines buffer whose first line is longer than the window width.
  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'a' * 140, 'b' * 80 ] )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ) as vim:
    vim.current.window.width = 120
    vim.current.window.options[ 'wrap' ] = False
    vimsupport.SetFittingHeightForCurrentWindow()
  vim_command.assert_called_once_with( '2wincmd _' )


def AssertBuffersAreEqualAsBytes( result_buffer, expected_buffer ):
  eq_( len( result_buffer ), len( expected_buffer ) )
  for result_line, expected_line in zip( result_buffer, expected_buffer ):
    eq_( ToBytes( result_line ), ToBytes( expected_line ) )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Repl_1_test():
  # Replace with longer range
  result_buffer = VimBuffer( 'buffer', contents = [ 'This is a string' ] )
  start, end = _BuildLocations( 1, 11, 1, 17 )
  vimsupport.ReplaceChunk( start, end, 'pie', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a pie' ], result_buffer )

  # and replace again
  start, end = _BuildLocations( 1, 10, 1, 11 )
  vimsupport.ReplaceChunk( start, end, ' piece of ', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a piece of pie' ], result_buffer )

  # and once more, for luck
  start, end = _BuildLocations( 1, 1, 1, 5 )
  vimsupport.ReplaceChunk( start, end, 'How long', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'How long is a piece of pie' ],
                                result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Repl_2_test():
  # Replace with shorter range
  result_buffer = VimBuffer( 'buffer', contents = [ 'This is a string' ] )
  start, end = _BuildLocations( 1, 11, 1, 17 )
  vimsupport.ReplaceChunk( start, end, 'test', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a test' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Repl_3_test():
  # Replace with equal range
  result_buffer = VimBuffer( 'buffer', contents = [ 'This is a string' ] )
  start, end = _BuildLocations( 1, 6, 1, 8 )
  vimsupport.ReplaceChunk( start, end, 'be', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This be a string' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Add_1_test():
  # Insert at start
  result_buffer = VimBuffer( 'buffer', contents = [ 'is a string' ] )
  start, end = _BuildLocations( 1, 1, 1, 1 )
  vimsupport.ReplaceChunk( start, end, 'This ', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a string' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Add_2_test():
  # Insert at end
  result_buffer = VimBuffer( 'buffer', contents = [ 'This is a ' ] )
  start, end = _BuildLocations( 1, 11, 1, 11 )
  vimsupport.ReplaceChunk( start, end, 'string', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a string' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Add_3_test():
  # Insert in the middle
  result_buffer = VimBuffer( 'buffer', contents = [ 'This is a string' ] )
  start, end = _BuildLocations( 1, 8, 1, 8 )
  vimsupport.ReplaceChunk( start, end, ' not', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is not a string' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Del_1_test():
  # Delete from start
  result_buffer = VimBuffer( 'buffer', contents = [ 'This is a string' ] )
  start, end = _BuildLocations( 1, 1, 1, 6 )
  vimsupport.ReplaceChunk( start, end, '', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'is a string' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Del_2_test():
  # Delete from end
  result_buffer = VimBuffer( 'buffer', contents = [ 'This is a string' ] )
  start, end = _BuildLocations( 1, 10, 1, 18 )
  vimsupport.ReplaceChunk( start, end, '', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Del_3_test():
  # Delete from middle
  result_buffer = VimBuffer( 'buffer', contents = [ 'This is not a string' ] )
  start, end = _BuildLocations( 1, 9, 1, 13 )
  vimsupport.ReplaceChunk( start, end, '', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a string' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Unicode_ReplaceUnicodeChars_test():
  # Replace Unicode characters.
  result_buffer = VimBuffer(
    'buffer', contents = [ 'This Uniçø∂‰ string is in the middle' ] )
  start, end = _BuildLocations( 1, 6, 1, 20 )
  vimsupport.ReplaceChunk( start, end, 'Unicode ', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This Unicode string is in the middle' ],
                                 result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Unicode_ReplaceAfterUnicode_test():
  # Replace ASCII characters after Unicode characters in the line.
  result_buffer = VimBuffer(
    'buffer', contents = [ 'This Uniçø∂‰ string is in the middle' ] )
  start, end = _BuildLocations( 1, 30, 1, 43 )
  vimsupport.ReplaceChunk( start, end, 'fåke', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This Uniçø∂‰ string is fåke' ],
                                 result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleLine_Unicode_Grown_test():
  # Replace ASCII characters after Unicode characters in the line.
  result_buffer = VimBuffer( 'buffer', contents = [ 'a' ] )
  start, end = _BuildLocations( 1, 1, 1, 2 )
  vimsupport.ReplaceChunk( start, end, 'å', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'å' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_RemoveSingleLine_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 2, 1, 3, 1 )
  vimsupport.ReplaceChunk( start, end, '', result_buffer )
  # First line is not affected.
  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleToMultipleLines_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 2, 3, 2, 4 )
  vimsupport.ReplaceChunk( start, end, 'cccc', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aBcccc',
                                  'aCa' ], result_buffer )

  # now make another change to the second line
  start, end = _BuildLocations( 2, 2, 2, 2 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbF', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aEb',
                                  'bFBcccc',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleToMultipleLines2_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 2, 2, 2, 2 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbFb\nG', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aEb',
                                  'bFb',
                                  'GBa',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleToMultipleLines3_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 2, 2, 2, 2 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbFb\nbGb', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aEb',
                                  'bFb',
                                  'bGbBa',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleToMultipleLinesReplace_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 1, 2, 1, 4 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbFb\nbGb', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aEb',
                                  'bFb',
                                  'bGb',
                                  'aBa',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SingleToMultipleLinesReplace_2_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 1, 4, 1, 4 )
  vimsupport.ReplaceChunk( start, end, 'cccc', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAacccc',
                                  'aBa',
                                  'aCa', ], result_buffer )

  # now do a subsequent change (insert in the middle of the first line)
  start, end = _BuildLocations( 1, 2, 1, 4 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbFb\nbGb', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aEb',
                                  'bFb',
                                  'bGbcccc',
                                  'aBa',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_MultipleLinesToSingleLine_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCaaaa' ] )
  start, end = _BuildLocations( 3, 4, 3, 5 )
  vimsupport.ReplaceChunk( start, end, 'dd\ndd', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aBa',
                                  'aCadd',
                                  'ddaa' ], result_buffer )

  # make another modification applying offsets
  start, end = _BuildLocations( 3, 3, 3, 4 )
  vimsupport.ReplaceChunk( start, end, 'cccc', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aBa',
                                  'aCccccdd',
                                  'ddaa' ], result_buffer )

  # and another, for luck
  start, end = _BuildLocations( 2, 2, 3, 2 )
  vimsupport.ReplaceChunk( start, end, 'E', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aECccccdd',
                                  'ddaa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_MultipleLinesToSameMultipleLines_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa',
                                                    'aDe' ] )
  start, end = _BuildLocations( 2, 2, 3, 2 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbF', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aEb',
                                  'bFCa',
                                  'aDe' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_MultipleLinesToMoreMultipleLines_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa',
                                                    'aDe' ] )
  start, end = _BuildLocations( 2, 2, 3, 2 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbFb\nbG', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aEb',
                                  'bFb',
                                  'bGCa',
                                  'aDe' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_MultipleLinesToLessMultipleLines_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa',
                                                    'aDe' ] )
  start, end = _BuildLocations( 1, 2, 3, 2 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbF', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aEb',
                                  'bFCa',
                                  'aDe' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_MultipleLinesToEvenLessMultipleLines_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa',
                                                    'aDe' ] )
  start, end = _BuildLocations( 1, 2, 4, 2 )
  vimsupport.ReplaceChunk( start, end, 'Eb\nbF', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aEb',
                                  'bFDe' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_SpanBufferEdge_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 1, 1, 1, 3 )
  vimsupport.ReplaceChunk( start, end, 'bDb', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'bDba',
                                  'aBa',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_DeleteTextInLine_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 2, 2, 2, 3 )
  vimsupport.ReplaceChunk( start, end, '', result_buffer )
  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'aa',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_AddTextInLine_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 2, 2, 2, 2 )
  vimsupport.ReplaceChunk( start, end, 'bDb', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'abDbBa',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_ReplaceTextInLine_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'aAa',
                                                    'aBa',
                                                    'aCa' ] )
  start, end = _BuildLocations( 2, 2, 2, 3 )
  vimsupport.ReplaceChunk( start, end, 'bDb', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                  'abDba',
                                  'aCa' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_NewlineChunk_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'first line',
                                                    'second line' ] )
  start, end = _BuildLocations( 1, 11, 2, 1 )
  vimsupport.ReplaceChunk( start, end, '\n', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'first line',
                                  'second line' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunk_BeyondEndOfFile_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'first line',
                                                    'second line' ] )
  start, end = _BuildLocations( 1, 11, 3, 1 )
  vimsupport.ReplaceChunk( start, end, '\n', result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'first line' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 3 ) )
def ReplaceChunk_CursorPosition_test():
  result_buffer = VimBuffer( 'buffer', contents = [ 'bar' ] )
  start, end = _BuildLocations( 1, 1, 1, 1 )
  vimsupport.ReplaceChunk( start,
                           end,
                           'xyz\nfoo',
                           result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'xyz', 'foobar' ], result_buffer )
  # Cursor line is 0-based.
  assert_that( vimsupport.CurrentLineAndColumn(), contains( 1, 6 ) )


def _BuildLocations( start_line, start_column, end_line, end_column ):
  return {
    'line_num'  : start_line,
    'column_num': start_column,
  }, {
    'line_num'  : end_line,
    'column_num': end_column,
  }


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunksInBuffer_SortedChunks_test():
  chunks = [
    _BuildChunk( 1, 4, 1, 4, '(' ),
    _BuildChunk( 1, 11, 1, 11, ')' )
  ]

  result_buffer = VimBuffer( 'buffer', contents = [ 'CT<10 >> 2> ct' ] )
  vimsupport.ReplaceChunksInBuffer( chunks, result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'CT<(10 >> 2)> ct' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunksInBuffer_UnsortedChunks_test():
  chunks = [
    _BuildChunk( 1, 11, 1, 11, ')' ),
    _BuildChunk( 1, 4, 1, 4, '(' )
  ]

  result_buffer = VimBuffer( 'buffer', contents = [ 'CT<10 >> 2> ct' ] )
  vimsupport.ReplaceChunksInBuffer( chunks, result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'CT<(10 >> 2)> ct' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunksInBuffer_LineOverlappingChunks_test():
  chunks = [
    _BuildChunk( 1, 11, 2, 1, '\n    ' ),
    _BuildChunk( 2, 12, 3, 1, '\n    ' ),
    _BuildChunk( 3, 11, 4, 1, '\n    ' )
  ]

  result_buffer = VimBuffer( 'buffer', contents = [ 'first line',
                                                    'second line',
                                                    'third line',
                                                    'fourth line' ] )
  vimsupport.ReplaceChunksInBuffer( chunks, result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'first line',
                                  '    second line',
                                  '    third line',
                                  '    fourth line' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunksInBuffer_OutdentChunks_test():
  chunks = [
    _BuildChunk( 1,  1, 1, 5, '  ' ),
    _BuildChunk( 1, 15, 2, 9, '\n    ' ),
    _BuildChunk( 2, 20, 3, 3, '\n' )
  ]

  result_buffer = VimBuffer( 'buffer', contents = [ '    first line',
                                                    '        second line',
                                                    '    third line' ] )
  vimsupport.ReplaceChunksInBuffer( chunks, result_buffer )

  AssertBuffersAreEqualAsBytes( [ '  first line',
                                  '    second line',
                                  '  third line' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunksInBuffer_OneLineIndentingChunks_test():
  chunks = [
    _BuildChunk( 1,  8, 2,  1, '\n ' ),
    _BuildChunk( 2,  9, 2, 10, '\n  ' ),
    _BuildChunk( 2, 19, 2, 20, '\n ' )
  ]

  result_buffer = VimBuffer( 'buffer', contents = [ 'class {',
                                                    'method { statement }',
                                                    '}' ] )
  vimsupport.ReplaceChunksInBuffer( chunks, result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'class {',
                                  ' method {',
                                  '  statement',
                                  ' }',
                                  '}' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
def ReplaceChunksInBuffer_SameLocation_test():
  chunks = [
    _BuildChunk( 1, 1, 1, 1, 'this ' ),
    _BuildChunk( 1, 1, 1, 1, 'is ' ),
    _BuildChunk( 1, 1, 1, 1, 'pure ' )
  ]

  result_buffer = VimBuffer( 'buffer', contents = [ 'folly' ] )
  vimsupport.ReplaceChunksInBuffer( chunks, result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'this is pure folly' ], result_buffer )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
@patch( 'ycm.vimsupport.VariableExists', return_value = False )
@patch( 'ycm.vimsupport.SetFittingHeightForCurrentWindow' )
@patch( 'ycm.vimsupport.GetBufferNumberForFilename',
        return_value = 1,
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.BufferIsVisible',
        return_value = True,
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenFilename' )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'vim.eval', new_callable = ExtendedMock )
@patch( 'vim.command', new_callable = ExtendedMock )
def ReplaceChunks_SingleFile_Open_test( vim_command,
                                        vim_eval,
                                        post_vim_message,
                                        open_filename,
                                        buffer_is_visible,
                                        get_buffer_number_for_filename,
                                        set_fitting_height,
                                        variable_exists ):
  single_buffer_name = os.path.realpath( 'single_file' )

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', single_buffer_name )
  ]

  result_buffer = VimBuffer(
    single_buffer_name,
    contents = [
      'line1',
      'line2',
      'line3'
    ]
  )

  with patch( 'vim.buffers', [ None, result_buffer, None ] ):
    vimsupport.ReplaceChunks( chunks )

  # Ensure that we applied the replacement correctly
  eq_( result_buffer.GetLines(), [
    'replacementline2',
    'line3',
  ] )

  # GetBufferNumberForFilename is called twice:
  #  - once to the check if we would require opening the file (so that we can
  #    raise a warning)
  #  - once whilst applying the changes
  get_buffer_number_for_filename.assert_has_exact_calls( [
    call( single_buffer_name ),
    call( single_buffer_name ),
  ] )

  # BufferIsVisible is called twice for the same reasons as above
  buffer_is_visible.assert_has_exact_calls( [
    call( 1 ),
    call( 1 ),
  ] )

  # we don't attempt to open any files
  open_filename.assert_not_called()

  # But we do set the quickfix list
  vim_eval.assert_has_exact_calls( [
    call( 'setqflist( {0} )'.format( json.dumps( [ {
      'bufnr': 1,
      'filename': single_buffer_name,
      'lnum': 1,
      'col': 1,
      'text': 'replacement',
      'type': 'F'
    } ] ) ) ),
  ] )

  # And it is ReplaceChunks that prints the message showing the number of
  # changes
  post_vim_message.assert_has_exact_calls( [
    call( 'Applied 1 changes', warning = False ),
  ] )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
@patch( 'ycm.vimsupport.VariableExists', return_value = False )
@patch( 'ycm.vimsupport.SetFittingHeightForCurrentWindow' )
@patch( 'ycm.vimsupport.GetBufferNumberForFilename',
        side_effect = [ -1, -1, 1 ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.BufferIsVisible',
        side_effect = [ False, False, True ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenFilename',
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.Confirm',
        return_value = True,
        new_callable = ExtendedMock )
@patch( 'vim.eval', return_value = 10, new_callable = ExtendedMock )
@patch( 'vim.command', new_callable = ExtendedMock )
def ReplaceChunks_SingleFile_NotOpen_test( vim_command,
                                           vim_eval,
                                           confirm,
                                           post_vim_message,
                                           open_filename,
                                           buffer_is_visible,
                                           get_buffer_number_for_filename,
                                           set_fitting_height,
                                           variable_exists ):
  single_buffer_name = os.path.realpath( 'single_file' )

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', single_buffer_name )
  ]

  result_buffer = VimBuffer(
    single_buffer_name,
    contents = [
      'line1',
      'line2',
      'line3'
    ]
  )

  with patch( 'vim.buffers', [ None, result_buffer, None ] ):
    vimsupport.ReplaceChunks( chunks )

  # We checked if it was OK to open the file
  confirm.assert_has_exact_calls( [
    call( vimsupport.FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT.format( 1 ) )
  ] )

  # Ensure that we applied the replacement correctly
  eq_( result_buffer.GetLines(), [
    'replacementline2',
    'line3',
  ] )

  # GetBufferNumberForFilename is called 3 times. The return values are set in
  # the @patch call above:
  #  - once to the check if we would require opening the file (so that we can
  #    raise a warning) (-1 return)
  #  - once whilst applying the changes (-1 return)
  #  - finally after calling OpenFilename (1 return)
  get_buffer_number_for_filename.assert_has_exact_calls( [
    call( single_buffer_name ),
    call( single_buffer_name ),
    call( single_buffer_name ),
  ] )

  # BufferIsVisible is called 3 times for the same reasons as above, with the
  # return of each one
  buffer_is_visible.assert_has_exact_calls( [
    call( -1 ),
    call( -1 ),
    call( 1 ),
  ] )

  # We open 'single_file' as expected.
  open_filename.assert_called_with( single_buffer_name, {
    'focus': True,
    'fix': True,
    'size': 10
  } )

  # And close it again, then show the quickfix window.
  vim_command.assert_has_exact_calls( [
    call( 'lclose' ),
    call( 'hide' ),
  ] )

  # And update the quickfix list
  vim_eval.assert_has_exact_calls( [
    call( '&previewheight' ),
    call( 'setqflist( {0} )'.format( json.dumps( [ {
      'bufnr': 1,
      'filename': single_buffer_name,
      'lnum': 1,
      'col': 1,
      'text': 'replacement',
      'type': 'F'
    } ] ) ) ),
  ] )

  # And it is ReplaceChunks that prints the message showing the number of
  # changes
  post_vim_message.assert_has_exact_calls( [
    call( 'Applied 1 changes', warning = False ),
  ] )


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
@patch( 'ycm.vimsupport.VariableExists', return_value = False )
@patch( 'ycm.vimsupport.SetFittingHeightForCurrentWindow' )
@patch( 'ycm.vimsupport.GetBufferNumberForFilename',
        side_effect = [ -1, 1 ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.BufferIsVisible',
        side_effect = [ False, True ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenFilename',
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.Confirm',
        return_value = True,
        new_callable = ExtendedMock )
@patch( 'vim.eval', return_value = 10, new_callable = ExtendedMock )
@patch( 'vim.command', new_callable = ExtendedMock )
def ReplaceChunks_SingleFile_NotOpen_Silent_test(
  vim_command,
  vim_eval,
  confirm,
  post_vim_message,
  open_filename,
  buffer_is_visible,
  get_buffer_number_for_filename,
  set_fitting_height,
  variable_exists ):

  # This test is the same as ReplaceChunks_SingleFile_NotOpen_test, but we pass
  # the silent flag, as used by post-complete actions, and shows the stuff we
  # _don't_ call in that case.

  single_buffer_name = os.path.realpath( 'single_file' )

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', single_buffer_name )
  ]

  result_buffer = VimBuffer(
    single_buffer_name,
    contents = [
      'line1',
      'line2',
      'line3'
    ]
  )

  with patch( 'vim.buffers', [ None, result_buffer, None ] ):
    vimsupport.ReplaceChunks( chunks, silent=True )

  # We didn't check if it was OK to open the file (silent)
  confirm.assert_not_called()

  # Ensure that we applied the replacement correctly
  eq_( result_buffer.GetLines(), [
    'replacementline2',
    'line3',
  ] )

  # GetBufferNumberForFilename is called 2 times. The return values are set in
  # the @patch call above:
  #  - once whilst applying the changes (-1 return)
  #  - finally after calling OpenFilename (1 return)
  get_buffer_number_for_filename.assert_has_exact_calls( [
    call( single_buffer_name ),
    call( single_buffer_name ),
  ] )

  # BufferIsVisible is called 2 times for the same reasons as above, with the
  # return of each one
  buffer_is_visible.assert_has_exact_calls( [
    call( -1 ),
    call( 1 ),
  ] )

  # We open 'single_file' as expected.
  open_filename.assert_called_with( single_buffer_name, {
    'focus': True,
    'fix': True,
    'size': 10
  } )

  # And close it again, but don't show the quickfix window
  vim_command.assert_has_exact_calls( [
    call( 'lclose' ),
    call( 'hide' ),
  ] )
  set_fitting_height.assert_not_called()

  # But we _don't_ update the QuickFix list
  vim_eval.assert_has_exact_calls( [
    call( '&previewheight' ),
  ] )

  # And we don't print a message either
  post_vim_message.assert_not_called()


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
@patch( 'ycm.vimsupport.GetBufferNumberForFilename',
        side_effect = [ -1, -1, 1 ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.BufferIsVisible',
        side_effect = [ False, False, True ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenFilename',
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.PostVimMessage',
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.Confirm',
        return_value = False,
        new_callable = ExtendedMock )
@patch( 'vim.eval',
        return_value = 10,
        new_callable = ExtendedMock )
@patch( 'vim.command', new_callable = ExtendedMock )
def ReplaceChunks_User_Declines_To_Open_File_test(
                                           vim_command,
                                           vim_eval,
                                           confirm,
                                           post_vim_message,
                                           open_filename,
                                           buffer_is_visible,
                                           get_buffer_number_for_filename ):

  # Same as above, except the user selects Cancel when asked if they should
  # allow us to open lots of (ahem, 1) file.
  single_buffer_name = os.path.realpath( 'single_file' )

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', single_buffer_name )
  ]

  result_buffer = VimBuffer(
    single_buffer_name,
    contents = [
      'line1',
      'line2',
      'line3'
    ]
  )

  with patch( 'vim.buffers', [ None, result_buffer, None ] ):
    vimsupport.ReplaceChunks( chunks )

  # We checked if it was OK to open the file
  confirm.assert_has_exact_calls( [
    call( vimsupport.FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT.format( 1 ) )
  ] )

  # Ensure that buffer is not changed
  eq_( result_buffer.GetLines(), [
    'line1',
    'line2',
    'line3',
  ] )

  # GetBufferNumberForFilename is called once. The return values are set in
  # the @patch call above:
  #  - once to the check if we would require opening the file (so that we can
  #    raise a warning) (-1 return)
  get_buffer_number_for_filename.assert_has_exact_calls( [
    call( single_buffer_name ),
  ] )

  # BufferIsVisible is called once for the above file, which wasn't visible.
  buffer_is_visible.assert_has_exact_calls( [
    call( -1 ),
  ] )

  # We don't attempt to open any files or update any quickfix list or anything
  # like that
  open_filename.assert_not_called()
  vim_eval.assert_not_called()
  vim_command.assert_not_called()
  post_vim_message.assert_not_called()


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
@patch( 'ycm.vimsupport.GetBufferNumberForFilename',
        side_effect = [ -1, -1, 1 ],
        new_callable = ExtendedMock )
# Key difference is here: In the final check, BufferIsVisible returns False
@patch( 'ycm.vimsupport.BufferIsVisible',
        side_effect = [ False, False, False ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenFilename',
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.PostVimMessage',
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.Confirm',
        return_value = True,
        new_callable = ExtendedMock )
@patch( 'vim.eval',
        return_value = 10,
        new_callable = ExtendedMock )
@patch( 'vim.command',
        new_callable = ExtendedMock )
def ReplaceChunks_User_Aborts_Opening_File_test(
                                           vim_command,
                                           vim_eval,
                                           confirm,
                                           post_vim_message,
                                           open_filename,
                                           buffer_is_visible,
                                           get_buffer_number_for_filename ):

  # Same as above, except the user selects Abort or Quick during the
  # "swap-file-found" dialog
  single_buffer_name = os.path.realpath( 'single_file' )

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', single_buffer_name )
  ]

  result_buffer = VimBuffer(
    single_buffer_name,
    contents = [
      'line1',
      'line2',
      'line3'
    ]
  )

  with patch( 'vim.buffers', [ None, result_buffer, None ] ):
    assert_that( calling( vimsupport.ReplaceChunks ).with_args( chunks ),
                 raises( RuntimeError,
                  'Unable to open file: .+single_file\n'
                  'FixIt/Refactor operation aborted prior to completion. '
                  'Your files have not been fully updated. '
                  'Please use undo commands to revert the applied changes.' ) )

  # We checked if it was OK to open the file
  confirm.assert_has_exact_calls( [
    call( vimsupport.FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT.format( 1 ) )
  ] )

  # Ensure that buffer is not changed
  eq_( result_buffer.GetLines(), [
    'line1',
    'line2',
    'line3',
  ] )

  # We tried to open this file
  open_filename.assert_called_with( single_buffer_name, {
    'focus': True,
    'fix': True,
    'size': 10
  } )
  vim_eval.assert_called_with( "&previewheight" )

  # But raised an exception before issuing the message at the end
  post_vim_message.assert_not_called()


@patch( 'vim.current.window.cursor', ( 1, 1 ) )
@patch( 'ycm.vimsupport.VariableExists', return_value = False )
@patch( 'ycm.vimsupport.SetFittingHeightForCurrentWindow' )
@patch( 'ycm.vimsupport.GetBufferNumberForFilename', side_effect = [
          22, # first_file (check)
          -1, # second_file (check)
          22, # first_file (apply)
          -1, # second_file (apply)
          19, # second_file (check after open)
        ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.BufferIsVisible', side_effect = [
          True,  # first_file (check)
          False, # second_file (check)
          True,  # first_file (apply)
          False, # second_file (apply)
          True,  # side_effect (check after open)
        ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenFilename',
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.PostVimMessage',
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.Confirm', return_value = True,
        new_callable = ExtendedMock )
@patch( 'vim.eval', return_value = 10,
        new_callable = ExtendedMock )
@patch( 'vim.command',
        new_callable = ExtendedMock )
def ReplaceChunks_MultiFile_Open_test( vim_command,
                                       vim_eval,
                                       confirm,
                                       post_vim_message,
                                       open_filename,
                                       buffer_is_visible,
                                       get_buffer_number_for_filename,
                                       set_fitting_height,
                                       variable_exists ):

  # Chunks are split across 2 files, one is already open, one isn't
  first_buffer_name = os.path.realpath( '1_first_file' )
  second_buffer_name = os.path.realpath( '2_second_file' )

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'first_file_replacement ', first_buffer_name ),
    _BuildChunk( 2, 1, 2, 1, 'second_file_replacement ', second_buffer_name ),
  ]

  first_file = VimBuffer(
    first_buffer_name,
    number = 22,
    contents = [
      'line1',
      'line2',
      'line3',
    ]
  )
  second_file = VimBuffer(
    second_buffer_name,
    number = 19,
    contents = [
      'another line1',
      'ACME line2',
    ]
  )

  vim_buffers = [ None ] * 23
  vim_buffers[ 22 ] = first_file
  vim_buffers[ 19 ] = second_file

  with patch( 'vim.buffers', vim_buffers ):
    vimsupport.ReplaceChunks( chunks )

  # We checked for the right file names
  get_buffer_number_for_filename.assert_has_exact_calls( [
    call( first_buffer_name ),
    call( second_buffer_name ),
    call( first_buffer_name ),
    call( second_buffer_name ),
    call( second_buffer_name ),
  ] )

  # We checked if it was OK to open the file
  confirm.assert_has_exact_calls( [
    call( vimsupport.FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT.format( 1 ) )
  ] )

  # Ensure that buffers are updated
  eq_( second_file.GetLines(), [
    'another line1',
    'second_file_replacement ACME line2',
  ] )
  eq_( first_file.GetLines(), [
    'first_file_replacement line2',
    'line3',
  ] )

  # We open '2_second_file' as expected.
  open_filename.assert_called_with( second_buffer_name, {
    'focus': True,
    'fix': True,
    'size': 10
  } )

  # And close it again, then show the quickfix window.
  vim_command.assert_has_exact_calls( [
    call( 'lclose' ),
    call( 'hide' ),
  ] )

  # And update the quickfix list with each entry
  vim_eval.assert_has_exact_calls( [
    call( '&previewheight' ),
    call( 'setqflist( {0} )'.format( json.dumps( [ {
      'bufnr': 22,
      'filename': first_buffer_name,
      'lnum': 1,
      'col': 1,
      'text': 'first_file_replacement ',
      'type': 'F'
    }, {
      'bufnr': 19,
      'filename': second_buffer_name,
      'lnum': 2,
      'col': 1,
      'text': 'second_file_replacement ',
      'type': 'F'
    } ] ) ) ),
  ] )

  # And it is ReplaceChunks that prints the message showing the number of
  # changes
  post_vim_message.assert_has_exact_calls( [
    call( 'Applied 2 changes', warning = False ),
  ] )


def _BuildChunk( start_line,
                 start_column,
                 end_line,
                 end_column,
                 replacement_text, filepath='test_file_name' ):
  return {
    'range': {
      'start': {
        'filepath': filepath,
        'line_num': start_line,
        'column_num': start_column,
      },
      'end': {
        'filepath': filepath,
        'line_num': end_line,
        'column_num': end_column,
      },
    },
    'replacement_text': replacement_text
  }


def GetDiagnosticMatchPattern_ErrorInMiddleOfLine_test():
  current_buffer = VimBuffer(
    'some_file',
    contents = [ 'Highlight this error please' ]
  )

  with patch( 'vim.current.buffer', current_buffer ):
    assert_that(
      vimsupport.GetDiagnosticMatchPattern( 1, 16, 1, 21 ),
      equal_to( '\\%1l\\%16c\\_.\\{-}\\%1l\\%21c' )
    )


def AddDiagnosticSyntaxMatch_WarningAtEndOfLine_test():
  current_buffer = VimBuffer(
    'some_file',
    contents = [ 'Highlight this warning' ]
  )

  with patch( 'vim.current.buffer', current_buffer ):
    assert_that(
      vimsupport.GetDiagnosticMatchPattern( 1, 16, 1, 23 ),
      equal_to( '\\%1l\\%16c\\_.\\{-}\\%1l\\%23c' )
    )


def AddDiagnosticSyntaxMatch_UnicodeAtEndOfLine_test():
  current_buffer = VimBuffer(
    'some_file',
    contents = [ 'Highlight unicøde' ]
  )

  with patch( 'vim.current.buffer', current_buffer ):
    assert_that(
      vimsupport.GetDiagnosticMatchPattern( 1, 16, 1, 19 ),
      equal_to( '\\%1l\\%16c\\_.\\{-}\\%1l\\%19c' )
    )


@patch( 'vim.command', new_callable=ExtendedMock )
@patch( 'vim.current', new_callable=ExtendedMock )
def WriteToPreviewWindow_test( vim_current, vim_command ):
  vim_current.window.options.__getitem__ = MagicMock( return_value = True )

  vimsupport.WriteToPreviewWindow( "test" )

  vim_command.assert_has_exact_calls( [
    call( 'silent! pclose!' ),
    call( 'silent! pedit! _TEMP_FILE_' ),
    call( 'silent! wincmd P' ),
    call( 'silent! wincmd p' ) ] )

  vim_current.buffer.__setitem__.assert_called_with(
      slice( None, None, None ), [ 'test' ] )

  vim_current.buffer.options.__setitem__.assert_has_exact_calls( [
    call( 'modifiable', True ),
    call( 'readonly', False ),
    call( 'buftype', 'nofile' ),
    call( 'bufhidden', 'wipe' ),
    call( 'buflisted', False ),
    call( 'swapfile', False ),
    call( 'modifiable', False ),
    call( 'modified', False ),
    call( 'readonly', True ),
  ], any_order = True )


@patch( 'vim.current' )
def WriteToPreviewWindow_MultiLine_test( vim_current ):
  vim_current.window.options.__getitem__ = MagicMock( return_value = True )
  vimsupport.WriteToPreviewWindow( "test\ntest2" )

  vim_current.buffer.__setitem__.assert_called_with(
      slice( None, None, None ), [ 'test', 'test2' ] )


@patch( 'vim.command', new_callable=ExtendedMock )
@patch( 'vim.current', new_callable=ExtendedMock )
def WriteToPreviewWindow_JumpFail_test( vim_current, vim_command ):
  vim_current.window.options.__getitem__ = MagicMock( return_value = False )

  vimsupport.WriteToPreviewWindow( "test" )

  vim_command.assert_has_exact_calls( [
    call( 'silent! pclose!' ),
    call( 'silent! pedit! _TEMP_FILE_' ),
    call( 'silent! wincmd P' ),
    call( 'redraw' ),
    call( "echo 'test'" ),
  ] )

  vim_current.buffer.__setitem__.assert_not_called()
  vim_current.buffer.options.__setitem__.assert_not_called()


@patch( 'vim.command', new_callable=ExtendedMock )
@patch( 'vim.current', new_callable=ExtendedMock )
def WriteToPreviewWindow_JumpFail_MultiLine_test( vim_current, vim_command ):

  vim_current.window.options.__getitem__ = MagicMock( return_value = False )

  vimsupport.WriteToPreviewWindow( "test\ntest2" )

  vim_command.assert_has_exact_calls( [
    call( 'silent! pclose!' ),
    call( 'silent! pedit! _TEMP_FILE_' ),
    call( 'silent! wincmd P' ),
    call( 'redraw' ),
    call( "echo 'test'" ),
    call( "echo 'test2'" ),
  ] )

  vim_current.buffer.__setitem__.assert_not_called()
  vim_current.buffer.options.__setitem__.assert_not_called()


def BufferIsVisibleForFilename_test():
  visible_buffer = VimBuffer( 'visible_filename', number = 1 )
  hidden_buffer = VimBuffer( 'hidden_filename', number = 2 )

  with MockVimBuffers( [ visible_buffer, hidden_buffer ], [ visible_buffer ] ):
    eq_( vimsupport.BufferIsVisibleForFilename( 'visible_filename' ), True )
    eq_( vimsupport.BufferIsVisibleForFilename( 'hidden_filename' ), False )
    eq_( vimsupport.BufferIsVisibleForFilename( 'another_filename' ), False )


def CloseBuffersForFilename_test():
  current_buffer = VimBuffer( 'some_filename', number = 2 )
  other_buffer = VimBuffer( 'some_filename', number = 5 )

  with MockVimBuffers( [ current_buffer, other_buffer ],
                       [ current_buffer ] ) as vim:
    vimsupport.CloseBuffersForFilename( 'some_filename' )

  assert_that( vim.buffers, empty() )


@patch( 'vim.command', new_callable = ExtendedMock )
@patch( 'vim.current', new_callable = ExtendedMock )
def OpenFilename_test( vim_current, vim_command ):
  # Options used to open a logfile.
  options = {
    'size': vimsupport.GetIntValue( '&previewheight' ),
    'fix': True,
    'focus': False,
    'watch': True,
    'position': 'end'
  }

  vimsupport.OpenFilename( __file__, options )

  vim_command.assert_has_exact_calls( [
    call( '12split {0}'.format( __file__ ) ),
    call( "exec "
          "'au BufEnter <buffer> :silent! checktime {0}'".format( __file__ ) ),
    call( 'silent! normal! Gzz' ),
    call( 'silent! wincmd p' )
  ] )

  vim_current.buffer.options.__setitem__.assert_has_exact_calls( [
    call( 'autoread', True ),
  ] )

  vim_current.window.options.__setitem__.assert_has_exact_calls( [
    call( 'winfixheight', True )
  ] )


def GetUnsavedAndSpecifiedBufferData_EncodedUnicodeCharsInBuffers_test():
  filepath = os.path.realpath( 'filename' )
  contents = [ ToBytes( u'abc' ), ToBytes( u'fДa' ) ]
  vim_buffer = VimBuffer( filepath, contents = contents )

  with patch( 'vim.buffers', [ vim_buffer ] ):
    assert_that( vimsupport.GetUnsavedAndSpecifiedBufferData( vim_buffer,
                                                              filepath ),
                 has_entry( filepath,
                            has_entry( u'contents', u'abc\nfДa\n' ) ) )


def GetBufferFilepath_NoBufferName_UnicodeWorkingDirectory_test():
  vim_buffer = VimBuffer( '', number = 42 )
  unicode_dir = PathToTestFile( u'uni¢𐍈d€' )
  with CurrentWorkingDirectory( unicode_dir ):
    assert_that( vimsupport.GetBufferFilepath( vim_buffer ),
                 equal_to( os.path.join( unicode_dir, '42' ) ) )


# NOTE: Vim returns byte offsets for columns, not actual character columns. This
# makes 'ДД' have 4 columns: column 0, column 2 and column 4.
@patch( 'vim.current.line', ToBytes( 'ДДaa' ) )
@patch( 'ycm.vimsupport.CurrentColumn', side_effect = [ 4 ] )
def TextBeforeCursor_EncodedUnicode_test( *args ):
  eq_( vimsupport.TextBeforeCursor(), u'ДД' )


# NOTE: Vim returns byte offsets for columns, not actual character columns. This
# makes 'ДД' have 4 columns: column 0, column 2 and column 4.
@patch( 'vim.current.line', ToBytes( 'aaДД' ) )
@patch( 'ycm.vimsupport.CurrentColumn', side_effect = [ 2 ] )
def TextAfterCursor_EncodedUnicode_test( *args ):
  eq_( vimsupport.TextAfterCursor(), u'ДД' )


@patch( 'vim.current.line', ToBytes( 'fДa' ) )
def CurrentLineContents_EncodedUnicode_test( *args ):
  eq_( vimsupport.CurrentLineContents(), u'fДa' )


@patch( 'vim.eval', side_effect = lambda x: x )
def VimExpressionToPythonType_IntAsUnicode_test( *args ):
  eq_( vimsupport.VimExpressionToPythonType( '123' ), 123 )


@patch( 'vim.eval', side_effect = lambda x: x )
def VimExpressionToPythonType_IntAsBytes_test( *args ):
  eq_( vimsupport.VimExpressionToPythonType( ToBytes( '123' ) ), 123 )


@patch( 'vim.eval', side_effect = lambda x: x )
def VimExpressionToPythonType_StringAsUnicode_test( *args ):
  eq_( vimsupport.VimExpressionToPythonType( 'foo' ), 'foo' )


@patch( 'vim.eval', side_effect = lambda x: x )
def VimExpressionToPythonType_StringAsBytes_test( *args ):
  eq_( vimsupport.VimExpressionToPythonType( ToBytes( 'foo' ) ), 'foo' )


@patch( 'vim.eval', side_effect = lambda x: x )
def VimExpressionToPythonType_ListPassthrough_test( *args ):
  eq_( vimsupport.VimExpressionToPythonType( [ 1, 2 ] ), [ 1, 2 ] )


@patch( 'vim.eval', side_effect = lambda x: x )
def VimExpressionToPythonType_ObjectPassthrough_test( *args ):
  eq_( vimsupport.VimExpressionToPythonType( { 1: 2 } ), { 1: 2 } )


@patch( 'vim.eval', side_effect = lambda x: x )
def VimExpressionToPythonType_GeneratorPassthrough_test( *args ):
  gen = ( x**2 for x in [ 1, 2, 3 ] )
  eq_( vimsupport.VimExpressionToPythonType( gen ), gen )


@patch( 'vim.eval',
        new_callable = ExtendedMock,
        side_effect = [ None, 2, None ] )
def SelectFromList_LastItem_test( vim_eval ):
  eq_( vimsupport.SelectFromList( 'test', [ 'a', 'b' ] ),
       1 )

  vim_eval.assert_has_exact_calls( [
    call( 'inputsave()' ),
    call( 'inputlist( ["test", "1: a", "2: b"] )' ),
    call( 'inputrestore()' )
  ] )


@patch( 'vim.eval',
        new_callable = ExtendedMock,
        side_effect = [ None, 1, None ] )
def SelectFromList_FirstItem_test( vim_eval ):
  eq_( vimsupport.SelectFromList( 'test', [ 'a', 'b' ] ),
       0 )

  vim_eval.assert_has_exact_calls( [
    call( 'inputsave()' ),
    call( 'inputlist( ["test", "1: a", "2: b"] )' ),
    call( 'inputrestore()' )
  ] )


@patch( 'vim.eval', side_effect = [ None, 3, None ] )
def SelectFromList_OutOfRange_test( vim_eval ):
  assert_that( calling( vimsupport.SelectFromList ).with_args( 'test',
                                                               [ 'a', 'b' ] ),
               raises( RuntimeError, vimsupport.NO_SELECTION_MADE_MSG ) )


@patch( 'vim.eval', side_effect = [ None, 0, None ] )
def SelectFromList_SelectPrompt_test( vim_eval ):
  assert_that( calling( vimsupport.SelectFromList ).with_args( 'test',
                                                             [ 'a', 'b' ] ),
               raises( RuntimeError, vimsupport.NO_SELECTION_MADE_MSG ) )


@patch( 'vim.eval', side_effect = [ None, -199, None ] )
def SelectFromList_Negative_test( vim_eval ):
  assert_that( calling( vimsupport.SelectFromList ).with_args( 'test',
                                                               [ 'a', 'b' ] ),
               raises( RuntimeError, vimsupport.NO_SELECTION_MADE_MSG ) )


def Filetypes_IntegerFiletype_test():
  current_buffer = VimBuffer( 'buffer', number = 1, filetype = '42' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    assert_that( vimsupport.CurrentFiletypes(), contains( '42' ) )
    assert_that( vimsupport.GetBufferFiletypes( 1 ), contains( '42' ) )
    assert_that( vimsupport.FiletypesForBuffer( current_buffer ),
                 contains( '42' ) )


@patch( 'ycm.vimsupport.VariableExists', return_value = False )
@patch( 'ycm.vimsupport.SearchInCurrentBuffer', return_value = 0 )
@patch( 'vim.current' )
def InsertNamespace_insert_test( vim_current, *args ):
  contents = [ '',
               'namespace Taqueria {',
               '',
               '  int taco = Math' ]
  vim_current.buffer = VimBuffer( '', contents = contents )
  vim_current.window.cursor = ( 1, 1 )

  vimsupport.InsertNamespace( 'System' )

  expected_buffer = [ 'using System;',
                      '',
                      'namespace Taqueria {',
                      '',
                      '  int taco = Math' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, vim_current.buffer )


@patch( 'ycm.vimsupport.VariableExists', return_value = False )
@patch( 'ycm.vimsupport.SearchInCurrentBuffer', return_value = 2 )
@patch( 'vim.current' )
def InsertNamespace_append_test( vim_current, *args ):
  contents = [ 'namespace Taqueria {',
               '  using System;',
               '',
               '  class Tasty {',
               '    int taco;',
               '    List salad = new List' ]
  vim_current.buffer = VimBuffer( '', contents = contents )
  vim_current.window.cursor = ( 1, 1 )

  vimsupport.InsertNamespace( 'System.Collections' )

  expected_buffer = [ 'namespace Taqueria {',
                      '  using System;',
                      '  using System.Collections;',
                      '',
                      '  class Tasty {',
                      '    int taco;',
                      '    List salad = new List' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, vim_current.buffer )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_SameFile_SameBuffer_NoSwapFile_test( vim_command ):
  # No 'u' prefix for the current buffer name string to simulate Vim returning
  # bytes on Python 2 but unicode on Python 3.
  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ) as vim:
    vimsupport.JumpToLocation( os.path.realpath( u'uni¢𐍈d€' ),
                               2,
                               5,
                               'aboveleft',
                               'same-buffer' )

    assert_that( vim.current.window.cursor, equal_to( ( 2, 4 ) ) )
    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( 'normal! zz' )
    ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_SameBuffer_Unmodified_test( vim_command ):
  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ) as vim:
    target_name = os.path.realpath( u'different_uni¢𐍈d€' )

    vimsupport.JumpToLocation( target_name, 2, 5, 'belowright', 'same-buffer' )

    assert_that( vim.current.window.cursor, equal_to( ( 2, 4 ) ) )
    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( u'keepjumps belowright edit {0}'.format( target_name ) ),
      call( 'normal! zz' )
    ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_SameBuffer_Modified_CannotHide_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€', modified = True )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ) as vim:
    target_name = os.path.realpath( u'different_uni¢𐍈d€' )

    vimsupport.JumpToLocation( target_name, 2, 5, 'botright', 'same-buffer' )

    assert_that( vim.current.window.cursor, equal_to( ( 2, 4 ) ) )
    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( u'keepjumps botright split {0}'.format( target_name ) ),
      call( 'normal! zz' )
    ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_SameBuffer_Modified_CanHide_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€', modified = True, bufhidden = "hide" )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ) as vim:
    target_name = os.path.realpath( u'different_uni¢𐍈d€' )

    vimsupport.JumpToLocation( target_name, 2, 5, 'leftabove', 'same-buffer' )

    assert_that( vim.current.window.cursor, equal_to( ( 2, 4 ) ) )
    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( u'keepjumps leftabove edit {0}'.format( target_name ) ),
      call( 'normal! zz' )
    ] )


@patch( 'vim.command',
        side_effect = [ None, VimError( 'Unknown code' ), None ] )
def JumpToLocation_DifferentFile_SameBuffer_SwapFile_Unexpected_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    assert_that(
      calling( vimsupport.JumpToLocation ).with_args(
        os.path.realpath( u'different_uni¢𐍈d€' ),
        2,
        5,
        'rightbelow',
        'same-buffer' ),
      raises( VimError, 'Unknown code' )
    )


@patch( 'vim.command',
        new_callable = ExtendedMock,
        side_effect = [ None, VimError( 'E325' ), None ] )
def JumpToLocation_DifferentFile_SameBuffer_SwapFile_Quit_test( vim_command ):
  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    target_name = os.path.realpath( u'different_uni¢𐍈d€' )

    vimsupport.JumpToLocation( target_name, 2, 5, 'topleft', 'same-buffer' )

    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( u'keepjumps topleft edit {0}'.format( target_name ) )
    ] )


@patch( 'vim.command',
        new_callable = ExtendedMock,
        side_effect = [ None, KeyboardInterrupt, None ] )
def JumpToLocation_DifferentFile_SameBuffer_SwapFile_Abort_test( vim_command ):
  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    target_name = os.path.realpath( u'different_uni¢𐍈d€' )

    vimsupport.JumpToLocation( target_name, 2, 5, 'vertical', 'same-buffer' )

    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( u'keepjumps vertical edit {0}'.format( target_name ) )
    ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_Split_CurrentTab_NotAlreadyOpened_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  current_window = MagicMock( buffer = current_buffer )
  current_tab = MagicMock( windows = [ current_window ] )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ) as vim:
    vim.current.tabpage = current_tab

    target_name = os.path.realpath( u'different_uni¢𐍈d€' )

    vimsupport.JumpToLocation( target_name,
                               2,
                               5,
                               'aboveleft',
                               'split-or-existing-window' )

    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( u'keepjumps aboveleft split {0}'.format( target_name ) ),
      call( 'normal! zz' )
    ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_Split_CurrentTab_AlreadyOpened_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  different_buffer = VimBuffer( 'different_uni¢𐍈d€' )
  current_window = MagicMock( buffer = current_buffer )
  different_window = MagicMock( buffer = different_buffer )
  current_tab = MagicMock( windows = [ current_window, different_window ] )
  with MockVimBuffers( [ current_buffer, different_buffer ],
                       [ current_buffer ] ) as vim:
    vim.current.tabpage = current_tab

    vimsupport.JumpToLocation( os.path.realpath( u'different_uni¢𐍈d€' ),
                               2,
                               5,
                               'belowright',
                               'split-or-existing-window' )

    assert_that( vim.current.tabpage, equal_to( current_tab ) )
    assert_that( vim.current.window, equal_to( different_window ) )
    assert_that( vim.current.window.cursor, equal_to( ( 2, 4 ) ) )
    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( 'normal! zz' )
    ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_Split_AllTabs_NotAlreadyOpened_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    target_name = os.path.realpath( u'different_uni¢𐍈d€' )

    vimsupport.JumpToLocation( target_name,
                               2,
                               5,
                               'tab',
                               'split-or-existing-window' )

    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( u'keepjumps tab split {0}'.format( target_name ) ),
      call( 'normal! zz' )
    ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_Split_AllTabs_AlreadyOpened_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  different_buffer = VimBuffer( 'different_uni¢𐍈d€' )
  current_window = MagicMock( buffer = current_buffer )
  different_window = MagicMock( buffer = different_buffer )
  current_tab = MagicMock( windows = [ current_window, different_window ] )
  with patch( 'vim.tabpages', [ current_tab ] ):
    with MockVimBuffers( [ current_buffer, different_buffer ],
                         [ current_buffer ] ) as vim:
      vimsupport.JumpToLocation( os.path.realpath( u'different_uni¢𐍈d€' ),
                                 2,
                                 5,
                                 'tab',
                                 'split-or-existing-window' )

      assert_that( vim.current.tabpage, equal_to( current_tab ) )
      assert_that( vim.current.window, equal_to( different_window ) )
      assert_that( vim.current.window.cursor, equal_to( ( 2, 4 ) ) )
      vim_command.assert_has_exact_calls( [
        call( 'normal! m\'' ),
        call( 'normal! zz' )
      ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_NewOrExistingTab_NotAlreadyOpened_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    target_name = os.path.realpath( u'different_uni¢𐍈d€' )

    vimsupport.JumpToLocation( target_name,
                               2,
                               5,
                               'aboveleft vertical',
                               'new-or-existing-tab' )

    vim_command.assert_has_exact_calls( [
      call( 'normal! m\'' ),
      call( u'keepjumps aboveleft vertical tabedit {0}'.format( target_name ) ),
      call( 'normal! zz' )
    ] )


@patch( 'vim.command', new_callable = ExtendedMock )
def JumpToLocation_DifferentFile_NewOrExistingTab_AlreadyOpened_test(
    vim_command ):

  current_buffer = VimBuffer( 'uni¢𐍈d€' )
  different_buffer = VimBuffer( 'different_uni¢𐍈d€' )
  current_window = MagicMock( buffer = current_buffer )
  different_window = MagicMock( buffer = different_buffer )
  current_tab = MagicMock( windows = [ current_window, different_window ] )
  with patch( 'vim.tabpages', [ current_tab ] ):
    with MockVimBuffers( [ current_buffer, different_buffer ],
                         [ current_buffer ] ) as vim:
      vimsupport.JumpToLocation( os.path.realpath( u'different_uni¢𐍈d€' ),
                                 2,
                                 5,
                                 'belowright tab',
                                 'new-or-existing-tab' )

      assert_that( vim.current.tabpage, equal_to( current_tab ) )
      assert_that( vim.current.window, equal_to( different_window ) )
      assert_that( vim.current.window.cursor, equal_to( ( 2, 4 ) ) )
      vim_command.assert_has_exact_calls( [
        call( 'normal! m\'' ),
        call( 'normal! zz' )
      ] )


@patch( 'ycm.tests.test_utils.VIM_VERSION', Version( 7, 4, 1578 ) )
def VimVersionAtLeast_test():
  assert_that( vimsupport.VimVersionAtLeast( '7.3.414' ) )
  assert_that( vimsupport.VimVersionAtLeast( '7.4.1578' ) )
  assert_that( not vimsupport.VimVersionAtLeast( '7.4.1579' ) )
  assert_that( not vimsupport.VimVersionAtLeast( '7.4.1898' ) )
  assert_that( not vimsupport.VimVersionAtLeast( '8.1.278' ) )
