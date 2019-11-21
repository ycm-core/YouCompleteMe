# Copyright (C) 2013-2019 YouCompleteMe contributors
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
import logging
from ycmd.utils import ToUnicode
from ycm.client.base_request import ( BaseRequest, DisplayServerException,
                                      MakeServerException )
from ycm import vimsupport
from ycm.vimsupport import NO_COMPLETIONS

_logger = logging.getLogger( __name__ )


class CompletionRequest( BaseRequest ):
  def __init__( self, request_data ):
    super( CompletionRequest, self ).__init__()
    self.request_data = request_data
    self._response_future = None


  def Start( self ):
    self._response_future = self.PostDataToHandlerAsync( self.request_data,
                                                         'completions' )


  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def _RawResponse( self ):
    if not self._response_future:
      return NO_COMPLETIONS

    response = self.HandleFuture( self._response_future,
                                  truncate_message = True )
    if not response:
      return NO_COMPLETIONS

    # Vim may not be able to convert the 'errors' entry to its internal format
    # so we remove it from the response.
    errors = response.pop( 'errors', [] )
    for e in errors:
      exception = MakeServerException( e )
      _logger.error( exception )
      DisplayServerException( exception, truncate_message = True )

    response[ 'line' ] = self.request_data[ 'line_num' ]
    response[ 'column' ] = self.request_data[ 'column_num' ]
    return response


  def Response( self ):
    response = self._RawResponse()
    response[ 'completions' ] = _ConvertCompletionDatasToVimDatas(
        response[ 'completions' ] )
    return response


  def OnCompleteDone( self ):
    if not self.Done():
      return

    if 'cs' in vimsupport.CurrentFiletypes():
      self._OnCompleteDone_Csharp()
    else:
      self._OnCompleteDone_FixIt()


  def _GetExtraDataUserMayHaveCompleted( self ):
    completed_item = vimsupport.GetVariableValue( 'v:completed_item' )

    # If Vim supports user_data (8.0.1493 or later), we actually know the
    # _exact_ element that was selected, having put its extra_data in the
    # user_data field. Otherwise, we have to guess by matching the values in the
    # completed item and the list of completions. Sometimes this returns
    # multiple possibilities, which is essentially unresolvable.
    if 'user_data' not in completed_item:
      completions = self._RawResponse()[ 'completions' ]
      return _FilterToMatchingCompletions( completed_item, completions )

    if completed_item[ 'user_data' ]:
      return [ json.loads( completed_item[ 'user_data' ] ) ]

    return []


  def _OnCompleteDone_Csharp( self ):
    extra_datas = self._GetExtraDataUserMayHaveCompleted()
    namespaces = [ _GetRequiredNamespaceImport( c ) for c in extra_datas ]
    namespaces = [ n for n in namespaces if n ]
    if not namespaces:
      return

    if len( namespaces ) > 1:
      choices = [ "{0} {1}".format( i + 1, n )
                  for i, n in enumerate( namespaces ) ]
      choice = vimsupport.PresentDialog( "Insert which namespace:", choices )
      if choice < 0:
        return
      namespace = namespaces[ choice ]
    else:
      namespace = namespaces[ 0 ]

    vimsupport.InsertNamespace( namespace )


  def _OnCompleteDone_FixIt( self ):
    extra_datas = self._GetExtraDataUserMayHaveCompleted()
    fixit_completions = [ _GetFixItCompletion( c ) for c in extra_datas ]
    fixit_completions = [ f for f in fixit_completions if f ]
    if not fixit_completions:
      return

    # If we have user_data in completions (8.0.1493 or later), then we would
    # only ever return max. 1 completion here. However, if we had to guess, it
    # is possible that we matched multiple completion items (e.g. for overloads,
    # or similar classes in multiple packages). In any case, rather than
    # prompting the user and disturbing her workflow, we just apply the first
    # one. This might be wrong, but the solution is to use a (very) new version
    # of Vim which supports user_data on completion items
    fixit_completion = fixit_completions[ 0 ]

    for fixit in fixit_completion:
      vimsupport.ReplaceChunks( fixit[ 'chunks' ], silent=True )


def _GetRequiredNamespaceImport( extra_data ):
  return extra_data.get( 'required_namespace_import' )


def _GetFixItCompletion( extra_data ):
  return extra_data.get( 'fixits' )


def _FilterToMatchingCompletions( completed_item, completions ):
  """Filter to completions matching the item Vim said was completed"""
  match_keys = [ 'word', 'abbr', 'menu', 'info' ]
  matched_completions = []
  for completion in completions:
    item = _ConvertCompletionDataToVimData( completion )

    def matcher( key ):
      return ( ToUnicode( completed_item.get( key, "" ) ) ==
               ToUnicode( item.get( key, "" ) ) )

    if all( matcher( i ) for i in match_keys ):
      matched_completions.append( completion.get( 'extra_data', {} ) )
  return matched_completions


def _GetCompletionInfoField( completion_data ):
  info = completion_data.get( 'detailed_info', '' )

  if 'extra_data' in completion_data:
    docstring = completion_data[ 'extra_data' ].get( 'doc_string', '' )
    if docstring:
      if info:
        info += '\n' + docstring
      else:
        info = docstring

  # This field may contain null characters e.g. \x00 in Python docstrings. Vim
  # cannot evaluate such characters so they are removed.
  return info.replace( '\x00', '' )


def _ConvertCompletionDataToVimData( completion_data ):
  # See :h complete-items for a description of the dictionary fields.
  return {
    'word'     : completion_data[ 'insertion_text' ],
    'abbr'     : completion_data.get( 'menu_text', '' ),
    'menu'     : completion_data.get( 'extra_menu_info', '' ),
    'info'     : _GetCompletionInfoField( completion_data ),
    'kind'     : ToUnicode( completion_data.get( 'kind', '' ) )[ :1 ].lower(),
    # Disable Vim filtering.
    'equal'    : 1,
    'dup'      : 1,
    'empty'    : 1,
    # We store the completion item extra_data as a string in the completion
    # user_data. This allows us to identify the _exact_ item that was completed
    # in the CompleteDone handler, by inspecting this item from v:completed_item
    #
    # We convert to string because completion user data items must be strings.
    #
    # Note: Not all versions of Vim support this (added in 8.0.1483), but adding
    # the item to the dictionary is harmless in earlier Vims.
    # Note: Since 8.2.0084 we don't need to use json.dumps() here.
    'user_data': json.dumps( completion_data.get( 'extra_data', {} ) )
  }


def _ConvertCompletionDatasToVimDatas( response_data ):
  return [ _ConvertCompletionDataToVimData( x ) for x in response_data ]
