#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Chiel ten Brinke <ctenbrinke@gmail.com>
#                           Strahinja Val Markovic <val@markovic.io>
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

import vim
from ycm.completers.threaded_completer import ThreadedCompleter
from ycm import vimsupport

import urllib2
import urllib
import urlparse
import json


class CsharpCompleter( ThreadedCompleter ):
  """
  A Completer that uses the Omnisharp server as completion engine.
  """

  def __init__( self ):
    super( CsharpCompleter, self ).__init__()
    self.OmniSharp_host = vim.eval( 'g:OmniSharp_host' )

  def SupportedFiletypes( self ):
    """ Just csharp """
    return ['cs']

  def ComputeCandidates( self, unused_query, unused_start_column ):
    return [ { 'word': str( completion['CompletionText'] ),
               'menu': str( completion['DisplayText'] ),
               'info': str( completion['Description'] ) }
             for completion in self.getCompletions() ]

  def getCompletions( self ):
    """Ask server for completions"""
    line, column = vimsupport.CurrentLineAndColumn()

    parameters = {}
    parameters['line'], parameters['column'] = line + 1, column + 1
    parameters['buffer'] = '\n'.join( vim.current.buffer )
    parameters['filename'] = vim.current.buffer.name

    resp = self.getResponse( '/autocomplete', parameters )
    if(json != ''):
      return json.loads( resp )
    return []

  def getResponse( self, endPoint, parameters={} ):
    """Handle communication with server"""
    target = urlparse.urljoin( self.OmniSharp_host , endPoint )
    parameters = urllib.urlencode( parameters )
    try:
      response = urllib2.urlopen( target, parameters )
      return response.read()
    except:
      return ''
