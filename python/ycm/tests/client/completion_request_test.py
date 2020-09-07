# Copyright (C) 2015-2019 YouCompleteMe Contributors
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

import json
from hamcrest import assert_that, equal_to
from ycm.tests.conftest import UserOptions
from ycm.tests.test_utils import MockVimModule
vim_mock = MockVimModule()

from ycm.client import completion_request


class ConvertCompletionResponseToVimDatas_test:
  """ This class tests the
      completion_request.ConvertCompletionResponseToVimDatas method """

  def _Check( self, completion_data, expected_vim_data ):
    vim_data = completion_request.ConvertCompletionDataToVimData(
        completion_data )

    try:
      assert_that( vim_data, equal_to( expected_vim_data ) )
    except Exception:
      print( "Expected:\n"
               f"'{ expected_vim_data }'\n"
             "when parsing:\n'"
               f"{ completion_data }'\n"
             "But found:\n"
               f"'{ vim_data }'" )
      raise


  def AllFields_test( self ):
    extra_data = {
        'doc_string':    'DOC STRING',
    }
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'detailed_info':   'DETAILED INFO',
      'extra_data': extra_data,
    }, {
      'word'     : 'INSERTION TEXT',
      'abbr'     : 'MENU TEXT',
      'menu'     : 'EXTRA MENU INFO',
      'kind'     : 'k',
      'info'     : 'DETAILED INFO\nDOC STRING',
      'equal'    : 1,
      'dup'      : 1,
      'empty'    : 1,
      'user_data': json.dumps( extra_data ),
    } )


  def OnlyInsertionTextField_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT'
    }, {
      'word'     : 'INSERTION TEXT',
      'abbr'     : '',
      'menu'     : '',
      'kind'     : '',
      'info'     : '',
      'equal'    : 1,
      'dup'      : 1,
      'empty'    : 1,
      'user_data': '{}',
    } )


  def JustDetailedInfo_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'detailed_info':   'DETAILED INFO',
    }, {
      'word'     : 'INSERTION TEXT',
      'abbr'     : 'MENU TEXT',
      'menu'     : 'EXTRA MENU INFO',
      'kind'     : 'k',
      'info'     : 'DETAILED INFO',
      'equal'    : 1,
      'dup'      : 1,
      'empty'    : 1,
      'user_data': '{}',
    } )


  def JustDocString_test( self ):
    extra_data = {
      'doc_string':    'DOC STRING',
    }
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'extra_data': extra_data,
    }, {
      'word'     : 'INSERTION TEXT',
      'abbr'     : 'MENU TEXT',
      'menu'     : 'EXTRA MENU INFO',
      'kind'     : 'k',
      'info'     : 'DOC STRING',
      'equal'    : 1,
      'dup'      : 1,
      'empty'    : 1,
      'user_data': json.dumps( extra_data ),
    } )


  def ExtraInfoNoDocString_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'extra_data': {
      },
    }, {
      'word'     : 'INSERTION TEXT',
      'abbr'     : 'MENU TEXT',
      'menu'     : 'EXTRA MENU INFO',
      'kind'     : 'k',
      'info'     : '',
      'equal'    : 1,
      'dup'      : 1,
      'empty'    : 1,
      'user_data': '{}',
    } )


  def NullCharactersInExtraInfoAndDocString_test( self ):
    extra_data = {
      'doc_string': 'DOC\x00STRING'
    }
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'detailed_info':   'DETAILED\x00INFO',
      'extra_data': extra_data,
    }, {
      'word'     : 'INSERTION TEXT',
      'abbr'     : 'MENU TEXT',
      'menu'     : 'EXTRA MENU INFO',
      'kind'     : 'k',
      'info'     : 'DETAILEDINFO\nDOCSTRING',
      'equal'    : 1,
      'dup'      : 1,
      'empty'    : 1,
      'user_data': json.dumps( extra_data ),
    } )


  def ExtraInfoNoDocStringWithDetailedInfo_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'detailed_info':   'DETAILED INFO',
      'extra_data': {
      },
    }, {
      'word'     : 'INSERTION TEXT',
      'abbr'     : 'MENU TEXT',
      'menu'     : 'EXTRA MENU INFO',
      'kind'     : 'k',
      'info'     : 'DETAILED INFO',
      'equal'    : 1,
      'dup'      : 1,
      'empty'    : 1,
      'user_data': '{}',
    } )


  def EmptyInsertionText_test( self ):
    extra_data = {
      'doc_string':    'DOC STRING',
    }
    self._Check( {
      'insertion_text':  '',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'detailed_info':   'DETAILED INFO',
      'extra_data': extra_data,
    }, {
      'word'     : '',
      'abbr'     : 'MENU TEXT',
      'menu'     : 'EXTRA MENU INFO',
      'kind'     : 'k',
      'info'     : 'DETAILED INFO\nDOC STRING',
      'equal'    : 1,
      'dup'      : 1,
      'empty'    : 1,
      'user_data': json.dumps( extra_data ),
    } )


  def TruncateForPopup_test( self, *args ):
    with UserOptions( { '&columns': 60, '&completeopt': b'popup,menuone' } ):
      extra_data = {
        'doc_string':    'DOC STRING',
      }
      self._Check( {
        'insertion_text':  '',
        'menu_text':       'MENU TEXT',
        'extra_menu_info': 'ESPECIALLY LONG EXTRA MENU INFO LOREM IPSUM DOLOR',
        'kind':            'K',
        'detailed_info':   'DETAILED INFO',
        'extra_data': extra_data,
      }, {
        'word'     : '',
        'abbr'     : 'MENU TEXT',
        'menu'     : 'ESPECIALLY LONG E...',
        'kind'     : 'k',
        'info'     : 'ESPECIALLY LONG EXTRA MENU INFO LOREM IPSUM DOLOR\n\n' +
                     'DETAILED INFO\nDOC STRING',
        'equal'    : 1,
        'dup'      : 1,
        'empty'    : 1,
        'user_data': json.dumps( extra_data ),
      } )


  def OnlyTruncateForPopupIfNecessary_test( self, *args ):
    with UserOptions( { '&columns': 60, '&completeopt': b'popup,menuone' } ):
      extra_data = {
        'doc_string':    'DOC STRING',
      }
      self._Check( {
        'insertion_text':  '',
        'menu_text':       'MENU TEXT',
        'extra_menu_info': 'EXTRA MENU INFO',
        'kind':            'K',
        'detailed_info':   'DETAILED INFO',
        'extra_data': extra_data,
      }, {
        'word'     : '',
        'abbr'     : 'MENU TEXT',
        'menu'     : 'EXTRA MENU INFO',
        'kind'     : 'k',
        'info'     : 'DETAILED INFO\nDOC STRING',
        'equal'    : 1,
        'dup'      : 1,
        'empty'    : 1,
        'user_data': json.dumps( extra_data ),
      } )


  def DontTruncateIfNotPopup_test( self, *args ):
    with UserOptions( { '&columns': 60, '&completeopt': b'preview,menuone' } ):
      extra_data = {
        'doc_string':    'DOC STRING',
      }
      self._Check( {
        'insertion_text':  '',
        'menu_text':       'MENU TEXT',
        'extra_menu_info': 'ESPECIALLY LONG EXTRA MENU INFO LOREM IPSUM DOLOR',
        'kind':            'K',
        'detailed_info':   'DETAILED INFO',
        'extra_data': extra_data,
      }, {
        'word'     : '',
        'abbr'     : 'MENU TEXT',
        'menu'     : 'ESPECIALLY LONG EXTRA MENU INFO LOREM IPSUM DOLOR',
        'kind'     : 'k',
        'info'     : 'DETAILED INFO\nDOC STRING',
        'equal'    : 1,
        'dup'      : 1,
        'empty'    : 1,
        'user_data': json.dumps( extra_data ),
      } )


  def TruncateForPopupWithoutDuplication_test( self, *args ):
    with UserOptions( { '&columns': 60, '&completeopt': b'popup,menuone' } ):
      extra_data = {
        'doc_string':    'DOC STRING',
      }
      self._Check( {
        'insertion_text':  '',
        'menu_text':       'MENU TEXT',
        'extra_menu_info': 'ESPECIALLY LONG METHOD SIGNATURE LOREM IPSUM',
        'kind':            'K',
        'detailed_info':   'ESPECIALLY LONG METHOD SIGNATURE LOREM IPSUM',
        'extra_data': extra_data,
      }, {
        'word'     : '',
        'abbr'     : 'MENU TEXT',
        'menu'     : 'ESPECIALLY LONG M...',
        'kind'     : 'k',
        'info'     : 'ESPECIALLY LONG METHOD SIGNATURE LOREM IPSUM\n' +
                     'DOC STRING',
        'equal'    : 1,
        'dup'      : 1,
        'empty'    : 1,
        'user_data': json.dumps( extra_data ),
      } )
