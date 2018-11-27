#!/usr/bin/env python

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import os
import subprocess
import sys
import os.path as p
import glob

PY_MAJOR, PY_MINOR, PY_PATCH = sys.version_info[ 0 : 3 ]
if not ( ( PY_MAJOR == 2 and PY_MINOR == 7 and PY_PATCH >= 1 ) or
         ( PY_MAJOR == 3 and PY_MINOR >= 4 ) or
         PY_MAJOR > 3 ):
  sys.exit( 'YouCompleteMe requires Python >= 2.7.1 or >= 3.4; '
            'your version of Python is ' + sys.version )

DIR_OF_THIS_SCRIPT = p.dirname( p.abspath( __file__ ) )
DIR_OF_OLD_LIBS = p.join( DIR_OF_THIS_SCRIPT, 'python' )


def CheckCall( args, **kwargs ):
  try:
    subprocess.check_call( args, **kwargs )
  except subprocess.CalledProcessError as error:
    sys.exit( error.returncode )


def Main():
  build_file = p.join( DIR_OF_THIS_SCRIPT, 'third_party', 'ycmd', 'build.py' )

  if not p.isfile( build_file ):
    sys.exit(
      'File {0} does not exist; you probably forgot to run:\n'
      '\tgit submodule update --init --recursive\n'.format( build_file ) )

  CheckCall( [ sys.executable, build_file ] + sys.argv[ 1: ] )

  # Remove old YCM libs if present so that YCM can start.
  old_libs = (
    glob.glob( p.join( DIR_OF_OLD_LIBS, '*ycm_core.*' ) ) +
    glob.glob( p.join( DIR_OF_OLD_LIBS, '*ycm_client_support.*' ) ) +
    glob.glob( p.join( DIR_OF_OLD_LIBS, '*clang*.*' ) ) )
  for lib in old_libs:
    os.remove( lib )


if __name__ == "__main__":
  Main()
