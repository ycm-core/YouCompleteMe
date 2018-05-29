# Copyright (C) 2016-2017 YouCompleteMe contributors
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

from ycm.client.base_request import BaseRequest, BuildRequestData


class DebugInfoRequest( BaseRequest ):
  def __init__( self, extra_data = None ):
    super( DebugInfoRequest, self ).__init__()
    self._extra_data = extra_data
    self._response = None


  def Start( self ):
    request_data = BuildRequestData()
    if self._extra_data:
      request_data.update( self._extra_data )
    self._response = self.PostDataToHandler( request_data,
                                             'debug_info',
                                             display_message = False )


  def Response( self ):
    return self._response


def FormatDebugInfoResponse( response ):
  if not response:
    return 'Server errored, no debug info from server\n'
  message = _FormatYcmdDebugInfo( response )
  completer = response[ 'completer' ]
  if completer:
    message += _FormatCompleterDebugInfo( completer )
  return message


def _FormatYcmdDebugInfo( ycmd ):
  python = ycmd[ 'python' ]
  clang = ycmd[ 'clang' ]
  message = ( 'Server Python interpreter: {0}\n'
              'Server Python version: {1}\n'
              'Server has Clang support compiled in: {2}\n'
              'Clang version: {3}\n'.format( python[ 'executable' ],
                                             python[ 'version' ],
                                             clang[ 'has_support' ],
                                             clang[ 'version' ] ) )
  extra_conf = ycmd[ 'extra_conf' ]
  extra_conf_path = extra_conf[ 'path' ]
  if not extra_conf_path:
    message += 'No extra configuration file found\n'
  elif not extra_conf[ 'is_loaded' ]:
    message += ( 'Extra configuration file found but not loaded\n'
                 'Extra configuration path: {0}\n'.format( extra_conf_path ) )
  else:
    message += ( 'Extra configuration file found and loaded\n'
                 'Extra configuration path: {0}\n'.format( extra_conf_path ) )
  return message


def _FormatCompleterDebugInfo( completer ):
  message = '{0} completer debug information:\n'.format( completer[ 'name' ] )
  for server in completer[ 'servers' ]:
    name = server[ 'name' ]
    if server[ 'is_running' ]:
      address = server[ 'address' ]
      port = server[ 'port' ]
      if address and port:
        message += '  {0} running at: http://{1}:{2}\n'.format( name,
                                                                address,
                                                                port )
      else:
        message += '  {0} running\n'.format( name )
      message += '  {0} process ID: {1}\n'.format( name, server[ 'pid' ] )
    else:
      message += '  {0} not running\n'.format( name )
    message += '  {0} executable: {1}\n'.format( name, server[ 'executable' ] )
    logfiles = server[ 'logfiles' ]
    if logfiles:
      message += '  {0} logfiles:\n'.format( name )
      for logfile in logfiles:
        message += '    {0}\n'.format( logfile )
    else:
      message += '  No logfiles available\n'
    if 'extras' in server:
      for extra in server[ 'extras' ]:
        message += '  {0} {1}: {2}\n'.format( name,
                                              extra[ 'key' ],
                                              extra[ 'value' ] )
  for item in completer[ 'items' ]:
    message += '  {0}: {1}\n'.format( item[ 'key' ].capitalize(),
                                      item[ 'value' ] )
  return message


def SendDebugInfoRequest( extra_data = None ):
  request = DebugInfoRequest( extra_data )
  # This is a blocking call.
  request.Start()
  return request.Response()
