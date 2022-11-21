#!/usr/bin/env python3

import argparse
import glob
import os
import os.path as p
import subprocess
import sys

DIR_OF_THIS_SCRIPT = p.dirname( p.abspath( __file__ ) )
DIR_OF_THIRD_PARTY = p.join( DIR_OF_THIS_SCRIPT, 'third_party' )

# We don't include python-future (not to be confused with pythonfutures) because
# it needs to be inserted in sys.path AFTER the standard library imports but we
# can't do that with PYTHONPATH because the std lib paths are always appended to
# PYTHONPATH. We do it correctly inside Vim because we have access to the right
# sys.path. So for dev, we rely on python-future being installed correctly with
#
#   pip install -r python/test_requirements.txt
#
# Pip knows how to install this correctly so that it doesn't matter where in
# sys.path the path is.
python_path = [ p.join( DIR_OF_THIS_SCRIPT, 'python' ),
                p.join( DIR_OF_THIRD_PARTY, 'ycmd' ) ]
if os.environ.get( 'PYTHONPATH' ):
  python_path.append( os.environ[ 'PYTHONPATH' ] )
os.environ[ 'PYTHONPATH' ] = os.pathsep.join( python_path )


def RunFlake8():
  print( 'Running flake8' )
  args = [ sys.executable,
           '-m',
           'flake8',
           p.join( DIR_OF_THIS_SCRIPT, 'python' ) ]
  root_dir_scripts = glob.glob( p.join( DIR_OF_THIS_SCRIPT, '*.py' ) )
  args.extend( root_dir_scripts )
  subprocess.check_call( args )


def ParseArguments():
  parser = argparse.ArgumentParser()
  parser.add_argument( '--skip-build', action = 'store_true',
                       help = 'Do not build ycmd before testing' )
  parser.add_argument( '--coverage', action = 'store_true',
                       help = 'Enable coverage report' )
  parser.add_argument( '--no-flake8', action = 'store_true',
                       help = 'Do not run flake8' )
  parser.add_argument( '--dump-path', action = 'store_true',
                       help = 'Dump the PYTHONPATH required to run tests '
                              'manually, then exit.' )

  parsed_args, unittest_args = parser.parse_known_args()

  if 'COVERAGE' in os.environ:
    parsed_args.coverage = ( os.environ[ 'COVERAGE' ] == 'true' )

  return parsed_args, unittest_args


def BuildYcmdLibs( args ):
  if not args.skip_build:
    subprocess.check_call( [
      sys.executable,
      p.join( DIR_OF_THIS_SCRIPT, 'third_party', 'ycmd', 'build.py' ),
      '--quiet'
    ] )


def UnittestTests( parsed_args, extra_unittest_args ):
  # if any extra arg is a specific file, or the '--' token, then assume the
  # arguments are unittest-aware test selection:
  #  - don't use discover
  #  - don't set the pattern to search for
  unittest_args = [ '-cb' ]
  prefer_regular = any( arg == '--' or p.isfile( arg )
                        for arg in extra_unittest_args )
  if not prefer_regular:
    unittest_args += [ '-p', '*_test.py' ]

  if extra_unittest_args:
    unittest_args.extend( extra_unittest_args )
  if not ( prefer_regular and extra_unittest_args ):
    unittest_args.append( '-s' )
    test_directory = p.join( DIR_OF_THIS_SCRIPT, 'python', 'ycm', 'tests' )
    unittest_args.append( test_directory )

  if parsed_args.coverage:
    executable = [ sys.executable, '-We', '-m', 'coverage', 'run' ]
  else:
    executable = [ sys.executable, '-We' ]

  unittest = [ '-m', 'unittest' ]
  if not prefer_regular:
    unittest.append( 'discover' )
  subprocess.check_call( executable + unittest + unittest_args )


def Main():
  ( parsed_args, unittest_args ) = ParseArguments()
  if parsed_args.dump_path:
    print( os.environ[ 'PYTHONPATH' ] )
    sys.exit()

  if not parsed_args.no_flake8:
    RunFlake8()

  BuildYcmdLibs( parsed_args )
  UnittestTests( parsed_args, unittest_args )


if __name__ == "__main__":
  Main()
