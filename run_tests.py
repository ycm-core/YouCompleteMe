#!/usr/bin/env python

import os
import subprocess
import os.path as p
import sys

DIR_OF_THIS_SCRIPT = p.dirname( p.abspath( __file__ ) )
DIR_OF_THIRD_PARTY = p.join( DIR_OF_THIS_SCRIPT, 'third_party' )
DIR_OF_YCMD_THIRD_PARTY = p.join( DIR_OF_THIRD_PARTY, 'ycmd', 'third_party' )

python_path = []
for folder in os.listdir( DIR_OF_THIRD_PARTY ):
  python_path.append( p.abspath( p.join( DIR_OF_THIRD_PARTY, folder ) ) )
for folder in os.listdir( DIR_OF_YCMD_THIRD_PARTY ):
  # We skip python-future because it needs to be inserted in sys.path AFTER
  # the standard library imports but we can't do that with PYTHONPATH because
  # the std lib paths are always appended to PYTHONPATH. We do it correctly in
  # prod in ycmd/utils.py because we have access to the right sys.path.
  # So for dev, we rely on python-future being installed correctly with
  #   pip install -r test_requirements.txt
  #
  # Pip knows how to install this correctly so that it doesn't matter where in
  # sys.path the path is.
  if folder == 'python-future':
    continue
  python_path.append( p.abspath( p.join( DIR_OF_YCMD_THIRD_PARTY, folder ) ) )
if os.environ.get( 'PYTHONPATH' ):
  python_path.append( os.environ[ 'PYTHONPATH' ] )
os.environ[ 'PYTHONPATH' ] = os.pathsep.join( python_path )

sys.path.insert( 1, p.abspath( p.join( DIR_OF_YCMD_THIRD_PARTY,
                                       'argparse' ) ) )

import argparse


def RunFlake8():
  print( 'Running flake8' )
  subprocess.check_call( [
    sys.executable, '-m', 'flake8', p.join( DIR_OF_THIS_SCRIPT, 'python' )
  ] )


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
