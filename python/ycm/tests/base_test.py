#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013  Google Inc.
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

from nose.tools import eq_, ok_, with_setup
from mock import MagicMock
from ycm.test_utils import MockVimModule
vim_mock = MockVimModule()
from ycm import base
from ycm import vimsupport
import sys

# column is 0-based
def SetVimCurrentColumnAndLineValue( column, line_value ):
  vimsupport.CurrentColumn = MagicMock( return_value = column )
  vimsupport.CurrentLineContents = MagicMock( return_value = line_value )


def Setup():
  sys.modules[ 'ycm.vimsupport' ] = MagicMock()
  vimsupport.CurrentFiletypes = MagicMock( return_value = [''] )
  vimsupport.CurrentColumn = MagicMock( return_value = 1 )
  vimsupport.CurrentLineContents = MagicMock( return_value = '' )


@with_setup( Setup )
def AdjustCandidateInsertionText_Basic_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar' ] ) )


@with_setup( Setup )
def AdjustCandidateInsertionText_ParenInTextAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar(zoo' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar' ] ) )


@with_setup( Setup )
def AdjustCandidateInsertionText_PlusInTextAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar+zoo' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar' ] ) )


@with_setup( Setup )
def AdjustCandidateInsertionText_WhitespaceInTextAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar zoo' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar' ] ) )


@with_setup( Setup )
def AdjustCandidateInsertionText_MoreThanWordMatchingAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar.h' )
  eq_( [ { 'abbr': 'foobar.h', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar.h' ] ) )

  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar(zoo' )
  eq_( [ { 'abbr': 'foobar(zoo', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText( [ 'foobar(zoo' ] ) )


@with_setup( Setup )
def AdjustCandidateInsertionText_NotSuffix_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': 'foofoo', 'word': 'foofoo' } ],
       base.AdjustCandidateInsertionText( [ 'foofoo' ] ) )


@with_setup( Setup )
def AdjustCandidateInsertionText_NothingAfterCursor_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = '' )
  eq_( [ 'foofoo',
         'zobar' ],
       base.AdjustCandidateInsertionText( [ 'foofoo',
                                            'zobar' ] ) )


@with_setup( Setup )
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


@with_setup( Setup )
def AdjustCandidateInsertionText_DictInput_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': 'foobar', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText(
         [ { 'word': 'foobar' } ] ) )


@with_setup( Setup )
def AdjustCandidateInsertionText_DontTouchAbbr_test():
  vimsupport.TextAfterCursor = MagicMock( return_value = 'bar' )
  eq_( [ { 'abbr': '1234', 'word': 'foo' } ],
       base.AdjustCandidateInsertionText(
         [ { 'abbr': '1234', 'word': 'foobar' } ] ) )


@with_setup( Setup )
def OverlapLength_Basic_test():
  eq_( 3, base.OverlapLength( 'foo bar', 'bar zoo' ) )
  eq_( 3, base.OverlapLength( 'foobar', 'barzoo' ) )


@with_setup( Setup )
def OverlapLength_BasicWithUnicode_test():
  eq_( 3, base.OverlapLength( u'bar fäö', u'fäö bar' ) )
  eq_( 3, base.OverlapLength( u'zoofäö', u'fäözoo' ) )


@with_setup( Setup )
def OverlapLength_OneCharOverlap_test():
  eq_( 1, base.OverlapLength( 'foo b', 'b zoo' ) )


@with_setup( Setup )
def OverlapLength_SameStrings_test():
  eq_( 6, base.OverlapLength( 'foobar', 'foobar' ) )


@with_setup( Setup )
def OverlapLength_Substring_test():
  eq_( 6, base.OverlapLength( 'foobar', 'foobarzoo' ) )
  eq_( 6, base.OverlapLength( 'zoofoobar', 'foobar' ) )


@with_setup( Setup )
def OverlapLength_LongestOverlap_test():
  eq_( 7, base.OverlapLength( 'bar foo foo', 'foo foo bar' ) )


@with_setup( Setup )
def OverlapLength_EmptyInput_test():
  eq_( 0, base.OverlapLength( '', 'goobar' ) )
  eq_( 0, base.OverlapLength( 'foobar', '' ) )
  eq_( 0, base.OverlapLength( '', '' ) )


@with_setup( Setup )
def OverlapLength_NoOverlap_test():
  eq_( 0, base.OverlapLength( 'foobar', 'goobar' ) )
  eq_( 0, base.OverlapLength( 'foobar', '(^($@#$#@' ) )
  eq_( 0, base.OverlapLength( 'foo bar zoo', 'foo zoo bar' ) )


@with_setup( Setup )
def LastEnteredCharIsIdentifierChar_Basic_test():
  SetVimCurrentColumnAndLineValue( 3, 'abc' )
  ok_( base.LastEnteredCharIsIdentifierChar() )

  SetVimCurrentColumnAndLineValue( 2, 'abc' )
  ok_( base.LastEnteredCharIsIdentifierChar() )

  SetVimCurrentColumnAndLineValue( 1, 'abc' )
  ok_( base.LastEnteredCharIsIdentifierChar() )


@with_setup( Setup )
def LastEnteredCharIsIdentifierChar_FiletypeHtml_test():
  SetVimCurrentColumnAndLineValue( 3, 'ab-' )
  vimsupport.CurrentFiletypes = MagicMock( return_value = ['html'] )
  ok_( base.LastEnteredCharIsIdentifierChar() )


@with_setup( Setup )
def LastEnteredCharIsIdentifierChar_ColumnIsZero_test():
  SetVimCurrentColumnAndLineValue( 0, 'abc' )
  ok_( not base.LastEnteredCharIsIdentifierChar() )


@with_setup( Setup )
def LastEnteredCharIsIdentifierChar_LineEmpty_test():
  SetVimCurrentColumnAndLineValue( 3, '' )
  ok_( not base.LastEnteredCharIsIdentifierChar() )

  SetVimCurrentColumnAndLineValue( 0, '' )
  ok_( not base.LastEnteredCharIsIdentifierChar() )


@with_setup( Setup )
def LastEnteredCharIsIdentifierChar_NotIdentChar_test():
  SetVimCurrentColumnAndLineValue( 3, 'ab;' )
  ok_( not base.LastEnteredCharIsIdentifierChar() )

  SetVimCurrentColumnAndLineValue( 1, ';' )
  ok_( not base.LastEnteredCharIsIdentifierChar() )

  SetVimCurrentColumnAndLineValue( 3, 'ab-' )
  ok_( not base.LastEnteredCharIsIdentifierChar() )


@with_setup( Setup )
def CurrentIdentifierFinished_Basic_test():
  SetVimCurrentColumnAndLineValue( 3, 'ab;' )
  ok_( base.CurrentIdentifierFinished() )

  SetVimCurrentColumnAndLineValue( 2, 'ab;' )
  ok_( not base.CurrentIdentifierFinished() )

  SetVimCurrentColumnAndLineValue( 1, 'ab;' )
  ok_( not base.CurrentIdentifierFinished() )


@with_setup( Setup )
def CurrentIdentifierFinished_NothingBeforeColumn_test():
  SetVimCurrentColumnAndLineValue( 0, 'ab;' )
  ok_( base.CurrentIdentifierFinished() )

  SetVimCurrentColumnAndLineValue( 0, '' )
  ok_( base.CurrentIdentifierFinished() )


@with_setup( Setup )
def CurrentIdentifierFinished_InvalidColumn_test():
  SetVimCurrentColumnAndLineValue( 5, '' )
  ok_( not base.CurrentIdentifierFinished() )

  SetVimCurrentColumnAndLineValue( 5, 'abc' )
  ok_( not base.CurrentIdentifierFinished() )


@with_setup( Setup )
def CurrentIdentifierFinished_InMiddleOfLine_test():
  SetVimCurrentColumnAndLineValue( 4, 'bar.zoo' )
  ok_( base.CurrentIdentifierFinished() )

  SetVimCurrentColumnAndLineValue( 4, 'bar(zoo' )
  ok_( base.CurrentIdentifierFinished() )

  SetVimCurrentColumnAndLineValue( 4, 'bar-zoo' )
  ok_( base.CurrentIdentifierFinished() )


@with_setup( Setup )
def CurrentIdentifierFinished_Html_test():
  SetVimCurrentColumnAndLineValue( 4, 'bar-zoo' )
  vimsupport.CurrentFiletypes = MagicMock( return_value = ['html'] )
  ok_( not base.CurrentIdentifierFinished() )


@with_setup( Setup )
def CurrentIdentifierFinished_WhitespaceOnly_test():
  SetVimCurrentColumnAndLineValue( 1, '\n' )
  ok_( base.CurrentIdentifierFinished() )

  SetVimCurrentColumnAndLineValue( 3, '\n    ' )
  ok_( base.CurrentIdentifierFinished() )

  SetVimCurrentColumnAndLineValue( 3, '\t\t\t\t' )
  ok_( base.CurrentIdentifierFinished() )

