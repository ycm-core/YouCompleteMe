# Copyright (C) 2013 Google Inc.
#               2020 YouCompleteMe contributors
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

import contextlib
from hamcrest import assert_that, equal_to
from unittest.mock import patch

from ycm.tests.test_utils import MockVimModule
vim_mock = MockVimModule()
from ycm import base


@contextlib.contextmanager
def MockCurrentFiletypes( filetypes = [ '' ] ):
  with patch( 'ycm.vimsupport.CurrentFiletypes', return_value = filetypes ):
    yield


@contextlib.contextmanager
def MockCurrentColumnAndLineContents( column, line_contents ):
  with patch( 'ycm.vimsupport.CurrentColumn', return_value = column ):
    with patch( 'ycm.vimsupport.CurrentLineContents',
                return_value = line_contents ):
      yield


@contextlib.contextmanager
def MockTextAfterCursor( text ):
  with patch( 'ycm.vimsupport.TextAfterCursor', return_value = text ):
    yield


def AdjustCandidateInsertionText_Basic_test():
  with MockTextAfterCursor( 'bar' ):
    assert_that( [ { 'word': 'foo',    'abbr': 'foobar' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                             { 'word': 'foobar', 'abbr': '' } ] ) ) )


def AdjustCandidateInsertionText_ParenInTextAfterCursor_test():
  with MockTextAfterCursor( 'bar(zoo' ):
    assert_that( [ { 'word': 'foo',    'abbr': 'foobar' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                             { 'word': 'foobar', 'abbr': '' } ] ) ) )


def AdjustCandidateInsertionText_PlusInTextAfterCursor_test():
  with MockTextAfterCursor( 'bar+zoo' ):
    assert_that( [ { 'word': 'foo',    'abbr': 'foobar' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                             { 'word': 'foobar', 'abbr': '' } ] ) ) )


def AdjustCandidateInsertionText_WhitespaceInTextAfterCursor_test():
  with MockTextAfterCursor( 'bar zoo' ):
    assert_that( [ { 'word': 'foo',    'abbr': 'foobar' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                             { 'word': 'foobar', 'abbr': '' } ] ) ) )


def AdjustCandidateInsertionText_MoreThanWordMatchingAfterCursor_test():
  with MockTextAfterCursor( 'bar.h' ):
    assert_that( [ { 'word': 'foo', 'abbr': 'foobar.h' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                             { 'word': 'foobar.h', 'abbr': '' } ] ) ) )

  with MockTextAfterCursor( 'bar(zoo' ):
    assert_that( [ { 'word': 'foo', 'abbr': 'foobar(zoo' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                             { 'word': 'foobar(zoo', 'abbr': '' } ] ) ) )


def AdjustCandidateInsertionText_NotSuffix_test():
  with MockTextAfterCursor( 'bar' ):
    assert_that( [ { 'word': 'foofoo', 'abbr': 'foofoo' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                   { 'word': 'foofoo', 'abbr': '' } ] ) ) )


def AdjustCandidateInsertionText_NothingAfterCursor_test():
  with MockTextAfterCursor( '' ):
    assert_that( [ { 'word': 'foofoo', 'abbr': '' },
                   { 'word': 'zobar',  'abbr': '' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                   { 'word': 'foofoo', 'abbr': '' },
                   { 'word': 'zobar',  'abbr': '' } ] ) ) )


def AdjustCandidateInsertionText_MultipleStrings_test():
  with MockTextAfterCursor( 'bar' ):
    assert_that( [ { 'word': 'foo',    'abbr': 'foobar' },
                   { 'word': 'zo',     'abbr': 'zobar' },
                   { 'word': 'q',      'abbr': 'qbar' },
                   { 'word': '',       'abbr': 'bar' }, ],
                 equal_to( base.AdjustCandidateInsertionText( [
                   { 'word': 'foobar', 'abbr': '' },
                   { 'word': 'zobar',  'abbr': '' },
                   { 'word': 'qbar',   'abbr': '' },
                   { 'word': 'bar',    'abbr': '' } ] ) ) )


def AdjustCandidateInsertionText_DontTouchAbbr_test():
  with MockTextAfterCursor( 'bar' ):
    assert_that( [ { 'word': 'foo',    'abbr': '1234' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                   { 'word': 'foobar', 'abbr': '1234' } ] ) ) )


def AdjustCandidateInsertionText_NoAbbr_test():
  with MockTextAfterCursor( 'bar' ):
    assert_that( [ { 'word': 'foo', 'abbr': 'foobar' } ],
                 equal_to( base.AdjustCandidateInsertionText( [
                   { 'word': 'foobar' } ] ) ) )


def OverlapLength_Basic_test():
  assert_that( 3, equal_to( base.OverlapLength( 'foo bar', 'bar zoo' ) ) )
  assert_that( 3, equal_to( base.OverlapLength( 'foobar', 'barzoo' ) ) )


def OverlapLength_BasicWithUnicode_test():
  assert_that( 3, equal_to( base.OverlapLength( u'bar fäö', u'fäö bar' ) ) )
  assert_that( 3, equal_to( base.OverlapLength( u'zoofäö', u'fäözoo' ) ) )


def OverlapLength_OneCharOverlap_test():
  assert_that( 1, equal_to( base.OverlapLength( 'foo b', 'b zoo' ) ) )


def OverlapLength_SameStrings_test():
  assert_that( 6, equal_to( base.OverlapLength( 'foobar', 'foobar' ) ) )


def OverlapLength_Substring_test():
  assert_that( 6, equal_to( base.OverlapLength( 'foobar', 'foobarzoo' ) ) )
  assert_that( 6, equal_to( base.OverlapLength( 'zoofoobar', 'foobar' ) ) )


def OverlapLength_LongestOverlap_test():
  assert_that( 7, equal_to( base.OverlapLength( 'bar foo foo',
                                                'foo foo bar' ) ) )


def OverlapLength_EmptyInput_test():
  assert_that( 0, equal_to( base.OverlapLength( '', 'goobar' ) ) )
  assert_that( 0, equal_to( base.OverlapLength( 'foobar', '' ) ) )
  assert_that( 0, equal_to( base.OverlapLength( '', '' ) ) )


def OverlapLength_NoOverlap_test():
  assert_that( 0, equal_to( base.OverlapLength( 'foobar', 'goobar' ) ) )
  assert_that( 0, equal_to( base.OverlapLength( 'foobar', '(^($@#$#@' ) ) )
  assert_that( 0, equal_to( base.OverlapLength( 'foo bar zoo',
                                                'foo zoo bar' ) ) )


def LastEnteredCharIsIdentifierChar_Basic_test():
  with MockCurrentFiletypes():
    with MockCurrentColumnAndLineContents( 3, 'abc' ):
      assert_that( base.LastEnteredCharIsIdentifierChar() )

    with MockCurrentColumnAndLineContents( 2, 'abc' ):
      assert_that( base.LastEnteredCharIsIdentifierChar() )

    with MockCurrentColumnAndLineContents( 1, 'abc' ):
      assert_that( base.LastEnteredCharIsIdentifierChar() )


def LastEnteredCharIsIdentifierChar_FiletypeHtml_test():
  with MockCurrentFiletypes( [ 'html' ] ):
    with MockCurrentColumnAndLineContents( 3, 'ab-' ):
      assert_that( base.LastEnteredCharIsIdentifierChar() )


def LastEnteredCharIsIdentifierChar_ColumnIsZero_test():
  with MockCurrentColumnAndLineContents( 0, 'abc' ):
    assert_that( not base.LastEnteredCharIsIdentifierChar() )


def LastEnteredCharIsIdentifierChar_LineEmpty_test():
  with MockCurrentFiletypes():
    with MockCurrentColumnAndLineContents( 3, '' ):
      assert_that( not base.LastEnteredCharIsIdentifierChar() )

    with MockCurrentColumnAndLineContents( 0, '' ):
      assert_that( not base.LastEnteredCharIsIdentifierChar() )


def LastEnteredCharIsIdentifierChar_NotIdentChar_test():
  with MockCurrentFiletypes():
    with MockCurrentColumnAndLineContents( 3, 'ab;' ):
      assert_that( not base.LastEnteredCharIsIdentifierChar() )

    with MockCurrentColumnAndLineContents( 1, ';' ):
      assert_that( not base.LastEnteredCharIsIdentifierChar() )

    with MockCurrentColumnAndLineContents( 3, 'ab-' ):
      assert_that( not base.LastEnteredCharIsIdentifierChar() )


def LastEnteredCharIsIdentifierChar_Unicode_test():
  with MockCurrentFiletypes():
    # CurrentColumn returns a byte offset and character ø is 2 bytes length.
    with MockCurrentColumnAndLineContents( 5, 'føo(' ):
      assert_that( not base.LastEnteredCharIsIdentifierChar() )

    with MockCurrentColumnAndLineContents( 4, 'føo(' ):
      assert_that( base.LastEnteredCharIsIdentifierChar() )

    with MockCurrentColumnAndLineContents( 3, 'føo(' ):
      assert_that( base.LastEnteredCharIsIdentifierChar() )

    with MockCurrentColumnAndLineContents( 1, 'føo(' ):
      assert_that( base.LastEnteredCharIsIdentifierChar() )


def CurrentIdentifierFinished_Basic_test():
  with MockCurrentFiletypes():
    with MockCurrentColumnAndLineContents( 3, 'ab;' ):
      assert_that( base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 2, 'ab;' ):
      assert_that( not base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 1, 'ab;' ):
      assert_that( not base.CurrentIdentifierFinished() )


def CurrentIdentifierFinished_NothingBeforeColumn_test():
  with MockCurrentColumnAndLineContents( 0, 'ab;' ):
    assert_that( base.CurrentIdentifierFinished() )

  with MockCurrentColumnAndLineContents( 0, '' ):
    assert_that( base.CurrentIdentifierFinished() )


def CurrentIdentifierFinished_InvalidColumn_test():
  with MockCurrentFiletypes():
    with MockCurrentColumnAndLineContents( 5, '' ):
      assert_that( base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 5, 'abc' ):
      assert_that( not base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 4, 'ab;' ):
      assert_that( base.CurrentIdentifierFinished() )


def CurrentIdentifierFinished_InMiddleOfLine_test():
  with MockCurrentFiletypes():
    with MockCurrentColumnAndLineContents( 4, 'bar.zoo' ):
      assert_that( base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 4, 'bar(zoo' ):
      assert_that( base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 4, 'bar-zoo' ):
      assert_that( base.CurrentIdentifierFinished() )


def CurrentIdentifierFinished_Html_test():
  with MockCurrentFiletypes( [ 'html' ] ):
    with MockCurrentColumnAndLineContents( 4, 'bar-zoo' ):
      assert_that( not base.CurrentIdentifierFinished() )


def CurrentIdentifierFinished_WhitespaceOnly_test():
  with MockCurrentFiletypes():
    with MockCurrentColumnAndLineContents( 1, '\n' ):
      assert_that( base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 3, '\n    ' ):
      assert_that( base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 3, '\t\t\t\t' ):
      assert_that( base.CurrentIdentifierFinished() )


def CurrentIdentifierFinished_Unicode_test():
  with MockCurrentFiletypes():
    # CurrentColumn returns a byte offset and character ø is 2 bytes length.
    with MockCurrentColumnAndLineContents( 6, 'føo ' ):
      assert_that( base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 5, 'føo ' ):
      assert_that( base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 4, 'føo ' ):
      assert_that( not base.CurrentIdentifierFinished() )

    with MockCurrentColumnAndLineContents( 3, 'føo ' ):
      assert_that( not base.CurrentIdentifierFinished() )
