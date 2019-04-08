# Copyright (C) 2011-2019 ycmd contributors
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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

import vim
from ycm import vimsupport
from ycmd import utils
from ycmd.completers.completer import Completer
from ycm.client.base_request import BaseRequest

OMNIFUNC_RETURNED_BAD_VALUE = 'Omnifunc returned bad value to YCM!'
OMNIFUNC_NOT_LIST = ( 'Omnifunc did not return a list or a dict with a "words" '
                     ' list when expected.' )


class OmniCompleter( Completer ):
  def __init__( self, user_options ):
    super( OmniCompleter, self ).__init__( user_options )
    self._omnifunc = None


  def SupportedFiletypes( self ):
    return []


  def ShouldUseCache( self ):
    return bool( self.user_options[ 'cache_omnifunc' ] )


  def ShouldUseNow( self, request_data ):
    self._omnifunc = utils.ToUnicode( vim.eval( '&omnifunc' ) )
    if not self._omnifunc:
      return False
    if self.ShouldUseCache():
      return super( OmniCompleter, self ).ShouldUseNow( request_data )
    return self.ShouldUseNowInner( request_data )


  def ShouldUseNowInner( self, request_data ):
    if request_data[ 'force_semantic' ]:
      return True
    disabled_filetypes = self.user_options[
      'filetype_specific_completion_to_disable' ]
    if not vimsupport.CurrentFiletypesEnabled( disabled_filetypes ):
      return False
    return super( OmniCompleter, self ).ShouldUseNowInner( request_data )


  def ComputeCandidates( self, request_data ):
    if self.ShouldUseCache():
      return super( OmniCompleter, self ).ComputeCandidates( request_data )
    if self.ShouldUseNowInner( request_data ):
      return self.ComputeCandidatesInner( request_data )
    return []


  def ComputeCandidatesInner( self, request_data ):
    if not self._omnifunc:
      return []

    # Calling directly the omnifunc may move the cursor position. This is the
    # case with the default Vim omnifunc for C-family languages
    # (ccomplete#Complete) which calls searchdecl to find a declaration. This
    # function is supposed to move the cursor to the found declaration but it
    # doesn't when called through the omni completion mapping (CTRL-X CTRL-O).
    # So, we restore the cursor position after the omnifunc calls.
    line, column = vimsupport.CurrentLineAndColumn()

    try:
      start_column = vimsupport.GetIntValue( self._omnifunc + '(1,"")' )

      # Vim only stops completion if the value returned by the omnifunc is -3 or
      # -2. In other cases, if the value is negative or greater than the current
      # column, the start column is set to the current column; otherwise, the
      # value is used as the start column.
      if start_column in ( -3, -2 ):
        return []
      if start_column < 0 or start_column > column:
        start_column = column

      # Use the start column calculated by the omnifunc, rather than our own
      # interpretation. This is important for certain languages where our
      # identifier detection is either incorrect or not compatible with the
      # behaviour of the omnifunc. Note: do this before calling the omnifunc
      # because it affects the value returned by 'query'.
      request_data[ 'start_column' ] = start_column + 1

      # Vim internally moves the cursor to the start column before calling again
      # the omnifunc. Some omnifuncs like the one defined by the
      # LanguageClient-neovim plugin depend on this behavior to compute the list
      # of candidates.
      vimsupport.SetCurrentLineAndColumn( line, start_column )

      omnifunc_call = [ self._omnifunc,
                        "(0,'",
                        vimsupport.EscapeForVim( request_data[ 'query' ] ),
                        "')" ]
      items = vim.eval( ''.join( omnifunc_call ) )

      if isinstance( items, dict ) and 'words' in items:
        items = items[ 'words' ]

      if not hasattr( items, '__iter__' ):
        raise TypeError( OMNIFUNC_NOT_LIST )

      # Vim allows each item of the list to be either a string or a dictionary
      # but ycmd only supports lists where items are all strings or all
      # dictionaries. Convert all strings into dictionaries.
      for index, item in enumerate( items ):
        # Set the 'equal' field to 1 to disable Vim filtering.
        if not isinstance( item, dict ):
          items[ index ] = {
            'word': item,
            'equal': 1
          }
        else:
          item[ 'equal' ] = 1

      return items

    except ( TypeError, ValueError, vim.error ) as error:
      vimsupport.PostVimMessage(
        OMNIFUNC_RETURNED_BAD_VALUE + ' ' + str( error ) )
      return []

    finally:
      vimsupport.SetCurrentLineAndColumn( line, column )


  def FilterAndSortCandidatesInner( self, candidates, sort_property, query ):
    request_data = {
      'candidates': candidates,
      'sort_property': sort_property,
      'query': query
    }

    response = BaseRequest().PostDataToHandler( request_data,
                                                'filter_and_sort_candidates' )
    return response if response is not None else []
