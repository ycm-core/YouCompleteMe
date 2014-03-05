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

from server_utils import SetUpPythonPath
SetUpPythonPath()

import sys
import logging
import json
import argparse
import waitress
import signal
from ycm import user_options_store
from ycm import extra_conf_store
from ycm import utils
from ycm.server.watchdog_plugin import WatchdogPlugin

def YcmCoreSanityCheck():
  if 'ycm_core' in sys.modules:
    raise RuntimeError( 'ycm_core already imported, ycmd has a bug!' )


# We manually call sys.exit() on SIGTERM and SIGINT so that atexit handlers are
# properly executed.
def SetUpSignalHandler(stdout, stderr, keep_logfiles):
  def SignalHandler( signum, frame ):
    if stderr:
      # Reset stderr, just in case something tries to use it
      tmp = sys.stderr
      sys.stderr = sys.__stderr__
      tmp.close()
    if stdout:
      # Reset stdout, just in case something tries to use it
      tmp = sys.stdout
      sys.stdout = sys.__stdout__
      tmp.close()

    if not keep_logfiles:
      if stderr:
        utils.RemoveIfExists( stderr )
      if stdout:
        utils.RemoveIfExists( stdout )

    sys.exit()

  for sig in [ signal.SIGTERM,
               signal.SIGINT ]:
    signal.signal( sig, SignalHandler )


def Main():
  parser = argparse.ArgumentParser()
  parser.add_argument( '--host', type = str, default = 'localhost',
                       help = 'server hostname')
  # Default of 0 will make the OS pick a free port for us
  parser.add_argument( '--port', type = int, default = 0,
                       help = 'server port')
  parser.add_argument( '--log', type = str, default = 'info',
                       help = 'log level, one of '
                              '[debug|info|warning|error|critical]' )
  parser.add_argument( '--idle_suicide_seconds', type = int, default = 0,
                       help = 'num idle seconds before server shuts down')
  parser.add_argument( '--options_file', type = str, default = '',
                       help = 'file with user options, in JSON format' )
  parser.add_argument( '--stdout', type = str, default = None,
                       help = 'optional file to use for stdout' )
  parser.add_argument( '--stderr', type = str, default = None,
                       help = 'optional file to use for stderr' )
  parser.add_argument( '--keep_logfiles', action = 'store_true', default = None,
                       help = 'retain logfiles after the server exits' )
  args = parser.parse_args()

  if args.stdout is not None:
    sys.stdout = open(args.stdout, "w")
  if args.stderr is not None:
    sys.stderr = open(args.stderr, "w")

  numeric_level = getattr( logging, args.log.upper(), None )
  if not isinstance( numeric_level, int ):
    raise ValueError( 'Invalid log level: %s' % args.log )

  # Has to be called before any call to logging.getLogger()
  logging.basicConfig( format = '%(asctime)s - %(levelname)s - %(message)s',
                       level = numeric_level )

  options = ( json.load( open( args.options_file, 'r' ) )
              if args.options_file
              else user_options_store.DefaultOptions() )
  user_options_store.SetAll( options )

  # This ensures that ycm_core is not loaded before extra conf
  # preload was run.
  YcmCoreSanityCheck()
  extra_conf_store.CallGlobalExtraConfYcmCorePreloadIfExists()

  # This can't be a top-level import because it transitively imports
  # ycm_core which we want to be imported ONLY after extra conf
  # preload has executed.
  from ycm.server import handlers
  handlers.UpdateUserOptions( options )
  SetUpSignalHandler(args.stdout, args.stderr, args.keep_logfiles)
  handlers.app.install( WatchdogPlugin( args.idle_suicide_seconds ) )
  waitress.serve( handlers.app,
                  host = args.host,
                  port = args.port,
                  threads = 30 )


if __name__ == "__main__":
  Main()

