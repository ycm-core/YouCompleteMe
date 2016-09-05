# coding: utf-8
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

# Intentionally not importing unicode_literals!
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from ycm.test_utils import ExtendedMock, MockVimModule, MockVimCommand
MockVimModule()

from ycm import vimsupport
from nose.tools import eq_
from hamcrest import assert_that, calling, raises, none, has_entry
from mock import MagicMock, call, patch
from ycmd.utils import ToBytes, ToUnicode
import os
import json


def AssertBuffersAreEqualAsBytes( result_buffer, expected_buffer ):
  eq_( len( result_buffer ), len( expected_buffer ) )
  for result_line, expected_line in zip( result_buffer, expected_buffer ):
    eq_( ToBytes( result_line ), ToBytes( expected_line ) )


def ReplaceChunk_SingleLine_Repl_1_test():
  # Replace with longer range
  result_buffer = [ 'This is a string' ]
  start, end = _BuildLocations( 1, 1, 1, 5 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'How long',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'How long is a string' ], result_buffer )
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

  AssertBuffersAreEqualAsBytes( [ 'How long is a piece of string' ],
                                 result_buffer )
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

  AssertBuffersAreEqualAsBytes( [ 'How long is a piece of pie' ],
                                 result_buffer )
  eq_( new_line_offset, 0 )
  eq_( new_char_offset, -3 )
  eq_( line_offset, 0 )
  eq_( char_offset, 10 )


def ReplaceChunk_SingleLine_Repl_2_test():
  # Replace with shorter range
  result_buffer = [ 'This is a string' ]
  start, end = _BuildLocations( 1, 11, 1, 17 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'test',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a test' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -2 )


def ReplaceChunk_SingleLine_Repl_3_test():
  # Replace with equal range
  result_buffer = [ 'This is a string' ]
  start, end = _BuildLocations( 1, 6, 1, 8 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'be',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This be a string' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 0 )


def ReplaceChunk_SingleLine_Add_1_test():
  # Insert at start
  result_buffer = [ 'is a string' ]
  start, end = _BuildLocations( 1, 1, 1, 1 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'This ',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a string' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 5 )


def ReplaceChunk_SingleLine_Add_2_test():
  # Insert at end
  result_buffer = [ 'This is a ' ]
  start, end = _BuildLocations( 1, 11, 1, 11 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'string',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a string' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 6 )


def ReplaceChunk_SingleLine_Add_3_test():
  # Insert in the middle
  result_buffer = [ 'This is a string' ]
  start, end = _BuildLocations( 1, 8, 1, 8 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          ' not',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is not a string' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 4 )


def ReplaceChunk_SingleLine_Del_1_test():
  # Delete from start
  result_buffer = [ 'This is a string' ]
  start, end = _BuildLocations( 1, 1, 1, 6 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          '',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'is a string' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -5 )


def ReplaceChunk_SingleLine_Del_2_test():
  # Delete from end
  result_buffer = [ 'This is a string' ]
  start, end = _BuildLocations( 1, 10, 1, 18 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          '',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -8 )


def ReplaceChunk_SingleLine_Del_3_test():
  # Delete from middle
  result_buffer = [ 'This is not a string' ]
  start, end = _BuildLocations( 1, 9, 1, 13 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          '',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This is a string' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -4 )


def ReplaceChunk_SingleLine_Unicode_ReplaceUnicodeChars_test():
  # Replace Unicode characters.
  result_buffer = [ 'This Uniçø∂‰ string is in the middle' ]
  start, end = _BuildLocations( 1, 6, 1, 20 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Unicode ',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This Unicode string is in the middle' ],
                                 result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -6 )


def ReplaceChunk_SingleLine_Unicode_ReplaceAfterUnicode_test():
  # Replace ASCII characters after Unicode characters in the line.
  result_buffer = [ 'This Uniçø∂‰ string is in the middle' ]
  start, end = _BuildLocations( 1, 30, 1, 43 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'fåke',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'This Uniçø∂‰ string is fåke' ],
                                 result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -8 )


def ReplaceChunk_SingleLine_Unicode_Grown_test():
  # Replace ASCII characters after Unicode characters in the line.
  result_buffer = [ 'a' ]
  start, end = _BuildLocations( 1, 1, 1, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'å',
                                                          0,
                                                          0,
                                                          result_buffer )

  AssertBuffersAreEqualAsBytes( [ 'å' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 1 ) # Note: byte difference (a = 1 byte, å = 2 bytes)


def ReplaceChunk_RemoveSingleLine_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 2, 1, 3, 1 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, '',
                                                          0, 0, result_buffer )
  # First line is not affected.
  expected_buffer = [ 'aAa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, -1 )
  eq_( char_offset, 0 )


def ReplaceChunk_SingleToMultipleLines_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 2, 2, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Eb\nbF',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'aAa',
                      'aEb',
                      'bFBa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
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

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                   'aEb',
                                   'bFBcccc',
                                   'aCa' ], result_buffer )
  eq_( line_offset, 1 )
  eq_( char_offset, 4 )


def ReplaceChunk_SingleToMultipleLines2_test():
  result_buffer = [ 'aAa', 'aBa', 'aCa' ]
  start, end = _BuildLocations( 2, 2, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nG',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ 'aAa',
                      'aEb',
                      'bFb',
                      'GBa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 2 )
  eq_( char_offset, 0 )


def ReplaceChunk_SingleToMultipleLines3_test():
  result_buffer = [ 'aAa', 'aBa', 'aCa' ]
  start, end = _BuildLocations( 2, 2, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nbGb',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ 'aAa',
                      'aEb',
                      'bFb',
                      'bGbBa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 2 )
  eq_( char_offset, 2 )


def ReplaceChunk_SingleToMultipleLinesReplace_test():
  result_buffer = [ 'aAa', 'aBa', 'aCa' ]
  start, end = _BuildLocations( 1, 2, 1, 4 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nbGb',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ 'aEb',
                      'bFb',
                      'bGb',
                      'aBa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 2 )
  eq_( char_offset, 0 )


def ReplaceChunk_SingleToMultipleLinesReplace_2_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 1, 2, 1, 4 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nbGb',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ 'aEb',
                      'bFb',
                      'bGb',
                      'aBa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
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

  AssertBuffersAreEqualAsBytes( [ 'aEb',
                                   'bFb',
                                   'bGbcccc',
                                   'aBa',
                                   'aCa' ], result_buffer )

  eq_( line_offset, 2 )
  eq_( char_offset, 4 )


def ReplaceChunk_MultipleLinesToSingleLine_test():
  result_buffer = [ 'aAa', 'aBa', 'aCaaaa' ]
  start, end = _BuildLocations( 2, 2, 3, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'E',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'aAa', 'aECaaaa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
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

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                   'aECccccaaa' ], result_buffer )
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

  AssertBuffersAreEqualAsBytes( [ 'aAa',
                                   'aECccccdd',
                                   'ddaa' ], result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -2 )


def ReplaceChunk_MultipleLinesToSameMultipleLines_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa',
                    'aDe' ]
  start, end = _BuildLocations( 2, 2, 3, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Eb\nbF',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'aAa',
                      'aEb',
                      'bFCa',
                      'aDe' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 1 )


def ReplaceChunk_MultipleLinesToMoreMultipleLines_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa',
                    'aDe' ]
  start, end = _BuildLocations( 2, 2, 3, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'Eb\nbFb\nbG',
                                                          0,
                                                          0,
                                                          result_buffer )
  expected_buffer = [ 'aAa',
                      'aEb',
                      'bFb',
                      'bGCa',
                      'aDe' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 1 )
  eq_( char_offset, 1 )


def ReplaceChunk_MultipleLinesToLessMultipleLines_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa',
                    'aDe' ]
  start, end = _BuildLocations( 1, 2, 3, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Eb\nbF',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'aEb', 'bFCa', 'aDe' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, -1 )
  eq_( char_offset, 1 )


def ReplaceChunk_MultipleLinesToEvenLessMultipleLines_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa',
                    'aDe' ]
  start, end = _BuildLocations( 1, 2, 4, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Eb\nbF',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'aEb', 'bFDe' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, -2 )
  eq_( char_offset, 1 )


def ReplaceChunk_SpanBufferEdge_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 1, 1, 1, 3 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'bDba',
                      'aBa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 1 )


def ReplaceChunk_DeleteTextInLine_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 2, 2, 2, 3 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, '',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'aAa',
                      'aa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, -1 )


def ReplaceChunk_AddTextInLine_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 2, 2, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'aAa',
                      'abDbBa',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 3 )


def ReplaceChunk_ReplaceTextInLine_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 2, 2, 2, 3 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          0, 0, result_buffer )
  expected_buffer = [ 'aAa',
                      'abDba',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 2 )


def ReplaceChunk_SingleLineOffsetWorks_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 1, 1, 1, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          1, 1, result_buffer )
  expected_buffer = [ 'aAa',
                      'abDba',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 0 )
  eq_( char_offset, 2 )


def ReplaceChunk_SingleLineToMultipleLinesOffsetWorks_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 1, 1, 1, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'Db\nE',
                                                          1, 1, result_buffer )
  expected_buffer = [ 'aAa',
                      'aDb',
                      'Ea',
                      'aCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, 1 )
  eq_( char_offset, -1 )


def ReplaceChunk_MultipleLinesToSingleLineOffsetWorks_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 1, 1, 2, 2 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start, end, 'bDb',
                                                          1, 1, result_buffer )
  expected_buffer = [ 'aAa',
                      'abDbCa' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
  eq_( line_offset, -1 )
  eq_( char_offset, 3 )


def ReplaceChunk_MultipleLineOffsetWorks_test():
  result_buffer = [ 'aAa',
                    'aBa',
                    'aCa' ]
  start, end = _BuildLocations( 3, 1, 4, 3 )
  ( line_offset, char_offset ) = vimsupport.ReplaceChunk( start,
                                                          end,
                                                          'bDb\nbEb\nbFb',
                                                          -1,
                                                          1,
                                                          result_buffer )
  expected_buffer = [ 'aAa',
                      'abDb',
                      'bEb',
                      'bFba' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )
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


def ReplaceChunksInBuffer_SortedChunks_test():
  chunks = [
    _BuildChunk( 1, 4, 1, 4, '(' ),
    _BuildChunk( 1, 11, 1, 11, ')' )
  ]

  result_buffer = [ 'CT<10 >> 2> ct' ]
  vimsupport.ReplaceChunksInBuffer( chunks, result_buffer, None )

  expected_buffer = [ 'CT<(10 >> 2)> ct' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )


def ReplaceChunksInBuffer_UnsortedChunks_test():
  chunks = [
    _BuildChunk( 1, 11, 1, 11, ')' ),
    _BuildChunk( 1, 4, 1, 4, '(' )
  ]

  result_buffer = [ 'CT<10 >> 2> ct' ]
  vimsupport.ReplaceChunksInBuffer( chunks, result_buffer, None )

  expected_buffer = [ 'CT<(10 >> 2)> ct' ]
  AssertBuffersAreEqualAsBytes( expected_buffer, result_buffer )


class MockBuffer( object ):
  """An object that looks like a vim.buffer object, enough for ReplaceChunk to
  generate a location list"""

  def __init__( self, lines, name, number ):
    self.lines = lines
    self.name = name
    self.number = number


  def __getitem__( self, index ):
    """ Return the bytes for a given line at index |index| """
    return self.lines[ index ]


  def __len__( self ):
    return len( self.lines )


  def __setitem__( self, key, value ):
    return self.lines.__setitem__( key, value )


  def GetLines( self ):
    """ Return the contents of the buffer as a list of unicode strings"""
    return [ ToUnicode( x ) for x in self.lines ]


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

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', 'single_file' )
  ]

  result_buffer = MockBuffer( [
    'line1',
    'line2',
    'line3',
  ], 'single_file', 1 )

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
      call( 'single_file', False ),
      call( 'single_file', False ),
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
        'filename': 'single_file',
        'lnum': 1,
        'col': 1,
        'text': 'replacement',
        'type': 'F'
      } ] ) ) ),
  ] )
  vim_command.assert_has_exact_calls( [
      call( 'botright copen' ),
      call( 'silent! wincmd p' )
  ] )
  set_fitting_height.assert_called_once_with()

  # And it is ReplaceChunks that prints the message showing the number of
  # changes
  post_vim_message.assert_has_exact_calls( [
      call( 'Applied 1 changes', warning = False ),
  ] )


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

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', 'single_file' )
  ]

  result_buffer = MockBuffer( [
    'line1',
    'line2',
    'line3',
  ], 'single_file', 1 )

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
      call( 'single_file', False ),
      call( 'single_file', False ),
      call( 'single_file', False ),
  ] )

  # BufferIsVisible is called 3 times for the same reasons as above, with the
  # return of each one
  buffer_is_visible.assert_has_exact_calls( [
    call( -1 ),
    call( -1 ),
    call( 1 ),
  ] )

  # We open 'single_file' as expected.
  open_filename.assert_called_with( 'single_file', {
    'focus': True,
    'fix': True,
    'size': 10
  } )

  # And close it again, then show the quickfix window.
  vim_command.assert_has_exact_calls( [
    call( 'lclose' ),
    call( 'hide' ),
    call( 'botright copen' ),
    call( 'silent! wincmd p' )
  ] )
  set_fitting_height.assert_called_once_with()

  # And update the quickfix list
  vim_eval.assert_has_exact_calls( [
    call( '&previewheight' ),
    call( 'setqflist( {0} )'.format( json.dumps( [ {
      'bufnr': 1,
      'filename': 'single_file',
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

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', 'single_file' )
  ]

  result_buffer = MockBuffer( [
    'line1',
    'line2',
    'line3',
  ], 'single_file', 1 )

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
      call( 'single_file', False ),
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

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'replacement', 'single_file' )
  ]

  result_buffer = MockBuffer( [
    'line1',
    'line2',
    'line3',
  ], 'single_file', 1 )

  with patch( 'vim.buffers', [ None, result_buffer, None ] ):
    assert_that( calling( vimsupport.ReplaceChunks ).with_args( chunks ),
                 raises( RuntimeError,
                  'Unable to open file: single_file\nFixIt/Refactor operation '
                  'aborted prior to completion. Your files have not been '
                  'fully updated. Please use undo commands to revert the '
                  'applied changes.' ) )

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
  open_filename.assert_called_with( "single_file", {
    'focus': True,
    'fix': True,
    'size': 10
  } )
  vim_eval.assert_called_with( "&previewheight" )

  # But raised an exception before issuing the message at the end
  post_vim_message.assert_not_called()


@patch( 'ycm.vimsupport.VariableExists', return_value = False )
@patch( 'ycm.vimsupport.SetFittingHeightForCurrentWindow' )
@patch( 'ycm.vimsupport.GetBufferNumberForFilename', side_effect = [
          22, # first_file (check)
          -1, # another_file (check)
          22, # first_file (apply)
          -1, # another_file (apply)
          19, # another_file (check after open)
        ],
        new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.BufferIsVisible', side_effect = [
          True,  # first_file (check)
          False, # second_file (check)
          True,  # first_file (apply)
          False, # second_file (apply)
          True,  # side_effect (check after open)
        ],
        new_callable = ExtendedMock)
@patch( 'ycm.vimsupport.OpenFilename',
        new_callable = ExtendedMock)
@patch( 'ycm.vimsupport.PostVimMessage',
        new_callable = ExtendedMock)
@patch( 'ycm.vimsupport.Confirm', return_value = True,
        new_callable = ExtendedMock)
@patch( 'vim.eval', return_value = 10,
        new_callable = ExtendedMock)
@patch( 'vim.command',
        new_callable = ExtendedMock)
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

  chunks = [
    _BuildChunk( 1, 1, 2, 1, 'first_file_replacement ', '1_first_file' ),
    _BuildChunk( 2, 1, 2, 1, 'second_file_replacement ', '2_another_file' ),
  ]

  first_file = MockBuffer( [
    'line1',
    'line2',
    'line3',
  ], '1_first_file', 22 )
  another_file = MockBuffer( [
    'another line1',
    'ACME line2',
  ], '2_another_file', 19 )

  vim_buffers = [ None ] * 23
  vim_buffers[ 22 ] = first_file
  vim_buffers[ 19 ] = another_file

  with patch( 'vim.buffers', vim_buffers ):
    vimsupport.ReplaceChunks( chunks )

  # We checked for the right file names
  get_buffer_number_for_filename.assert_has_exact_calls( [
    call( '1_first_file', False ),
    call( '2_another_file', False ),
    call( '1_first_file', False ),
    call( '2_another_file', False ),
    call( '2_another_file', False ),
  ] )

  # We checked if it was OK to open the file
  confirm.assert_has_exact_calls( [
    call( vimsupport.FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT.format( 1 ) )
  ] )

  # Ensure that buffers are updated
  eq_( another_file.GetLines(), [
    'another line1',
    'second_file_replacement ACME line2',
  ] )
  eq_( first_file.GetLines(), [
    'first_file_replacement line2',
    'line3',
  ] )

  # We open '2_another_file' as expected.
  open_filename.assert_called_with( '2_another_file', {
    'focus': True,
    'fix': True,
    'size': 10
  } )

  # And close it again, then show the quickfix window.
  vim_command.assert_has_exact_calls( [
    call( 'lclose' ),
    call( 'hide' ),
    call( 'botright copen' ),
    call( 'silent! wincmd p' )
  ] )
  set_fitting_height.assert_called_once_with()

  # And update the quickfix list with each entry
  vim_eval.assert_has_exact_calls( [
    call( '&previewheight' ),
    call( 'setqflist( {0} )'.format( json.dumps( [ {
      'bufnr': 22,
      'filename': '1_first_file',
      'lnum': 1,
      'col': 1,
      'text': 'first_file_replacement ',
      'type': 'F'
    }, {
      'bufnr': 19,
      'filename': '2_another_file',
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


@patch( 'vim.eval', new_callable = ExtendedMock )
def AddDiagnosticSyntaxMatch_ErrorInMiddleOfLine_test( vim_eval ):
  current_buffer = MockBuffer( [
    'Highlight this error please'
  ], 'some_file', 1 )

  with patch( 'vim.current.buffer', current_buffer ):
    vimsupport.AddDiagnosticSyntaxMatch( 1, 16, 1, 21 )

  vim_eval.assert_called_once_with(
    r"matchadd('YcmErrorSection', '\%1l\%16c\_.\{-}\%1l\%21c')" )


@patch( 'vim.eval', new_callable = ExtendedMock )
def AddDiagnosticSyntaxMatch_WarningAtEndOfLine_test( vim_eval ):
  current_buffer = MockBuffer( [
    'Highlight this warning'
  ], 'some_file', 1 )

  with patch( 'vim.current.buffer', current_buffer ):
    vimsupport.AddDiagnosticSyntaxMatch( 1, 16, 1, 23, is_error = False )

  vim_eval.assert_called_once_with(
    r"matchadd('YcmWarningSection', '\%1l\%16c\_.\{-}\%1l\%23c')" )


@patch( 'vim.command', new_callable=ExtendedMock )
@patch( 'vim.current', new_callable=ExtendedMock)
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


def CheckFilename_test():
  assert_that(
    calling( vimsupport.CheckFilename ).with_args( None ),
    raises( RuntimeError, "'None' is not a valid filename" )
  )

  assert_that(
    calling( vimsupport.CheckFilename ).with_args( 'nonexistent_file' ),
    raises( RuntimeError,
            "filename 'nonexistent_file' cannot be opened. "
            "No such file or directory." )
  )

  assert_that( vimsupport.CheckFilename( __file__ ), none() )


def BufferIsVisibleForFilename_test():
  buffers = [
    {
      'number': 1,
      'filename': os.path.realpath( 'visible_filename' ),
      'window': 1
    },
    {
      'number': 2,
      'filename': os.path.realpath( 'hidden_filename' ),
    }
  ]

  with patch( 'vim.buffers', buffers ):
    eq_( vimsupport.BufferIsVisibleForFilename( 'visible_filename' ), True )
    eq_( vimsupport.BufferIsVisibleForFilename( 'hidden_filename' ), False )
    eq_( vimsupport.BufferIsVisibleForFilename( 'another_filename' ), False )


@patch( 'ycm.vimsupport.GetBufferNumberForFilename',
        side_effect = [ 2, 5, -1 ] )
@patch( 'vim.command',
        side_effect = MockVimCommand,
        new_callable = ExtendedMock )
def CloseBuffersForFilename_test( vim_command, *args ):
  vimsupport.CloseBuffersForFilename( 'some_filename' )

  vim_command.assert_has_exact_calls( [
    call( 'silent! bwipeout! 2' ),
    call( 'silent! bwipeout! 5' )
  ], any_order = True )


@patch( 'vim.command', new_callable = ExtendedMock )
@patch( 'vim.current', new_callable = ExtendedMock )
def OpenFilename_test( vim_current, vim_command ):
  # Options used to open a logfile
  options = {
    'size': vimsupport.GetIntValue( '&previewheight' ),
    'fix': True,
    'watch': True,
    'position': 'end'
  }

  vimsupport.OpenFilename( __file__, options )

  vim_command.assert_has_exact_calls( [
    call( '12split {0}'.format( __file__ ) ),
    call( "exec "
          "'au BufEnter <buffer> :silent! checktime {0}'".format( __file__ ) ),
    call( 'silent! normal G zz' ),
    call( 'silent! wincmd p' )
  ] )

  vim_current.buffer.options.__setitem__.assert_has_exact_calls( [
    call( 'autoread', True ),
  ] )

  vim_current.window.options.__setitem__.assert_has_exact_calls( [
    call( 'winfixheight', True )
  ] )


@patch( 'ycm.vimsupport.BufferModified', side_effect = [ True ] )
@patch( 'ycm.vimsupport.FiletypesForBuffer', side_effect = [ [ 'cpp' ] ] )
def GetUnsavedAndCurrentBufferData_EncodedUnicodeCharsInBuffers_test( *args ):
  mock_buffer = MagicMock()
  mock_buffer.name = os.path.realpath( 'filename' )
  mock_buffer.number = 1
  mock_buffer.__iter__.return_value = [ u'abc', ToBytes( u'fДa' ) ]

  with patch( 'vim.buffers', [ mock_buffer ] ):
    assert_that( vimsupport.GetUnsavedAndCurrentBufferData(),
                 has_entry( mock_buffer.name,
                            has_entry( u'contents', u'abc\nfДa\n' ) ) )


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
  assert_that( calling( vimsupport.SelectFromList).with_args( 'test',
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
