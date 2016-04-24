# Copyright (C) 2016 YouCompleteMe contributors
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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from mock import patch, call
from nose.tools import eq_
from hamcrest import contains_string

from ycm.test_utils import MockVimModule, ExtendedMock
MockVimModule()

from ycm.test_utils import DEFAULT_CLIENT_OPTIONS, ExpectedFailure
from ycm.omni_completer import OmniCompleter
from ycm.youcompleteme import YouCompleteMe

from ycmd import user_options_store
from ycmd.utils import ToBytes
from ycmd.request_wrap import RequestWrap


def BuildRequest( line_num, column_num, contents ):
  # Note: it would be nice to use ycmd.test_utils.BuildRequest directly here,
  # but we can't import ycmd.test_utils because that in turn imports ycm_core,
  # which would cause our "ycm_core not imported" test to fail.
  return {
    'line_num': line_num,
    'column_num': column_num,
    'filepath': '/test',
    'file_data': {
      '/test': {
        'contents': contents,
        'filetypes': [ 'java' ] # We need a filetype with a trigger, so we just
                                # use java
      }
    }
  }


def BuildRequestWrap( line_num, column_num, contents ):
  return RequestWrap( BuildRequest( line_num, column_num, contents ) )


def MakeUserOptions( custom_options = {} ):
  options = dict( user_options_store.DefaultOptions() )
  options.update( DEFAULT_CLIENT_OPTIONS )
  options.update( custom_options )
  return options


class OmniCompleter_test( object ):

  def setUp( self ):
    # We need a server instance for FilterAndSortCandidates
    self._server_state = YouCompleteMe( MakeUserOptions() )


  def tearDown( self ):
    self._server_state.OnVimLeave()


  def OmniCompleter_GetCompletions_Cache_List_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 1
    } ) )

    contents = 'test.'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 6,
                                     contents = contents )


    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = [ ToBytes( 'a' ),
                        ToBytes( 'b' ),
                        ToBytes( 'cdef' ) ]

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )
      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'')" ),
      ] )

      eq_( results, omnifunc_result )


  def OmniCompleter_GetCompletions_Cache_ListFilter_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 1
    } ) )

    contents = 'test.t'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 7,
                                     contents = contents )

    eq_( request_data[ 'query' ], 't' )

    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = [ ToBytes( 'a' ),
                        ToBytes( 'b' ),
                        ToBytes( 'cdef' ) ]

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )
      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'t')" ),
      ] )

      eq_( results, [] )


  def OmniCompleter_GetCompletions_NoCache_List_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 0
    } ) )

    contents = 'test.'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 6,
                                     contents = contents )


    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = [ ToBytes( 'a' ),
                        ToBytes( 'b' ),
                        ToBytes( 'cdef' ) ]

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )
      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'')" ),
      ] )

      eq_( results, omnifunc_result )


  def OmniCompleter_GetCompletions_NoCache_ListFilter_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 0
    } ) )

    contents = 'test.t'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 7,
                                     contents = contents )

    eq_( request_data[ 'query' ], 't' )

    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = [ ToBytes( 'a' ),
                        ToBytes( 'b' ),
                        ToBytes( 'cdef' ) ]

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )
      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'t')" ),
      ] )

      # actual result is that the results are not filtered, as we expect the
      # omniufunc or vim itself to do this filtering
      eq_( results, omnifunc_result )


  @ExpectedFailure( 'We ignore the result of the call to findstart and use our '
                    'own interpretation of where the identifier should be',
                    contains_string( "test_omnifunc(0,'t')" ) )
  def OmniCompleter_GetCompletsions_UseFindStart_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 1
    } ) )

    contents = 'test.t'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 7,
                                     contents = contents )

    eq_( request_data[ 'query' ], 't' )

    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = [ ToBytes( 'a' ),
                        ToBytes( 'b' ),
                        ToBytes( 'cdef' ) ]

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 1, omnifunc_result ] ) as vim_eval:
      results = omni_completer.ComputeCandidates( request_data )

      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),

        # Fails here: actual result is that the findstart result (1) is ignored
        # and we use the 't' query as we normally would on the server side
        call( "test_omnifunc(0,'test.t')" ),
      ] )

      eq_( results, omnifunc_result )


  def OmniCompleter_GetCompletions_Cache_Object_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 1
    } ) )

    contents = 'test.t'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 7,
                                     contents = contents )

    eq_( request_data[ 'query' ], 't' )

    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = {
      'words': [ ToBytes( 'a' ), ToBytes( 'b' ), ToBytes( 'CDtEF' ) ]
    }

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )

      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'t')" ),
      ] )

      eq_( results, [ ToBytes( 'CDtEF' ) ] )


  def OmniCompleter_GetCompletions_Cache_ObjectList_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 1
    } ) )

    contents = 'test.tt'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 8,
                                     contents = contents )

    eq_( request_data[ 'query' ], 'tt' )

    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = [
      {
        'word': ToBytes( 'a' ),
        'abbr': ToBytes( 'ABBR'),
        'menu': ToBytes( 'MENU' ),
        'info': ToBytes( 'INFO' ),
        'kind': ToBytes( 'K' )
      },
      {
        'word': ToBytes( 'test' ),
        'abbr': ToBytes( 'ABBRTEST'),
        'menu': ToBytes( 'MENUTEST' ),
        'info': ToBytes( 'INFOTEST' ),
        'kind': ToBytes( 'T' )
      }
    ]

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )

      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'tt')" ),
      ] )

      eq_( results, [ omnifunc_result[ 1 ] ] )


  def OmniCompleter_GetCompletions_NoCache_ObjectList_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 0
    } ) )

    contents = 'test.tt'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 8,
                                     contents = contents )

    eq_( request_data[ 'query' ], 'tt' )

    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = [
      {
        'word': ToBytes( 'a' ),
        'abbr': ToBytes( 'ABBR'),
        'menu': ToBytes( 'MENU' ),
        'info': ToBytes( 'INFO' ),
        'kind': ToBytes( 'K' )
      },
      {
        'word': ToBytes( 'test' ),
        'abbr': ToBytes( 'ABBRTEST'),
        'menu': ToBytes( 'MENUTEST' ),
        'info': ToBytes( 'INFOTEST' ),
        'kind': ToBytes( 'T' )
      }
    ]

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )

      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'tt')" ),
      ] )

      # We don't filter the result - we expect the omnifunc to do that
      # based on the query we supplied (Note: that means no fuzzy matching!)
      eq_( results, omnifunc_result )


  def OmniCompleter_GetCompletions_Cache_ObjectListObject_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 1
    } ) )

    contents = 'test.tt'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 8,
                                     contents = contents )

    eq_( request_data[ 'query' ], 'tt' )

    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = {
      'words': [
        {
          'word': ToBytes( 'a' ),
          'abbr': ToBytes( 'ABBR'),
          'menu': ToBytes( 'MENU' ),
          'info': ToBytes( 'INFO' ),
          'kind': ToBytes( 'K' )
        },
        {
          'word': ToBytes( 'test' ),
          'abbr': ToBytes( 'ABBRTEST'),
          'menu': ToBytes( 'MENUTEST' ),
          'info': ToBytes( 'INFOTEST' ),
          'kind': ToBytes( 'T' )
        }
      ]
    }

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )

      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'tt')" ),
      ] )

      eq_( results, [ omnifunc_result[ 'words' ][ 1 ] ] )


  def OmniCompleter_GetCompletions_NoCache_ObjectListObject_test( self ):
    omni_completer = OmniCompleter( MakeUserOptions( {
      'cache_omnifunc': 0
    } ) )

    contents = 'test.tt'
    request_data = BuildRequestWrap( line_num = 1,
                                     column_num = 8,
                                     contents = contents )

    eq_( request_data[ 'query' ], 'tt' )

    # Make sure there is an omnifunc set up.
    with patch( 'vim.eval', return_value = ToBytes( 'test_omnifunc' ) ):
      omni_completer.OnFileReadyToParse( request_data )

    omnifunc_result = {
      'words': [
        {
          'word': ToBytes( 'a' ),
          'abbr': ToBytes( 'ABBR'),
          'menu': ToBytes( 'MENU' ),
          'info': ToBytes( 'INFO' ),
          'kind': ToBytes( 'K' )
        },
        {
          'word': ToBytes( 'test' ),
          'abbr': ToBytes( 'ABBRTEST'),
          'menu': ToBytes( 'MENUTEST' ),
          'info': ToBytes( 'INFOTEST' ),
          'kind': ToBytes( 'T' )
        }
      ]
    }

    # And get the completions
    with patch( 'vim.eval',
                new_callable = ExtendedMock,
                side_effect = [ 6, omnifunc_result ] ) as vim_eval:

      results = omni_completer.ComputeCandidates( request_data )

      vim_eval.assert_has_exact_calls( [
        call( 'test_omnifunc(1,"")' ),
        call( "test_omnifunc(0,'tt')" ),
      ] )

      # No FilterAndSortCandidates for cache_omnifunc=0 (we expect the omnifunc
      # to do the filtering?)
      eq_( results,  omnifunc_result[ 'words' ] )
