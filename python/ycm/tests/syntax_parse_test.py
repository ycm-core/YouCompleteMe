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

from ycm.test_utils import MockVimModule
MockVimModule()

import os
from nose.tools import eq_
from hamcrest import assert_that, has_items
from ycm import syntax_parse


def ContentsOfTestFile( test_file ):
  dir_of_script = os.path.dirname( os.path.abspath( __file__ ) )
  full_path_to_test_file = os.path.join( dir_of_script, 'testdata', test_file )
  return open( full_path_to_test_file ).read()



def KeywordsFromSyntaxListOutput_PythonSyntax_test():
  eq_( set(['bytearray', 'IndexError', 'all', 'help', 'vars',
            'SyntaxError', 'global', 'elif', 'unicode', 'sorted', 'memoryview',
            'isinstance', 'except', 'nonlocal', 'NameError', 'finally',
            'BytesWarning', 'dict', 'IOError', 'pass', 'oct', 'match', 'bin',
            'SystemExit', 'return', 'StandardError', 'format', 'TabError',
            'break', 'next', 'not', 'UnicodeDecodeError', 'False',
            'RuntimeWarning', 'list', 'iter', 'try', 'reload', 'Warning',
            'round', 'dir', 'cmp', 'set', 'bytes', 'UnicodeTranslateError',
            'intern', 'issubclass', 'yield', 'Ellipsis', 'hash', 'locals',
            'BufferError', 'slice', 'for', 'FloatingPointError', 'sum',
            'VMSError', 'getattr', 'abs', 'print', 'import', 'True',
            'FutureWarning', 'ImportWarning', 'None', 'EOFError', 'len',
            'frozenset', 'ord', 'super', 'raise', 'TypeError',
            'KeyboardInterrupt', 'UserWarning', 'filter', 'range',
            'staticmethod', 'SystemError', 'or', 'BaseException', 'pow',
            'RuntimeError', 'float', 'MemoryError', 'StopIteration', 'globals',
            'divmod', 'enumerate', 'apply', 'LookupError', 'open', 'basestring',
            'from', 'UnicodeError', 'zip', 'hex', 'long', 'IndentationError',
            'int', 'chr', '__import__', 'type', 'Exception', 'continue',
            'tuple', 'reduce', 'reversed', 'else', 'assert',
            'UnicodeEncodeError', 'input', 'with', 'hasattr', 'delattr',
            'setattr', 'raw_input', 'PendingDeprecationWarning', 'compile',
            'ArithmeticError', 'while', 'del', 'str', 'property', 'def', 'and',
            'GeneratorExit', 'ImportError', 'xrange', 'is', 'EnvironmentError',
            'KeyError', 'coerce', 'SyntaxWarning', 'file', 'in', 'unichr',
            'ascii', 'any', 'as', 'if', 'OSError', 'DeprecationWarning', 'min',
            'UnicodeWarning', 'execfile', 'id', 'complex', 'bool', 'ValueError',
            'NotImplemented', 'map', 'exec', 'buffer', 'max', 'class', 'object',
            'repr', 'callable', 'ZeroDivisionError', 'eval', '__debug__',
            'ReferenceError', 'AssertionError', 'classmethod',
            'UnboundLocalError', 'NotImplementedError', 'lambda',
            'AttributeError', 'OverflowError', 'WindowsError'] ),
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
  eq_( set(['code', 'text', 'cols', 'datetime', 'disabled', 'shape', 'codetype',
           'alt', 'compact', 'style', 'valuetype', 'short', 'finally',
           'continue', 'extends', 'valign', 'match', 'bordercolor', 'do',
           'return', 'rel', 'rules', 'void', 'nohref', 'abbr', 'background',
           'scrolling', 'instanceof', 'name', 'summary', 'try', 'default',
           'noshade', 'coords', 'dir', 'frame', 'usemap', 'ismap', 'static',
           'hspace', 'vlink', 'for', 'selected', 'rev', 'vspace', 'content',
           'method', 'version', 'volatile', 'above', 'new', 'charoff', 'public',
           'alink', 'enum', 'codebase', 'if', 'noresize', 'interface',
           'checked', 'byte', 'super', 'throw', 'src', 'language', 'package',
           'standby', 'script', 'longdesc', 'maxlength', 'cellpadding',
           'throws', 'tabindex', 'color', 'colspan', 'accesskey', 'float',
           'while', 'private', 'height', 'boolean', 'wrap', 'prompt', 'nowrap',
           'size', 'rows', 'span', 'clip', 'bgcolor', 'top', 'long', 'start',
           'scope', 'scheme', 'type', 'final', 'lang', 'visibility', 'else',
           'assert', 'transient', 'link', 'catch', 'true', 'serializable',
           'target', 'lowsrc', 'this', 'double', 'align', 'value', 'cite',
           'headers', 'below', 'protected', 'declare', 'classid', 'defer',
           'false', 'synchronized', 'int', 'abstract', 'accept', 'hreflang',
           'char', 'border', 'id', 'native', 'rowspan', 'charset', 'archive',
           'strictfp', 'readonly', 'axis', 'cellspacing', 'profile', 'multiple',
           'object', 'action', 'pagex', 'pagey', 'marginheight', 'data',
           'class', 'frameborder', 'enctype', 'implements', 'break', 'gutter',
           'url', 'clear', 'face', 'switch', 'marginwidth', 'width', 'left']),
       syntax_parse._KeywordsFromSyntaxListOutput(
         ContentsOfTestFile( 'java_syntax' ) ) )


def KeywordsFromSyntaxListOutput_PhpSyntax_ContainsFunctions_test():
  assert_that( syntax_parse._KeywordsFromSyntaxListOutput(
                   ContentsOfTestFile( 'php_syntax' ) ),
               has_items( 'array_change_key_case' ) )


def KeywordsFromSyntaxListOutput_Basic_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
foogroup xxx foo bar
             zoo goo
             links to Statement"""
         )
     )


def KeywordsFromSyntaxListOutput_Function_test():
  eq_( set([ 'foo', 'bar', 'zoo', 'goo' ]),
       syntax_parse._KeywordsFromSyntaxListOutput( """
foogroup xxx foo bar
             zoo goo
             links to Function"""
         )
     )


def KeywordsFromSyntaxListOutput_ContainedArgAllowed_test():
  assert_that( syntax_parse._KeywordsFromSyntaxListOutput( """
phpFunctions   xxx contained gzclose yaz_syntax html_entity_decode fbsql_read_blob png2wbmp mssql_init cpdf_set_title gztell fbsql_insert_id empty cpdf_restore mysql_field_type closelog swftext ldap_search curl_errno gmp_div_r mssql_data_seek getmyinode printer_draw_pie mcve_initconn ncurses_getmaxyx defined
                   contained replace_child has_attributes specified insertdocument assign node_name hwstat addshape get_attribute_node html_dump_mem userlist
                   links to Function""" ),
              has_items( 'gzclose', 'userlist', 'ldap_search' ) )


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


def ExtractKeywordsFromGroup_ContainedSyntaxArgAllowed_test():
  eq_( ['foo', 'zoq', 'bar', 'goo', 'far' ],
       syntax_parse._ExtractKeywordsFromGroup( syntax_parse.SyntaxGroup('', [
         'contained foo zoq',
         'contained bar goo',
         'far',
       ] ) )
     )
