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

from webtest import TestApp
from .. import server
from ..responses import BuildCompletionData
from nose.tools import ok_, eq_
import bottle

bottle.debug( True )


def GetCompletions_IdentifierCompleterWorks_test():
  app = TestApp( server.app )
  event_data = {
    'event_name': 'FileReadyToParse',
    'filetypes': ['foo'],
    'filepath': '/foo/bar',
    'file_data': {
      '/foo/bar': {
        'contents': 'foo foogoo ba',
        'filetypes': ['foo']
      }
    }
  }

  app.post_json( '/event_notification', event_data )

  line_value = 'oo foo foogoo ba';
  completion_data = {
    'query': 'oo',
    'filetypes': ['foo'],
    'filepath': '/foo/bar',
    'line_num': 0,
    'column_num': 2,
    'start_column': 0,
    'line_value': line_value,
    'file_data': {
      '/foo/bar': {
        'contents': line_value,
        'filetypes': ['foo']
      }
    }
  }

  eq_( [ BuildCompletionData( 'foo' ),
         BuildCompletionData( 'foogoo' ) ],
       app.post_json( '/get_completions', completion_data ).json )


def FiletypeCompletionAvailable_Works_test():
  app = TestApp( server.app )
  request_data = {
    'filetypes': ['cpp']
  }

  ok_( app.post_json( '/filetype_completion_available',
                      request_data ).json )
