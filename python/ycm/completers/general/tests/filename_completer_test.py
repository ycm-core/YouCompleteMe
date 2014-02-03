#!/usr/bin/env python
#
# Copyright (C) 2014  Davit Samvelyan <davitsamvelyan@gmail.com>
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

import os
from nose.tools import eq_
from ycm.completers.general.filename_completer import FilenameCompleter
from ycm import user_options_store

test_dir = os.path.dirname( os.path.abspath( __file__ ) )
data_dir = os.path.join( test_dir, "testdata", "filename_completer" )
file_path = os.path.join( data_dir, "test.cpp" )

fnc = FilenameCompleter( user_options_store.DefaultOptions() )
# We cache include flags for test.cpp file for unit testing.
fnc._flags.flags_for_file[ file_path ] = [
  "-I", os.path.join( data_dir, "include" ),
  "-I", os.path.join( data_dir, "include", "Qt" ),
  "-I", os.path.join( data_dir, "include", "QtGui" ),
]

request_data = {
  'filepath' : file_path,
  'file_data' : { file_path : { 'filetypes' : 'cpp' } }
}

def GetCompletionData( request_data ):
  request_data[ 'start_column' ] = len( request_data[ 'line_value' ] )
  candidates = fnc.ComputeCandidatesInner( request_data )
  return [ ( c[ 'insertion_text' ], c[ 'extra_menu_info' ] ) for c in candidates ]



def QuotedIncludeCompletion_test():
  request_data[ 'line_value' ] = '#include "'
  data = GetCompletionData( request_data )
  eq_( [
        ( 'include',  '[Dir]' ),
        ( 'Qt',       '[Dir]' ),
        ( 'QtGui',    '[File&Dir]' ),
        ( 'QDialog',  '[File]' ),
        ( 'QWidget',  '[File]' ),
        ( 'test.cpp', '[File]' ),
        ( 'test.hpp', '[File]' ),
       ], data )

  request_data[ 'line_value' ] = '#include "include/'
  data = GetCompletionData( request_data )
  eq_( [
        ( 'Qt',       '[Dir]' ),
        ( 'QtGui',    '[Dir]' ),
       ], data )


def IncludeCompletion_test():
  request_data[ 'line_value' ] = '#include <'
  data = GetCompletionData( request_data )
  eq_( [
        ( 'Qt',       '[Dir]' ),
        ( 'QtGui',    '[File&Dir]' ),
        ( 'QDialog',  '[File]' ),
        ( 'QWidget',  '[File]' ),
       ], data )

  request_data[ 'line_value' ] = '#include <QtGui/'
  data = GetCompletionData( request_data )
  eq_( [
        ( 'QDialog',  '[File]' ),
        ( 'QWidget',  '[File]' ),
       ], data )


def SystemPathCompletion_test():
  request_data[ 'line_value' ] = 'const char* c = "./'
  # Order of system path completion entries may differ
  # on different systems
  data = sorted( GetCompletionData( request_data ) )
  eq_( [
        ( 'include',  '[Dir]' ),
        ( 'test.cpp', '[File]' ),
        ( 'test.hpp', '[File]' ),
       ], data )

  request_data[ 'line_value' ] = 'const char* c = "./include/'
  data = sorted( GetCompletionData( request_data ) )
  eq_( [
        ( 'Qt',       '[Dir]' ),
        ( 'QtGui',    '[Dir]' ),
       ], data )
