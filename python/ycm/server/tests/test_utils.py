#!/usr/bin/env python
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

import os
from .. import handlers
from ycm import user_options_store

def BuildRequest( **kwargs ):
  filepath = kwargs[ 'filepath' ] if 'filepath' in kwargs else '/foo'
  contents = kwargs[ 'contents' ] if 'contents' in kwargs else ''
  filetype = kwargs[ 'filetype' ] if 'filetype' in kwargs else 'foo'

  request = {
    'query': '',
    'line_num': 0,
    'column_num': 0,
    'start_column': 0,
    'filetypes': [ filetype ],
    'filepath': filepath,
    'line_value': contents,
    'file_data': {
      filepath: {
        'contents': contents,
        'filetypes': [ filetype ]
      }
    }
  }

  for key, value in kwargs.iteritems():
    if key in [ 'contents', 'filetype', 'filepath' ]:
      continue
    request[ key ] = value

    if key == 'line_num':
      lines = contents.splitlines()
      if len( lines ) > 1:
        # NOTE: assumes 0-based line_num
        request[ 'line_value' ] = lines[ value ]

  return request


def Setup():
  handlers.SetServerStateToDefaults()


def ChangeSpecificOptions( options ):
  current_options = dict( user_options_store.GetAll() )
  current_options.update( options )
  handlers.UpdateUserOptions( current_options )


def PathToTestDataDir():
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, 'testdata' )


def PathToTestFile( test_basename ):
  return os.path.join( PathToTestDataDir(), test_basename )


