import os

flags = [
'-Wall',
'-Wextra',
'-Werror',
'-Wc++98-compat',
'-Wno-long-long',
'-Wno-variadic-macros',
'-DNDEBUG',
'-isystem',
'../BoostParts',
'-isystem',
# This path will only work on OS X, but extra paths that don't exist are not
# harmful
'/System/Library/Frameworks/Python.framework/Headers',
'-isystem',
'../llvm/include',
'-isystem',
'../llvm/tools/clang/include',
'-I',
'.',
'-isystem',
'./tests/gmock/gtest',
'-isystem',
'./tests/gmock/gtest/include',
'-isystem',
'./tests/gmock',
'-isystem',
'./tests/gmock/include'
]

def DirectoryOfThisScript():
  return os.path.dirname( os.path.abspath( __file__ ) )


def MakeAbsoluteIfRelativePath( path ):
  if not path.startswith( '.' ):
    return path

  full_path = os.path.join( DirectoryOfThisScript(), path )
  return os.path.normpath( full_path )


def FlagsForFile( filename ):
  results = {}
  results[ 'flags' ] = [ MakeAbsoluteIfRelativePath( x ) for x in flags ]
  results[ 'do_cache' ] = True
  return results

