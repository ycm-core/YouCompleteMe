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
  message = (
    f'Server Python interpreter: { python[ "executable" ] }\n'
    f'Server Python version: { python[ "version" ] }\n'
    f'Server has Clang support compiled in: { clang[ "has_support" ] }\n'
    f'Clang version: { clang[ "version" ] }\n' )
  extra_conf = ycmd[ 'extra_conf' ]
  extra_conf_path = extra_conf[ 'path' ]
  if not extra_conf_path:
    message += 'No extra configuration file found\n'
  elif not extra_conf[ 'is_loaded' ]:
    message += ( 'Extra configuration file found but not loaded\n'
                 f'Extra configuration path: { extra_conf_path }\n' )
  else:
    message += ( 'Extra configuration file found and loaded\n'
                 f'Extra configuration path: { extra_conf_path }\n' )
  return message


def _FormatCompleterDebugInfo( completer ):
  message = f'{ completer[ "name" ] } completer debug information:\n'
  for server in completer[ 'servers' ]:
    name = server[ 'name' ]
    if server[ 'is_running' ]:
      address = server[ 'address' ]
      port = server[ 'port' ]
      if address and port:
        message += f'  { name } running at: http://{ address }:{ port }\n'
      else:
        message += f'  { name } running\n'
      message += f'  { name } process ID: { server[ "pid" ] }\n'
    else:
      message += f'  { name } not running\n'
    message += f'  { name } executable: { server[ "executable" ] }\n'
    logfiles = server[ 'logfiles' ]
    if logfiles:
      message += f'  { name } logfiles:\n'
      for logfile in logfiles:
        message += f'    { logfile }\n'
    else:
      message += '  No logfiles available\n'
    if 'extras' in server:
      for extra in server[ 'extras' ]:
        message += f'  { name } { extra[ "key" ] }: { extra[ "value" ] }\n'
  for item in completer[ 'items' ]:
    message += f'  { item[ "key" ].capitalize() }: { item[ "value" ] }\n'
  return message


def SendDebugInfoRequest( extra_data = None ):
  request = DebugInfoRequest( extra_data )
  # This is a blocking call.
  request.Start()
  return request.Response()
