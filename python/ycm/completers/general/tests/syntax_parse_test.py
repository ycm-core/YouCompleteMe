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

import os
from nose.tools import eq_
from ycm.test_utils import MockVimModule
vim_mock = MockVimModule()
from ycm.completers.general import syntax_parse


def ContentsOfTestFile( test_file ):
  dir_of_script = os.path.dirname( os.path.abspath( __file__ ) )
  full_path_to_test_file = os.path.join( dir_of_script, 'testdata', test_file )
  return open( full_path_to_test_file ).read()



def KeywordsFromSyntaxListOutput_PythonSyntax_test():
  eq_( set(['and', 'IndexError', 'elif', 'BytesWarning', 'ZeroDivisionError',
            'ImportError', 'is', 'global', 'UnicodeTranslateError',
            'GeneratorExit', 'BufferError', 'StopIteration', 'as',
            'SystemError', 'UnicodeError', 'EnvironmentError', 'in', 'EOFError',
            'LookupError', 'Exception', 'PendingDeprecationWarning', 'if',
            'OSError', 'DeprecationWarning', 'raise', 'for',
            'FloatingPointError', 'UnicodeWarning', 'VMSError', 'except',
            'nonlocal', 'ReferenceError', 'NameError', 'pass', 'finally',
            'Warning', 'UnboundLocalError', 'print', 'IOError',
            'IndentationError', 'True', 'RuntimeError', 'FutureWarning',
            'ImportWarning', 'SystemExit', 'None', 'return', 'StandardError',
            'exec', 'ValueError', 'TabError', 'else', 'break', 'SyntaxError',
            'UnicodeEncodeError', 'WindowsError', 'not', 'UnicodeDecodeError',
            'with', 'class', 'KeyError', 'AssertionError', 'assert',
            'TypeError', 'False', 'RuntimeWarning', 'KeyboardInterrupt',
            'UserWarning', 'SyntaxWarning', 'yield', 'OverflowError', 'try',
            'ArithmeticError', 'while', 'continue', 'del', 'MemoryError',
            'NotImplementedError', 'BaseException', 'AttributeError', 'or',
            'def', 'lambda', 'from', 'import']),
       syntax_parse._KeywordsFromSyntaxListOutput(
         ContentsOfTestFile( 'python_syntax' ) ) )


def KeywordsFromSyntaxListOutput_CppSyntax_test():
  eq_( set(['int_fast32_t', 'FILE', 'size_t', 'bitor', 'typedef', 'const',
            'struct', 'uint8_t', 'fpos_t', 'thread_local', 'unsigned',
            'uint_least16_t', 'match', 'do', 'intptr_t', 'uint_least64_t',
            'return', 'auto', 'void', '_Complex', 'break', '_Alignof', 'not',
            'using', '_Static_assert', '_Thread_local', 'public',
            'uint_fast16_t', 'this', 'continue', 'char32_t', 'int16_t',
            'intmax_t', 'static', 'clock_t', 'sizeof', 'int_fast64_t',
            'mbstate_t', 'try', 'xor', 'uint_fast32_t', 'int_least8_t', 'div_t',
            'volatile', 'template', 'char16_t', 'new', 'ldiv_t',
            'int_least16_t', 'va_list', 'uint_least8_t', 'goto', 'noreturn',
            'enum', 'static_assert', 'bitand', 'compl', 'imaginary', 'jmp_buf',
            'throw', 'asm', 'ptrdiff_t', 'uint16_t', 'or', 'uint_fast8_t',
            '_Bool', 'int32_t', 'float', 'private', 'restrict', 'wint_t',
            'operator', 'not_eq', '_Imaginary', 'alignas', 'union', 'long',
            'uint_least32_t', 'int_least64_t', 'friend', 'uintptr_t', 'int8_t',
            'else', 'export', 'int_fast8_t', 'catch', 'true', 'case', 'default',
            'double', '_Noreturn', 'signed', 'typename', 'while', 'protected',
            'wchar_t', 'wctrans_t', 'uint64_t', 'delete', 'and', 'register',
            'false', 'int', 'uintmax_t', 'off_t', 'char', 'int64_t',
            'int_fast16_t', 'DIR', '_Atomic', 'time_t', 'xor_eq', 'namespace',
            'virtual', 'complex', 'bool', 'mutable', 'if', 'int_least32_t',
            'sig_atomic_t', 'and_eq', 'ssize_t', 'alignof', '_Alignas',
            '_Generic', 'extern', 'class', 'typeid', 'short', 'for',
            'uint_fast64_t', 'wctype_t', 'explicit', 'or_eq', 'switch',
            'uint32_t', 'inline']),
       syntax_parse._KeywordsFromSyntaxListOutput(
         ContentsOfTestFile( 'cpp_syntax' ) ) )


def KeywordsFromSyntaxListOutput_JavaSyntax_test():
  eq_( set(['false', 'synchronized', 'int', 'abstract', 'float', 'private',
            'char', 'catch', 'boolean', 'static', 'native', 'for', 'super',
            'while', 'long', 'throw', 'strictfp', 'finally', 'continue',
            'extends', 'volatile', 'if', 'public', 'match', 'do', 'return',
            'void', 'enum', 'else', 'break', 'transient', 'new', 'interface',
            'instanceof', 'byte', 'true', 'serializable', 'implements',
            'assert', 'short', 'package', 'this', 'double', 'final', 'try',
            'default', 'switch', 'protected', 'throws']),
       syntax_parse._KeywordsFromSyntaxListOutput(
         ContentsOfTestFile( 'java_syntax' ) ) )


def KeywordsFromSyntaxListOutput_Basic_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
foogroup xxx foo bar
             zoo goo
             links to Statement"""
         )
     )


def KeywordsFromSyntaxListOutput_JunkIgnored_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
--- Syntax items ---
foogroup xxx foo bar
             zoo goo
             links to Statement
Spell          cluster=NONE
NoSpell        cluster=NONE"""
         )
     )


def KeywordsFromSyntaxListOutput_MultipleStatementGroups_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
foogroup xxx foo bar
             links to Statement
bargroup xxx zoo goo
             links to Statement"""
         )
     )


def KeywordsFromSyntaxListOutput_StatementAndTypeGroups_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
foogroup xxx foo bar
             links to Statement
bargroup xxx zoo goo
             links to Type"""
         )
     )


def KeywordsFromSyntaxListOutput_StatementHierarchy_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo', 'qux', 'moo' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
baa xxx foo bar
        links to Foo
Foo xxx zoo goo
        links to Bar
Bar xxx qux moo
        links to Statement"""
         )
     )


def KeywordsFromSyntaxListOutput_TypeHierarchy_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo', 'qux', 'moo' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
baa xxx foo bar
        links to Foo
Foo xxx zoo goo
        links to Bar
Bar xxx qux moo
        links to Type"""
         )
     )


def KeywordsFromSyntaxListOutput_StatementAndTypeHierarchy_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo', 'qux', 'moo', 'na', 'nb', 'nc' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
tBaa xxx foo bar
        links to tFoo
tFoo xxx zoo goo
        links to tBar
tBar xxx qux moo
        links to Type
sBaa xxx na bar
        links to sFoo
sFoo xxx zoo nb
        links to sBar
sBar xxx qux nc
        links to Statement"""
         )
     )


def SyntaxGroupsFromOutput_Basic_test():
  groups = syntax_parse._SyntaxGroupsFromOutput(
        """foogroup xxx foo bar
                        zoo goo
                        links to Statement""" )

  assert 'foogroup' in groups


def ExtractKeywordsFromGroup_Basic_test():
  eq_( ['foo', 'bar', 'zoo', 'goo' ],
       syntax_parse._ExtractKeywordsFromGroup( syntax_parse.SyntaxGroup('', [
         'foo bar',
         'zoo goo',
       ] ) )
     )


def ExtractKeywordsFromGroup_Commas_test():
  eq_( ['foo', 'bar', 'zoo', 'goo' ],
       syntax_parse._ExtractKeywordsFromGroup( syntax_parse.SyntaxGroup('', [
         'foo, bar,',
         'zoo goo',
       ] ) )
     )


def ExtractKeywordsFromGroup_WithLinksTo_test():
  eq_( ['foo', 'bar', 'zoo', 'goo' ],
       syntax_parse._ExtractKeywordsFromGroup( syntax_parse.SyntaxGroup('', [
         'foo bar',
         'zoo goo',
         'links to Statement'
       ] ) )
     )


def ExtractKeywordsFromGroup_KeywordStarts_test():
  eq_( ['foo', 'bar', 'zoo', 'goo' ],
       syntax_parse._ExtractKeywordsFromGroup( syntax_parse.SyntaxGroup('', [
         'foo bar',
         'transparent boo baa',
         'zoo goo',
       ] ) )
     )


def ExtractKeywordsFromGroup_KeywordMiddle_test():
  eq_( ['foo', 'bar', 'zoo', 'goo' ],
       syntax_parse._ExtractKeywordsFromGroup( syntax_parse.SyntaxGroup('', [
         'foo oneline bar',
         'zoo goo',
       ] ) )
     )


def ExtractKeywordsFromGroup_KeywordAssign_test():
  eq_( ['foo', 'bar', 'zoo', 'goo' ],
       syntax_parse._ExtractKeywordsFromGroup( syntax_parse.SyntaxGroup('', [
         'foo end=zoo((^^//)) bar',
         'zoo goo',
       ] ) )
     )


def ExtractKeywordsFromGroup_KeywordAssignAndMiddle_test():
  eq_( ['foo', 'bar', 'zoo', 'goo' ],
       syntax_parse._ExtractKeywordsFromGroup( syntax_parse.SyntaxGroup('', [
         'foo end=zoo((^^//)) transparent bar',
         'zoo goo',
       ] ) )
     )
