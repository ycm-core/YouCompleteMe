# Copyright (C) 2016  YouCompleteMe contributors
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

from ycm.test_utils import MockVimModule
MockVimModule()

from hamcrest import assert_that, equal_to
from ycm.diagnostic_filter import DiagnosticFilter


def _assert_accept_equals( filter, text_or_obj, expected ):
  if not isinstance( text_or_obj, dict ):
    text_or_obj = { 'text': text_or_obj }

  assert_that( filter.IsAllowed( text_or_obj ), equal_to( expected ) )


def _assert_accepts( filter, text ):
  _assert_accept_equals( filter, text, True )


def _assert_rejects( filter, text ):
  _assert_accept_equals( filter, text, False )


class ConfigPriority_test():

  def ConfigPriority_Global_test( self ):
    opts = { 'quiet_messages': { 'regex': 'taco' } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_rejects( f, 'This is a Taco' )
    _assert_accepts( f, 'This is a Burrito' )


  def ConfigPriority_Filetype_test( self ):
    opts = { 'quiet_messages'      : {},
             'java_quiet_messages' : { 'regex': 'taco' } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_rejects( f, 'This is a Taco' )
    _assert_accepts( f, 'This is a Burrito' )


  def ConfigPriority_FiletypeOverridesGlobal_test( self ):
    # NB: if the filetype doesn't override the global,
    #  we would reject burrito and accept taco
    opts = { 'quiet_messages'      : { 'regex': 'burrito'},
             'java_quiet_messages' : { 'regex': 'taco' } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_rejects( f, 'This is a Taco' )
    _assert_accepts( f, 'This is a Burrito' )


  def ConfigPriority_FiletypeDisablesGlobal_test( self ):
    # NB: if the filetype doesn't override the global,
    #  we would reject burrito and accept taco
    opts = { 'quiet_messages'      : { 'regex': 'taco'},
             'java_quiet_messages' : { 'regex': [] } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_accepts( f, 'This is a Taco' )
    _assert_accepts( f, 'This is a Burrito' )


class ListOrSingle_test():
  # NB: we already test the single config above

  def ListOrSingle_SingleList_test( self ):
    # NB: if the filetype doesn't override the global,
    #  we would reject burrito and accept taco
    opts = { 'quiet_messages' : { 'regex': [ 'taco' ] } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_rejects( f, 'This is a Taco' )
    _assert_accepts( f, 'This is a Burrito' )


  def ListOrSingle_MultiList_test( self ):
    # NB: if the filetype doesn't override the global,
    #  we would reject burrito and accept taco
    opts = { 'quiet_messages' : { 'regex': [ 'taco', 'burrito' ] } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_rejects( f, 'This is a Taco' )
    _assert_rejects( f, 'This is a Burrito' )


def Invert_test():
    opts = { 'quiet_messages' : { '!regex': 'taco' } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_accepts( f, 'This is a Taco' )
    _assert_rejects( f, 'This is a Burrito' )


class Level_test():

  def Level_warnings_test( self ):
    opts = { 'quiet_messages' : { 'level': 'warnings' } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_rejects( f, { 'text': 'This is an unimportant taco',
                          'kind': 'WARNING' } )
    _assert_accepts( f, { 'text': 'This taco will be shown',
                          'kind': 'ERROR' } )


  def Level_errors_test( self ):
    opts = { 'quiet_messages' : { 'level': 'errors' } }
    f = DiagnosticFilter.from_filetype( opts, [ 'java' ] )

    _assert_accepts( f, { 'text': 'This is an IMPORTANT taco',
                          'kind': 'WARNING' } )
    _assert_rejects( f, { 'text': 'This taco will NOT be shown',
                          'kind': 'ERROR' } )
