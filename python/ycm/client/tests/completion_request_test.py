#!/usr/bin/env python
#
# Copyright (C) 2015 YouCompleteMe Contributors
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

from nose.tools import eq_
from ycm.test_utils import MockVimModule
vim_mock = MockVimModule()

from .. import completion_request

class ConvertCompletionResponseToVimDatas_test:
  """ This class tests the
      completion_request._ConvertCompletionResponseToVimDatas method """

  def _Check( self, completion_data, expected_vim_data ):
    vim_data = completion_request.ConvertCompletionDataToVimData(
        completion_data )

    try:
      eq_( expected_vim_data, vim_data )
    except:
      print "Expected:\n'{0}'\nwhen parsing:\n'{1}'\nBut found:\n'{2}'".format(
          expected_vim_data,
          completion_data,
          vim_data )
      raise


  def All_Fields_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'detailed_info':   'DETAILED INFO',
      'extra_data': {
        'doc_string':    'DOC STRING',
      },
    }, {
      'word': 'INSERTION TEXT',
      'abbr': 'MENU TEXT',
      'menu': 'EXTRA MENU INFO',
      'kind': 'k',
      'info': 'DETAILED INFO\nDOC STRING',
      'dup' : 1,
    } )


  def Just_Detailed_Info_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'detailed_info':   'DETAILED INFO',
    }, {
      'word': 'INSERTION TEXT',
      'abbr': 'MENU TEXT',
      'menu': 'EXTRA MENU INFO',
      'kind': 'k',
      'info': 'DETAILED INFO',
      'dup' : 1,
    } )


  def Just_Doc_String_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'extra_data': {
        'doc_string':    'DOC STRING',
      },
    }, {
      'word': 'INSERTION TEXT',
      'abbr': 'MENU TEXT',
      'menu': 'EXTRA MENU INFO',
      'kind': 'k',
      'info': 'DOC STRING',
      'dup' : 1,
    } )


  def Extra_Info_No_Doc_String_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'extra_data': {
      },
    }, {
      'word': 'INSERTION TEXT',
      'abbr': 'MENU TEXT',
      'menu': 'EXTRA MENU INFO',
      'kind': 'k',
      'dup' : 1,
    } )


  def Extra_Info_No_Doc_String_With_Detailed_Info_test( self ):
    self._Check( {
      'insertion_text':  'INSERTION TEXT',
      'menu_text':       'MENU TEXT',
      'extra_menu_info': 'EXTRA MENU INFO',
      'kind':            'K',
      'detailed_info':   'DETAILED INFO',
      'extra_data': {
      },
    }, {
      'word': 'INSERTION TEXT',
      'abbr': 'MENU TEXT',
      'menu': 'EXTRA MENU INFO',
      'kind': 'k',
      'info': 'DETAILED INFO',
      'dup' : 1,
    } )
