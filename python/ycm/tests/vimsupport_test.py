#!/usr/bin/env python
#
# Copyright (C) 2015 YouCompleteMe contributors
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

from ycm.test_utils import MockVimModule
MockVimModule()

from ycm import vimsupport
from nose.tools import eq_
from mock import MagicMock, call, patch


def ReplaceChunk_SingleLine_Repl_1_test():
  # Replace with longer range
  #                  12345678901234567
  result_buffer = [ "This is a string" ]
  start, end = _BuildLocations( 1, 1, 1, 5 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'How long',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "How long is a string" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 4 )

  # and replace again, using delta
  start, end = _BuildLocations( 1, 10, 1, 11 )
  ( new_line_offset, new_char_offset ) = vimsupport.ReplaceChunk(
                                                          start,
                                                          end,
                                                          ' piece of ',
                                                          line_offset,
                                                          char_offset,
                                                          result_buffer )

  line_offset += new_line_offset
  char_offset += new_char_offset

  eq_( [ 'How long is a piece of string' ], result_buffer )
  eq_( new_line_offset, 0 )
  eq_( new_char_offset, 9 )
  eq_( line_offset, 0 )
  eq_( char_offset, 13 )

  # and once more, for luck
  start, end = _BuildLocations( 1, 11, 1, 17 )

  ( new_line_offset, new_char_offset ) = vimsupport.ReplaceChunk(
                                                          start,
                                                          end,
                                                          'pie',
                                                          line_offset,
                                                          char_offset,
                                                          result_buffer )

  line_offset += new_line_offset
  char_offset += new_char_offset

  eq_( ['How long is a piece of pie' ], result_buffer )
  eq_( new_line_offset, 0 )
  eq_( new_char_offset, -3 )
  eq_( line_offset, 0 )
  eq_( char_offset, 10 )


def ReplaceChunk_SingleLine_Repl_2_test():
  # Replace with shorter range
  #                  12345678901234567
  result_buffer = [ "This is a string" ]
  start, end = _BuildLocations( 1, 11, 1, 17 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'test',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "This is a test" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -2 )


def ReplaceChunk_SingleLine_Repl_3_test():
  # Replace with equal range
  #                  12345678901234567
  result_buffer = [ "This is a string" ]
  start, end = _BuildLocations( 1, 6, 1, 8 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'be',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "This be a string" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 0 )


def ReplaceChunk_SingleLine_Add_1_test():
  # Insert at start
  result_buffer = [ "is a string" ]
  start, end = _BuildLocations( 1, 1, 1, 1 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'This ',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "This is a string" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 5 )


def ReplaceChunk_SingleLine_Add_2_test():
  # Insert at end
  result_buffer = [ "This is a " ]
  start, end = _BuildLocations( 1, 11, 1, 11 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'string',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "This is a string" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 6 )


def ReplaceChunk_SingleLine_Add_3_test():
  # Insert in the middle
  result_buffer = [ "This is a string" ]
  start, end = _BuildLocations( 1, 8, 1, 8 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          ' not',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "This is not a string" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 4 )


def ReplaceChunk_SingleLine_Del_1_test():
  # Delete from start
  result_buffer = [ "This is a string" ]
  start, end = _BuildLocations( 1, 1, 1, 6 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          '',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "is a string" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -5 )


def ReplaceChunk_SingleLine_Del_2_test():
  # Delete from end
  result_buffer = [ "This is a string" ]
  start, end = _BuildLocations( 1, 10, 1, 18 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          '',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "This is a" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -8 )


def ReplaceChunk_SingleLine_Del_3_test():
  # Delete from middle
  result_buffer = [ "This is not a string" ]
  start, end = _BuildLocations( 1, 9, 1, 13 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          '',
                                                          0,
                                                          0,
                                                          result_buffer )

  eq_( [ "This is a string" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -4 )


def ReplaceChunk_RemoveSingleLine_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 2, 1, 3, 1 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, '',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aAa", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, -1 )
  eq_( char_offset, 0 )


def ReplaceChunk_SingleToMultipleLines_test():
  result_buffer = [ "aAa",
                    "aBa",
                    "aCa" ]
  start, end = _BuildLocations( 2, 2, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Eb\nbF',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aAa",
                      "aEb",
                      "bFBa",
                      "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 1 )
  eq_( char_offset, 1 )

  # now make another change to the "2nd" line
  start, end = _BuildLocations( 2, 3, 2, 4 )
  ( new_line_offset, new_char_offset ) = vimsupport.ReplaceChunk( 
                                                           start, 
                                                           end, 
                                                           'cccc',
                                                           line_offset,
                                                           char_offset,
                                                           result_buffer )

  line_offset += new_line_offset
  char_offset += new_char_offset

  eq_( [ "aAa", "aEb", "bFBcccc", "aCa" ], result_buffer )
  eq_( line_offset, 1 )
  eq_( char_offset, 4 )


def ReplaceChunk_SingleToMultipleLines2_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 2, 2, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nG',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ "aAa", "aEb", "bFb", "GBa", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 2 )
  eq_( char_offset, 0 )


def ReplaceChunk_SingleToMultipleLines3_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 2, 2, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nbGb',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ "aAa", "aEb", "bFb", "bGbBa", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 2 )
  eq_( char_offset, 2 )


def ReplaceChunk_SingleToMultipleLinesReplace_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 1, 2, 1, 4 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nbGb',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ "aEb", "bFb", "bGb", "aBa", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 2 )
  eq_( char_offset, 0 )


def ReplaceChunk_SingleToMultipleLinesReplace_2_test():
  result_buffer = [ "aAa",
                    "aBa",
                    "aCa" ]
  start, end = _BuildLocations( 1, 2, 1, 4 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nbGb',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ "aEb",
                      "bFb",
                      "bGb",
                      "aBa",
                      "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 2 )
  eq_( char_offset, 0 )

  # now do a subsequent change (insert at end of line "1")
  start, end = _BuildLocations( 1, 4, 1, 4 )
  ( new_line_offset, new_char_offset ) = vimsupport.ReplaceChunk(
                                                          start,
                                                          end,
                                                          'cccc',
                                                          line_offset,
                                                          char_offset,
                                                          result_buffer )

  line_offset += new_line_offset
  char_offset += new_char_offset

  eq_( [ "aEb",
         "bFb",
         "bGbcccc",
         "aBa",
         "aCa" ], result_buffer )

  eq_( line_offset, 2 )
  eq_( char_offset, 4 )



def ReplaceChunk_MultipleLinesToSingleLine_test():
  result_buffer = [ "aAa", "aBa", "aCaaaa" ]
  start, end = _BuildLocations( 2, 2, 3, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'E',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aAa", "aECaaaa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, -1 )
  eq_( char_offset, 1 )

  # make another modification applying offsets
  start, end = _BuildLocations( 3, 3, 3, 4 )
  ( new_line_offset, new_char_offset ) = vimsupport.ReplaceChunk(
                                                          start,
                                                          end,
                                                          'cccc',
                                                          line_offset,
                                                          char_offset,
                                                          result_buffer )

  line_offset += new_line_offset
  char_offset += new_char_offset

  eq_( [ "aAa", "aECccccaaa" ], result_buffer )
  eq_( line_offset, -1 )
  eq_( char_offset, 4 )

  # and another, for luck
  start, end = _BuildLocations( 3, 4, 3, 5 )
  ( new_line_offset, new_char_offset ) = vimsupport.ReplaceChunk(
                                                          start,
                                                          end,
                                                          'dd\ndd',
                                                          line_offset,
                                                          char_offset,
                                                          result_buffer )

  line_offset += new_line_offset
  char_offset += new_char_offset

  eq_( [ "aAa", "aECccccdd", "ddaa" ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -2 )


def ReplaceChunk_MultipleLinesToSameMultipleLines_test():
  result_buffer = [ "aAa", "aBa", "aCa", "aDe" ]
  start, end = _BuildLocations( 2, 2, 3, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Eb\nbF',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aAa", "aEb", "bFCa", "aDe" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 1 )


def ReplaceChunk_MultipleLinesToMoreMultipleLines_test():
  result_buffer = [ "aAa", "aBa", "aCa", "aDe" ]
  start, end = _BuildLocations( 2, 2, 3, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nbG',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ "aAa", "aEb", "bFb", "bGCa", "aDe" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 1 )
  eq_( char_offset, 1 )


def ReplaceChunk_MultipleLinesToLessMultipleLines_test():
  result_buffer = [ "aAa", "aBa", "aCa", "aDe" ]
  start, end = _BuildLocations( 1, 2, 3, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Eb\nbF',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aEb", "bFCa", "aDe" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, -1 )
  eq_( char_offset, 1 )


def ReplaceChunk_MultipleLinesToEvenLessMultipleLines_test():
  result_buffer = [ "aAa", "aBa", "aCa", "aDe" ]
  start, end = _BuildLocations( 1, 2, 4, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Eb\nbF',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aEb", "bFDe" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, -2 )
  eq_( char_offset, 1 )


def ReplaceChunk_SpanBufferEdge_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 1, 1, 1, 3 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          0, 0, result_buffer )
  expected_buffer = [ "bDba", "aBa", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 1 )


def ReplaceChunk_DeleteTextInLine_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 2, 2, 2, 3 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, '',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aAa", "aa", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -1 )


def ReplaceChunk_AddTextInLine_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 2, 2, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aAa", "abDbBa", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 3 )


def ReplaceChunk_ReplaceTextInLine_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 2, 2, 2, 3 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          0, 0, result_buffer )
  expected_buffer = [ "aAa", "abDba", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 2 )


def ReplaceChunk_SingleLineOffsetWorks_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 1, 1, 1, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          1, 1, result_buffer )
  expected_buffer = [ "aAa", "abDba", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 2 )


def ReplaceChunk_SingleLineToMultipleLinesOffsetWorks_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 1, 1, 1, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Db\nE',
                                                          1, 1, result_buffer )
  expected_buffer = [ "aAa", "aDb", "Ea", "aCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 1 )
  eq_( char_offset, -1 )


def ReplaceChunk_MultipleLinesToSingleLineOffsetWorks_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 1, 1, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          1, 1, result_buffer )
  expected_buffer = [ "aAa", "abDbCa" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, -1 )
  eq_( char_offset, 3 )


def ReplaceChunk_MultipleLineOffsetWorks_test():
  result_buffer = [ "aAa", "aBa", "aCa" ]
  start, end = _BuildLocations( 3, 1, 4, 3 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'bDb\nbEb\nbFb',
                                                          -1,
                                                          1,
                                                          result_buffer )
  expected_buffer = [ "aAa", "abDb", "bEb", "bFba" ]
  eq_( expected_buffer, result_buffer )
  eq_( line_offset, 1 )
  eq_( char_offset, 1 )


def _BuildLocations( start_line, start_column, end_line, end_column ):
  return {
    'line_num'  : start_line,
    'column_num': start_column,
  }, {
    'line_num'  : end_line,
    'column_num': end_column,
  }


def ReplaceChunksList_SortedChunks_test():
  chunks = [
    _BuildChunk( 1, 4, 1, 4, '('),
    _BuildChunk( 1, 11, 1, 11, ')' )
  ]

  result_buffer = [ "CT<10 >> 2> ct" ]
  vimsupport.ReplaceChunksList( chunks, result_buffer )

  expected_buffer = [ "CT<(10 >> 2)> ct" ]
  eq_( expected_buffer, result_buffer )


def ReplaceChunksList_UnsortedChunks_test():
  chunks = [
    _BuildChunk( 1, 11, 1, 11, ')'),
    _BuildChunk( 1, 4, 1, 4, '(' )
  ]

  result_buffer = [ "CT<10 >> 2> ct" ]
  vimsupport.ReplaceChunksList( chunks, result_buffer )

  expected_buffer = [ "CT<(10 >> 2)> ct" ]
  eq_( expected_buffer, result_buffer )


def _BuildChunk( start_line, start_column, end_line, end_column,
                 replacement_text ):
  return {
    'range': {
      'start': {
        'line_num': start_line,
        'column_num': start_column,
      },
      'end': {
        'line_num': end_line,
        'column_num': end_column,
      },
    },
    'replacement_text': replacement_text
  }


def _Mock_tempname( arg ):
  if arg == 'tempname()':
    return '_TEMP_FILE_'

  raise ValueError( 'Unexpected evaluation: ' + arg )


@patch( 'vim.eval', side_effect=_Mock_tempname )
@patch( 'vim.command' )
@patch( 'vim.current' )
def WriteToPreviewWindow_test( vim_current, vim_command, vim_eval ):
  vim_current.window.options.__getitem__ = MagicMock( return_value = True )

  vimsupport.WriteToPreviewWindow( "test" )

  vim_command.assert_has_calls( [
    call( 'silent! pclose!' ),
    call( 'silent! pedit! _TEMP_FILE_' ),
    call( 'silent! wincmd P' ),
    call( 'silent! wincmd p' ) ] )

  vim_current.buffer.__setitem__.assert_called_with(
      slice( None, None, None ), [ 'test' ] )

  vim_current.buffer.options.__setitem__.assert_has_calls( [
    call( 'buftype', 'nofile' ),
    call( 'swapfile', False ),
    call( 'modifiable', False ),
    call( 'modified', False ),
    call( 'readonly', True ),
  ], any_order = True )


@patch( 'vim.eval', side_effect=_Mock_tempname )
@patch( 'vim.current' )
def WriteToPreviewWindow_MultiLine_test( vim_current, vim_eval ):
  vim_current.window.options.__getitem__ = MagicMock( return_value = True )
  vimsupport.WriteToPreviewWindow( "test\ntest2" )

  vim_current.buffer.__setitem__.assert_called_with(
      slice( None, None, None ), [ 'test', 'test2' ] )


@patch( 'vim.eval', side_effect=_Mock_tempname )
@patch( 'vim.command' )
@patch( 'vim.current' )
def WriteToPreviewWindow_JumpFail_test( vim_current, vim_command, vim_eval ):
  vim_current.window.options.__getitem__ = MagicMock( return_value = False )

  vimsupport.WriteToPreviewWindow( "test" )

  vim_command.assert_has_calls( [
    call( 'silent! pclose!' ),
    call( 'silent! pedit! _TEMP_FILE_' ),
    call( 'silent! wincmd P' ),
    call( "echom 'test'" ),
  ] )

  vim_current.buffer.__setitem__.assert_not_called()
  vim_current.buffer.options.__setitem__.assert_not_called()


@patch( 'vim.eval', side_effect=_Mock_tempname )
@patch( 'vim.command' )
@patch( 'vim.current' )
def WriteToPreviewWindow_JumpFail_MultiLine_test( vim_current,
                                                  vim_command,
                                                  vim_eval ):

  vim_current.window.options.__getitem__ = MagicMock( return_value = False )

  vimsupport.WriteToPreviewWindow( "test\ntest2" )

  vim_command.assert_has_calls( [
    call( 'silent! pclose!' ),
    call( 'silent! pedit! _TEMP_FILE_' ),
    call( 'silent! wincmd P' ),
    call( "echom 'test'" ),
    call( "echom 'test2'" ),
  ] )

  vim_current.buffer.__setitem__.assert_not_called()
  vim_current.buffer.options.__setitem__.assert_not_called()
