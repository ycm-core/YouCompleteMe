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

PY_MAJOR, PY_MINOR = sys.version_info[ 0 : 2 ]
if not ( ( PY_MAJOR == 2 and PY_MINOR >= 6 ) or
         ( PY_MAJOR == 3 and PY_MINOR >= 3 ) or
         PY_MAJOR > 3 ):
  sys.exit( 'YouCompleteMe requires Python >= 2.6 or >= 3.3; '
            'your version of Python is ' + sys.version )

DIR_OF_THIS_SCRIPT = p.dirname( p.abspath( __file__ ) )
DIR_OF_OLD_LIBS = p.join( DIR_OF_THIS_SCRIPT, 'python' )


def Main():
  build_file = p.join( DIR_OF_THIS_SCRIPT, 'third_party', 'ycmd', 'build.py' )

  if not p.isfile( build_file ):
    sys.exit( 'File ' + build_file + ' does not exist; you probably forgot '
              'to run:\n\tgit submodule update --init --recursive\n\n' )

  python_binary = sys.executable
  try:
    print("Building ycmd using [%s] with python binary [%s]:" % build_file, python_binary)
    subprocess.check_call( [ python_binary, build_file ] + sys.argv[1:] )
  except subprocess.CalledProcessError as processError:
    print("\nException raised while building ycmd:\n" + str(processError))

  # Remove old YCM libs if present so that YCM can start.
  old_libs = (
    glob.glob( p.join( DIR_OF_OLD_LIBS, '*ycm_core.*' ) ) +
    glob.glob( p.join( DIR_OF_OLD_LIBS, '*ycm_client_support.*' ) ) +
    glob.glob( p.join( DIR_OF_OLD_LIBS, '*clang*.*') ) )
  for lib in old_libs:
    os.remove( lib )

if __name__ == "__main__":
  Main()
