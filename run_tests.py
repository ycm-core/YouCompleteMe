#!/usr/bin/env python

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
python_path = [ p.join( DIR_OF_THIRD_PARTY, 'pythonfutures' ),
                p.join( DIR_OF_THIRD_PARTY, 'requests-futures' ),
                p.join( DIR_OF_THIRD_PARTY, 'requests_deps', 'chardet' ),
                p.join( DIR_OF_THIRD_PARTY, 'requests_deps', 'certifi' ),
                p.join( DIR_OF_THIRD_PARTY, 'requests_deps', 'idna' ),
                p.join( DIR_OF_THIRD_PARTY, 'requests_deps', 'requests' ),
                p.join( DIR_OF_THIRD_PARTY, 'requests_deps', 'urllib3', 'src' ),
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

  parsed_args, nosetests_args = parser.parse_known_args()

  if 'COVERAGE' in os.environ:
    parsed_args.coverage = ( os.environ[ 'COVERAGE' ] == 'true' )

  return parsed_args, nosetests_args


def BuildYcmdLibs( args ):
  if not args.skip_build:
    subprocess.check_call( [
      sys.executable,
      p.join( DIR_OF_THIS_SCRIPT, 'third_party', 'ycmd', 'build.py' )
    ] )


def NoseTests( parsed_args, extra_nosetests_args ):
  # Always passing --with-id to nosetests enables non-surprising usage of
  # its --failed flag.
  nosetests_args = [ '-v', '--with-id' ]

  if parsed_args.coverage:
    nosetests_args += [ '--with-coverage',
                        '--cover-erase',
                        '--cover-package=ycm',
                        '--cover-html' ]

  if extra_nosetests_args:
    nosetests_args.extend( extra_nosetests_args )
  else:
    nosetests_args.append( p.join( DIR_OF_THIS_SCRIPT, 'python' ) )

  subprocess.check_call( [ sys.executable, '-m', 'nose' ] + nosetests_args )


def Main():
  ( parsed_args, nosetests_args ) = ParseArguments()
  if not parsed_args.no_flake8:
    RunFlake8()
  BuildYcmdLibs( parsed_args )
  NoseTests( parsed_args, nosetests_args )


if __name__ == "__main__":
  Main()
