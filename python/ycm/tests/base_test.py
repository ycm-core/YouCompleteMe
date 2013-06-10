#!/usr/bin/env python
#
# Copyright (C) 2013  Strahinja Val Markovic  <val@markovic.io>
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

from nose.tools import eq_
from mock import MagicMock
from ycm.test_utils import MockVimModule
vim_mock = MockVimModule()
from ycm import base
from ycm import vimsupport


def AdjustCandidateInsertionText_Basic_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar' ] ) )


def AdjustCandidateInsertionText_ParenInTextAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar(zoo' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar' ] ) )


def AdjustCandidateInsertionText_PlusInTextAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar+zoo' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar' ] ) )


def AdjustCandidateInsertionText_WhitespaceInTextAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar zoo' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar' ] ) )


def AdjustCandidateInsertionText_NotSuffix_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': 'foofoo', 'word': 'foofoo' } ],
       base.AdjustCandidateInsertionText( [ 'foofoo' ] ) )


def AdjustCandidateInsertionText_NothingAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = '' )
  eq_( [ 'foofoo',
         'zobar' ],
       base.AdjustCandidateInsertionText( [ 'foofoo',
                                            'zobar' ] ) )


def AdjustCandidateInsertionText_MultipleStrings_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' },
         { 'abbr': 'zobar', 'word': 'zo' },
         { 'abbr': 'qbar', 'word': 'q' },
         { 'abbr': 'bar', 'word': '' },
       ],
       base.AdjustCandidateInsertionText( [ 'foobar',
                                            'zobar',
                                            'qbar',
                                            'bar' ] ) )


def AdjustCandidateInsertionText_DictInput_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText(
         [ { 'word': 'foobar' } ] ) )


def AdjustCandidateInsertionText_DontTouchAbbr_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': '1234', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText(
         [ { 'abbr': '1234', 'word': 'foobar' } ] ) )
