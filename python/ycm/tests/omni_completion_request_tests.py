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

from mock import MagicMock
from nose.tools import eq_
from hamcrest import assert_that, has_entries

from ycm.client.omni_completion_request import OmniCompletionRequest


def BuildOmnicompletionRequest( results ):
  omni_completer = MagicMock()
  omni_completer.ComputeCandidates = MagicMock( return_value = results )

  request = OmniCompletionRequest( omni_completer, None )
  request.Start()

  return request


def Done_AlwaysTrue_test():
  request = BuildOmnicompletionRequest( [] )

  eq_( request.Done(), True )


def Response_FromOmniCompleter_test():
  results = [ { "word": "test" } ]
  request = BuildOmnicompletionRequest( results )

  eq_( request.Response(), results )


def RawResponse_ConvertedFromOmniCompleter_test():
  vim_results = [
    { "word": "WORD", "abbr": "ABBR", "menu": "MENU",
      "kind": "KIND", "info": "INFO" },
    { "word": "WORD2", "abbr": "ABBR2", "menu": "MENU2",
      "kind": "KIND2", "info": "INFO" },
    { "word": "WORD", "abbr": "ABBR",  },
    {  },
  ]
  expected_results = [
    has_entries( { "insertion_text": "WORD", "menu_text": "ABBR",
                   "extra_menu_info": "MENU", "kind": [ "KIND" ],
                   "detailed_info": "INFO" } ),
    has_entries( { "insertion_text": "WORD2", "menu_text": "ABBR2",
                   "extra_menu_info": "MENU2", "kind": [ "KIND2" ],
                   "detailed_info": "INFO" } ),
    has_entries( { "insertion_text": "WORD", "menu_text": "ABBR",  } ),
    has_entries( {  } ),
  ]
  request = BuildOmnicompletionRequest( vim_results )

  results = request.RawResponse()

  eq_( len( results ), len( expected_results ) )
  for result, expected_result in zip( results, expected_results ):
    assert_that( result, expected_result )
