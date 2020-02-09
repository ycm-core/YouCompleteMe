# encoding: utf-8
#
# Copyright (C) 2016-2019 YouCompleteMe contributors
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

from hamcrest import assert_that, contains_exactly, empty, has_entries
import pytest

from ycm.tests.test_utils import MockVimBuffers, MockVimModule, VimBuffer
MockVimModule()

from ycm import vimsupport
from ycm.tests import YouCompleteMeInstance

FILETYPE = 'ycmtest'
TRIGGERS = {
  'ycmtest': [ '.' ]
}


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_List_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 5 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': 'a',    'equal': 1 },
          { 'word': 'b',    'equal': 1 },
          { 'word': 'cdef', 'equal': 1 }
        ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_ListFilter_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.t' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': empty(),
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_List_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 5 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': 'a',    'equal': 1 },
          { 'word': 'b',    'equal': 1 },
          { 'word': 'cdef', 'equal': 1 }
        ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_ListFilter_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.t' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest()
    # Actual result is that the results are not filtered, as we expect the
    # omnifunc or vim itself to do this filtering.
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': 'a',    'equal': 1 },
          { 'word': 'b',    'equal': 1 },
          { 'word': 'cdef', 'equal': 1 }
        ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_UseFindStart_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 0
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.t' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest()
    # Actual result is that the results are not filtered, as we expect the
    # omnifunc or vim itself to do this filtering.
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': 'a',    'equal': 1 },
          { 'word': 'b',    'equal': 1 },
          { 'word': 'cdef', 'equal': 1 }
        ],
        'completion_start_column': 1
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_UseFindStart_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 0
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.t' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest()
    # There are no results because the query 'test.t' doesn't match any
    # candidate (and cache_omnifunc=1, so we FilterAndSortCandidates).
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': empty(),
        'completion_start_column': 1
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_Object_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return { 'words': [ 'a', 'b', 'CDtEF' ] }

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.t' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ { 'word': 'CDtEF', 'equal': 1 } ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_ObjectList_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [
      {
        'word': 'a',
        'abbr': 'ABBR',
        'menu': 'MENU',
        'info': 'INFO',
        'kind': 'K'
      },
      {
        'word': 'test',
        'abbr': 'ABBRTEST',
        'menu': 'MENUTEST',
        'info': 'INFOTEST',
        'kind': 'T'
      }
    ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.tt' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 7 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': contains_exactly( {
          'word' : 'test',
          'abbr' : 'ABBRTEST',
          'menu' : 'MENUTEST',
          'info' : 'INFOTEST',
          'kind' : 'T',
          'equal': 1
        } ),
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_ObjectList_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [
      {
        'word': 'a',
        'abbr': 'ABBR',
        'menu': 'MENU',
        'info': 'INFO',
        'kind': 'K'
      },
      {
        'word': 'test',
        'abbr': 'ABBRTEST',
        'menu': 'MENUTEST',
        'info': 'INFOTEST',
        'kind': 'T'
      }
    ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.tt' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 7 ) ):
    ycm.SendCompletionRequest()
    # We don't filter the result - we expect the omnifunc to do that
    # based on the query we supplied (Note: that means no fuzzy matching!).
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ {
          'word' : 'a',
          'abbr' : 'ABBR',
          'menu' : 'MENU',
          'info' : 'INFO',
          'kind' : 'K',
          'equal': 1
        }, {
          'word' : 'test',
          'abbr' : 'ABBRTEST',
          'menu' : 'MENUTEST',
          'info' : 'INFOTEST',
          'kind' : 'T',
          'equal': 1
        } ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_ObjectListObject_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return { 'words': [
      {
        'word': 'a',
        'abbr': 'ABBR',
        'menu': 'MENU',
        'info': 'INFO',
        'kind': 'K'
      },
      {
        'word': 'test',
        'abbr': 'ABBRTEST',
        'menu': 'MENUTEST',
        'info': 'INFOTEST',
        'kind': 'T'
      }
    ] }

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.tt' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 7 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ {
          'word' : 'test',
          'abbr' : 'ABBRTEST',
          'menu' : 'MENUTEST',
          'info' : 'INFOTEST',
          'kind' : 'T',
          'equal': 1
        } ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_ObjectListObject_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return { 'words': [
      {
        'word': 'a',
        'abbr': 'ABBR',
        'menu': 'MENU',
        'info': 'INFO',
        'kind': 'K'
      },
      {
        'word': 'test',
        'abbr': 'ABBRTEST',
        'menu': 'MENUTEST',
        'info': 'INFOTEST',
        'kind': 'T'
      }
    ] }

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.tt' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 7 ) ):
    ycm.SendCompletionRequest()
    # No FilterAndSortCandidates for cache_omnifunc=0 (we expect the omnifunc
    # to do the filtering?)
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ {
          'word' : 'a',
          'abbr' : 'ABBR',
          'menu' : 'MENU',
          'info' : 'INFO',
          'kind' : 'K',
          'equal': 1
        }, {
          'word' : 'test',
          'abbr' : 'ABBRTEST',
          'menu' : 'MENUTEST',
          'info' : 'INFOTEST',
          'kind' : 'T',
          'equal': 1
        } ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_List_Unicode_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 12
    return [ '†est', 'å_unicode_identifier', 'πππππππ yummy πie' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ '†åsty_π.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 12 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': 'å_unicode_identifier', 'equal': 1 },
          { 'word': 'πππππππ yummy πie',    'equal': 1 },
          { 'word': '†est',                 'equal': 1 }
        ],
        'completion_start_column': 13
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_List_Unicode_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 12
    return [ '†est', 'å_unicode_identifier', 'πππππππ yummy πie' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ '†åsty_π.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 12 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': '†est',                 'equal': 1 },
          { 'word': 'å_unicode_identifier', 'equal': 1 },
          { 'word': 'πππππππ yummy πie',    'equal': 1 }
        ],
        'completion_start_column': 13
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_List_Filter_Unicode_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 12
    return [ '†est', 'å_unicode_identifier', 'πππππππ yummy πie' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ '†åsty_π.ππ' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 17 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ { 'word': 'πππππππ yummy πie', 'equal': 1 } ],
        'completion_start_column': 13
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_List_Filter_Unicode_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 12
    return [ 'πππππππ yummy πie' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ '†åsty_π.ππ' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 17 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ { 'word': 'πππππππ yummy πie', 'equal': 1 } ],
        'completion_start_column': 13
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_ObjectList_Unicode_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 12
    return [
      {
        'word': 'ålpha∫et',
        'abbr': 'å∫∫®',
        'menu': 'µ´~¨á',
        'info': '^~fo',
        'kind': '˚'
      },
      {
        'word': 'π†´ß†π',
        'abbr': 'ÅııÂÊ‰ÍÊ',
        'menu': '˜‰ˆËÊ‰ÍÊ',
        'info': 'ÈˆÏØÊ‰ÍÊ',
        'kind': 'Ê'
      }
    ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ '†åsty_π.ππ' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 17 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ {
          'word' : 'π†´ß†π',
          'abbr' : 'ÅııÂÊ‰ÍÊ',
          'menu' : '˜‰ˆËÊ‰ÍÊ',
          'info' : 'ÈˆÏØÊ‰ÍÊ',
          'kind' : 'Ê',
          'equal': 1
        } ],
        'completion_start_column': 13
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_Cache_ObjectListObject_Unicode_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 12
    return {
      'words': [
        {
          'word': 'ålpha∫et',
          'abbr': 'å∫∫®',
          'menu': 'µ´~¨á',
          'info': '^~fo',
          'kind': '˚'
        },
        {
          'word': 'π†´ß†π',
          'abbr': 'ÅııÂÊ‰ÍÊ',
          'menu': '˜‰ˆËÊ‰ÍÊ',
          'info': 'ÈˆÏØÊ‰ÍÊ',
          'kind': 'Ê'
        },
        {
          'word': 'test',
          'abbr': 'ÅııÂÊ‰ÍÊ',
          'menu': '˜‰ˆËÊ‰ÍÊ',
          'info': 'ÈˆÏØÊ‰ÍÊ',
          'kind': 'Ê'
        }
      ]
    }

  current_buffer = VimBuffer( 'buffer',
                              contents = [ '†åsty_π.t' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 13 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': contains_exactly( {
          'word' : 'test',
          'abbr' : 'ÅııÂÊ‰ÍÊ',
          'menu' : '˜‰ˆËÊ‰ÍÊ',
          'info' : 'ÈˆÏØÊ‰ÍÊ',
          'kind' : 'Ê',
          'equal': 1
        }, {
          'word' : 'ålpha∫et',
          'abbr' : 'å∫∫®',
          'menu' : 'µ´~¨á',
          'info' : '^~fo',
          'kind' : '˚',
          'equal': 1
        } ),
        'completion_start_column': 13
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_RestoreCursorPositionAfterOmnifuncCall_test(
  ycm ):

  # This omnifunc moves the cursor to the test definition like
  # ccomplete#Complete would.
  def Omnifunc( findstart, base ):
    vimsupport.SetCurrentLineAndColumn( 0, 0 )
    if findstart:
      return 5
    return [ 'length' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'String test',
                                           '',
                                           'test.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 3, 5 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      vimsupport.CurrentLineAndColumn(),
      contains_exactly( 2, 5 )
    )
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ { 'word': 'length', 'equal': 1 } ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_MoveCursorPositionAtStartColumn_test( ycm ):
  # This omnifunc relies on the cursor being moved at the start column when
  # called the second time like LanguageClient#complete from the
  # LanguageClient-neovim plugin.
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    if vimsupport.CurrentColumn() == 5:
      return [ 'length' ]
    return []

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'String test',
                                           '',
                                           'test.le' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 3, 7 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      vimsupport.CurrentLineAndColumn(),
      contains_exactly( 2, 7 )
    )
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ { 'word': 'length', 'equal': 1 } ],
        'completion_start_column': 6
      } )
    )


def StartColumnCompliance( ycm,
                           omnifunc_start_column,
                           ycm_completions,
                           ycm_start_column ):
  def Omnifunc( findstart, base ):
    if findstart:
      return omnifunc_start_column
    return [ 'foo' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'fo' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 2 ) ):
    ycm.SendCompletionRequest( force_semantic = True )
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': ycm_completions,
        'completion_start_column': ycm_start_column
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1 } )
@pytest.mark.parametrize(
  'omnifunc_start_column,ycm_completions,ycm_start_column', [
   [ -4, [ { 'word': 'foo', 'equal': 1 } ], 3 ],
   [ -3, [],                                1 ],
   [ -2, [],                                1 ],
   [ -1, [ { 'word': 'foo', 'equal': 1 } ], 3 ],
   [ 0, [ { 'word': 'foo', 'equal': 1 } ], 1 ],
   [ 1, [ { 'word': 'foo', 'equal': 1 } ], 2 ],
   [ 2, [ { 'word': 'foo', 'equal': 1 } ], 3 ],
   [ 3, [ { 'word': 'foo', 'equal': 1 } ], 3 ]
  ] )
def OmniCompleter_GetCompletions_StartColumnCompliance_test(
    ycm,
    omnifunc_start_column,
    ycm_completions,
    ycm_start_column ):
  StartColumnCompliance( ycm,
                         omnifunc_start_column,
                         ycm_completions,
                         ycm_start_column )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_NoSemanticTrigger_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 0
    return [ 'test' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'te' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 3 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': empty(),
        'completion_start_column': 1
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 0,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_NoCache_ForceSemantic_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 0
    return [ 'test' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'te' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 3 ) ):
    ycm.SendCompletionRequest( force_semantic = True )
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [ { 'word': 'test', 'equal': 1 } ],
        'completion_start_column': 1
      } )
    )


@YouCompleteMeInstance( { 'g:ycm_cache_omnifunc': 1,
                          'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_ConvertStringsToDictionaries_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [
      { 'word': 'a' },
      'b'
    ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 7 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': 'a', 'equal': 1 },
          { 'word': 'b', 'equal': 1 }
        ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( {
  'g:ycm_cache_omnifunc': 0,
  'g:ycm_filetype_specific_completion_to_disable': { FILETYPE: 1 },
  'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_FiletypeDisabled_SemanticTrigger_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': empty(),
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( {
  'g:ycm_cache_omnifunc': 0,
  'g:ycm_filetype_specific_completion_to_disable': { '*': 1 },
  'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_AllFiletypesDisabled_SemanticTrigger_test(
  ycm ):

  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest()
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': empty(),
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( {
  'g:ycm_cache_omnifunc': 0,
  'g:ycm_filetype_specific_completion_to_disable': { FILETYPE: 1 },
  'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_FiletypeDisabled_ForceSemantic_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest( force_semantic = True )
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': 'a',    'equal': 1 },
          { 'word': 'b',    'equal': 1 },
          { 'word': 'cdef', 'equal': 1 }
        ],
        'completion_start_column': 6
      } )
    )


@YouCompleteMeInstance( {
  'g:ycm_cache_omnifunc': 0,
  'g:ycm_filetype_specific_completion_to_disable': { '*': 1 },
  'g:ycm_semantic_triggers': TRIGGERS } )
def OmniCompleter_GetCompletions_AllFiletypesDisabled_ForceSemantic_test( ycm ):
  def Omnifunc( findstart, base ):
    if findstart:
      return 5
    return [ 'a', 'b', 'cdef' ]

  current_buffer = VimBuffer( 'buffer',
                              contents = [ 'test.' ],
                              filetype = FILETYPE,
                              omnifunc = Omnifunc )

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 6 ) ):
    ycm.SendCompletionRequest( force_semantic = True )
    assert_that(
      ycm.GetCompletionResponse(),
      has_entries( {
        'completions': [
          { 'word': 'a',    'equal': 1 },
          { 'word': 'b',    'equal': 1 },
          { 'word': 'cdef', 'equal': 1 }
        ],
        'completion_start_column': 6
      } )
    )
