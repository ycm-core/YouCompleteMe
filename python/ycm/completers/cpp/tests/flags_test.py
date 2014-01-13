#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Google Inc.
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

from nose.tools import eq_
from .. import flags


def SanitizeFlags_Passthrough_test():
  eq_( [ '-foo', '-bar' ],
       list( flags._SanitizeFlags( [ '-foo', '-bar' ] ) ) )


def SanitizeFlags_ArchRemoved_test():
  expected = [ '-foo', '-bar' ]
  to_remove = [ '-arch', 'arch_of_evil' ]

  eq_( expected,
       list( flags._SanitizeFlags( expected + to_remove ) ) )

  eq_( expected,
       list( flags._SanitizeFlags( to_remove + expected ) ) )

  eq_( expected,
       list( flags._SanitizeFlags(
         expected[ :1 ] + to_remove + expected[ -1: ] ) ) )


def RemoveUnusedFlags_Passthrough_test():
  eq_( [ '-foo', '-bar' ],
       flags._RemoveUnusedFlags( [ '-foo', '-bar' ], 'file' ) )


def RemoveUnusedFlags_RemoveCompilerPathIfFirst_test():
  def tester( path ):
    eq_( expected,
        flags._RemoveUnusedFlags( [ path ] + expected, filename ) )

  compiler_paths = [ 'c++', 'c', 'gcc', 'g++', 'clang', 'clang++',
                     '/usr/bin/c++', '/some/other/path', 'some_command' ]
  expected = [ '-foo', '-bar' ]
  filename = 'file'

  for compiler in compiler_paths:
    yield tester, compiler


def RemoveUnusedFlags_RemoveDashC_test():
  expected = [ '-foo', '-bar' ]
  to_remove = [ '-c' ]
  filename = 'file'

  eq_( expected,
       flags._RemoveUnusedFlags( expected + to_remove, filename ) )

  eq_( expected,
       flags._RemoveUnusedFlags( to_remove + expected, filename ) )

  eq_( expected,
       flags._RemoveUnusedFlags(
         expected[ :1 ] + to_remove + expected[ -1: ], filename ) )


def RemoveUnusedFlags_RemoveDashO_test():
  expected = [ '-foo', '-bar' ]
  to_remove = [ '-o', 'output_name' ]
  filename = 'file'

  eq_( expected,
       flags._RemoveUnusedFlags( expected + to_remove, filename ) )

  eq_( expected,
       flags._RemoveUnusedFlags( to_remove + expected, filename ) )

  eq_( expected,
       flags._RemoveUnusedFlags(
         expected[ :1 ] + to_remove + expected[ -1: ], filename ) )


def RemoveUnusedFlags_RemoveFilename_test():
  expected = [ '-foo', '-bar' ]
  to_remove = [ 'file' ]
  filename = 'file'

  eq_( expected,
       flags._RemoveUnusedFlags( expected + to_remove, filename ) )

  eq_( expected,
       flags._RemoveUnusedFlags( to_remove + expected, filename ) )

  eq_( expected,
       flags._RemoveUnusedFlags(
         expected[ :1 ] + to_remove + expected[ -1: ], filename ) )


def RemoveUnusedFlags_RemoveFlagWithoutPrecedingDashFlag_test():
  expected = [ '-foo', '-x', 'c++', '-bar', 'include_dir' ]
  to_remove = [ 'unrelated_file' ]
  filename = 'file'

  eq_( expected,
       flags._RemoveUnusedFlags( expected + to_remove, filename ) )

  eq_( expected,
       flags._RemoveUnusedFlags( to_remove + expected, filename ) )


def RemoveUnusedFlags_RemoveFilenameWithoutPrecedingInclude_test():
  expected = [ '-I', '/foo/bar', '-isystem/zoo/goo' ]
  to_remove = [ '/moo/boo' ]
  filename = 'file'

  eq_( expected,
       flags._RemoveUnusedFlags( expected + to_remove, filename ) )

  eq_( expected,
       flags._RemoveUnusedFlags( to_remove + expected, filename ) )

  eq_( expected + expected,
       flags._RemoveUnusedFlags( expected + to_remove + expected, filename ) )

