#!/usr/bin/env python
#
# Copyright (C) 2013  Google Inc.
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

import time
import os
import copy
from ycm import utils
from threading import Thread, Lock

# This class implements the Bottle plugin API:
# http://bottlepy.org/docs/dev/plugindev.html
#
# The idea here is to decorate every route handler automatically so that on
# every request, we log when the request was made. Then a watchdog thread checks
# every check_interval_seconds whether the server has been idle for a time
# greater that the passed-in idle_suicide_seconds. If it has, we kill the
# server.
#
# We want to do this so that if something goes bonkers in Vim and the server
# never gets killed by the client, we don't end up with lots of zombie servers.
class WatchdogPlugin( object ):
  name = 'watchdog'
  api = 2


  def __init__( self,
                idle_suicide_seconds,
                check_interval_seconds = 60 * 10 ):
    self._check_interval_seconds = check_interval_seconds
    self._idle_suicide_seconds = idle_suicide_seconds
    self._last_request_time = time.time()
    self._last_request_time_lock = Lock()
    if idle_suicide_seconds <= 0:
      return
    self._watchdog_thread = Thread( target = self._WatchdogMain )
    self._watchdog_thread.daemon = True
    self._watchdog_thread.start()


  def _GetLastRequestTime( self ):
    with self._last_request_time_lock:
      return copy.deepcopy( self._last_request_time )


  def _SetLastRequestTime( self, new_value ):
    with self._last_request_time_lock:
      self._last_request_time = new_value


  def _WatchdogMain( self ):
    while True:
      time.sleep( self._check_interval_seconds )
      if time.time() - self._GetLastRequestTime() > self._idle_suicide_seconds:
        utils.TerminateProcess( os.getpid() )


  def __call__( self, callback ):
    def wrapper( *args, **kwargs ):
      self._SetLastRequestTime( time.time() )
      return callback( *args, **kwargs )
    return wrapper

