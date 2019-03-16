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

version = sys.version_info[ 0 : 3 ]
if version < ( 2, 7, 1 ) or ( 3, 0, 0 ) <= version < ( 3, 5, 1 ):
  sys.exit( 'YouCompleteMe requires Python >= 2.7.1 or >= 3.5.1; '
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
