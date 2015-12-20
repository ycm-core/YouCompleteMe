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
    'flake8',
    '--select=F,C9',
    '--max-complexity=10',
    p.join( DIR_OF_THIS_SCRIPT, 'python' )
  ] )


def ParseArguments():
  parser = argparse.ArgumentParser()
  parser.add_argument( '--skip-build', action = 'store_true',
                       help = 'Do not build ycmd before testing.' )
  parser.add_argument( '--run-all', action = 'store_true',
                       help = 'Run all tests.' )

  return parser.parse_args()


def BuildYcmdLibs( args ):
  if not args.skip_build:
    subprocess.check_call( [
      sys.executable,
      p.join( DIR_OF_THIS_SCRIPT, 'third_party', 'ycmd', 'build.py' )
    ] )


def TestingVimscript():
  return os.environ.get( 'VIMSCRIPT' )


def NoseTests():
  subprocess.check_call( [
    'nosetests',
    '-v',
    p.join( DIR_OF_THIS_SCRIPT, 'python' ),
    '--exclude-dir={0}'.format( p.join( 'python', 'ycm', 'tests', 'vimscript' ) )
  ] )


def NoseVimscriptTests():
  subprocess.check_call( [
    'nosetests',
    '-v',
    p.join( DIR_OF_THIS_SCRIPT, 'python', 'ycm', 'tests', 'vimscript' )
  ] )


def Main():
  parsed_args = ParseArguments()
  RunFlake8()
  BuildYcmdLibs( parsed_args )

  if parsed_args.run_all:
    NoseTests()
    NoseVimscriptTests()
  elif TestingVimscript():
    NoseVimscriptTests()
  else:
    NoseTests()

if __name__ == "__main__":
  Main()
