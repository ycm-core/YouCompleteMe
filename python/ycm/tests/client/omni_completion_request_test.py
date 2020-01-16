# Copyright (C) 2020 YouCompleteMe contributors
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

from unittest.mock import MagicMock
from hamcrest import assert_that, has_entries

from ycm.client.omni_completion_request import OmniCompletionRequest


def BuildOmnicompletionRequest( results, start_column = 1 ):
  omni_completer = MagicMock()
  omni_completer.ComputeCandidates = MagicMock( return_value = results )

  request_data = {
    'line_num': 1,
    'column_num': 1,
    'start_column': start_column
  }
  request = OmniCompletionRequest( omni_completer, request_data )
  request.Start()

  return request


def Done_AlwaysTrue_test():
  request = BuildOmnicompletionRequest( [] )

  assert_that( request.Done() )


def Response_FromOmniCompleter_test():
  results = [ { "word": "test" } ]
  request = BuildOmnicompletionRequest( results )

  assert_that( request.Response(), has_entries( {
    'line': 1,
    'column': 1,
    'completion_start_column': 1,
    'completions': results
  } ) )
