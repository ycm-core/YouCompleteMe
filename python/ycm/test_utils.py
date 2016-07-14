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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from mock import MagicMock
from hamcrest import assert_that, equal_to
import re
import sys
import nose
import functools

from ycmd.utils import ToUnicode


BUFNR_REGEX = re.compile( r"^bufnr\('(.+)', ([0-9]+)\)$" )
BUFWINNR_REGEX = re.compile( r"^bufwinnr\(([0-9]+)\)$" )
BWIPEOUT_REGEX = re.compile( r"^(?:silent! )bwipeout!? ([0-9]+)$" )

# One-and only instance of mocked Vim object. The first 'import vim' that is
# executed binds the vim module to the instance of MagicMock that is created,
# and subsquent assignments to sys.modules[ 'vim' ] don't retrospectively
# update them. The result is that while running the tests, we must assign only
# one instance of MagicMock to sys.modules[ 'vim' ] and always return it.
#
# More explanation is available:
# https://github.com/Valloric/YouCompleteMe/pull/1694
VIM_MOCK = MagicMock()


def MockGetBufferNumber( buffer_filename ):
  for buffer in VIM_MOCK.buffers:
    if buffer[ 'filename' ] == buffer_filename:
      return buffer[ 'number' ]
  return -1


def MockGetBufferWindowNumber( buffer_number ):
  for buffer in VIM_MOCK.buffers:
    if buffer[ 'number' ] == buffer_number and 'window' in buffer:
      return buffer[ 'window' ]
  return -1


def MockVimEval( value ):
  if value == "g:ycm_min_num_of_chars_for_completion":
    return 0
  if value == "g:ycm_server_python_interpreter":
    return ''
  if value == "tempname()":
    return '_TEMP_FILE_'
  if value == "&previewheight":
    # Default value from Vim
    return 12

  match = BUFNR_REGEX.search( value )
  if match:
    return MockGetBufferNumber( match.group( 1 ) )

  match = BUFWINNR_REGEX.search( value )
  if match:
    return MockGetBufferWindowNumber( int( match.group( 1 ) ) )

  raise ValueError( 'Unexpected evaluation: ' + value )


def MockWipeoutBuffer( buffer_number ):
  buffers = VIM_MOCK.buffers

  for index, buffer in enumerate( buffers ):
    if buffer[ 'number' ] == buffer_number:
      return buffers.pop( index )


def MockVimCommand( command ):
  match = BWIPEOUT_REGEX.search( command )
  if match:
    return MockWipeoutBuffer( int( match.group( 1 ) ) )

  raise RuntimeError( 'Unexpected command: ' + command )


def MockVimModule():
  """The 'vim' module is something that is only present when running inside the
  Vim Python interpreter, so we replace it with a MagicMock for tests. If you
  need to add additional mocks to vim module functions, then use 'patch' from
  mock module, to ensure that the state of the vim mock is returned before the
  next test. That is:

    from ycm.test_utils import MockVimModule
    from mock import patch

    # Do this once
    MockVimModule()

    @patch( 'vim.eval', return_value='test' )
    @patch( 'vim.command', side_effect=ValueError )
    def test( vim_command, vim_eval ):
      # use vim.command via vim_command, e.g.:
      vim_command.assert_has_calls( ... )

  Failure to use this approach may lead to unexpected failures in other
  tests."""

  VIM_MOCK.buffers = {}
  VIM_MOCK.eval = MagicMock( side_effect = MockVimEval )
  sys.modules[ 'vim' ] = VIM_MOCK

  return VIM_MOCK


class ExtendedMock( MagicMock ):
  """An extension to the MagicMock class which adds the ability to check that a
  callable is called with a precise set of calls in a precise order.

  Example Usage:
    from ycm.test_utils import ExtendedMock
    @patch( 'test.testing', new_callable = ExtendedMock, ... )
    def my_test( test_testing ):
      ...
  """

  def assert_has_exact_calls( self, calls, any_order = False ):
    self.assert_has_calls( calls, any_order )
    assert_that( self.call_count, equal_to( len( calls ) ) )


def ExpectedFailure( reason, *exception_matchers ):
  """Defines a decorator to be attached to tests. This decorator
  marks the test as being known to fail, e.g. where documenting or exercising
  known incorrect behaviour.

  The parameters are:
    - |reason| a textual description of the reason for the known issue. This
               is used for the skip reason
    - |exception_matchers| additional arguments are hamcrest matchers to apply
                 to the exception thrown. If the matchers don't match, then the
                 test is marked as error, with the original exception.

  If the test fails (for the correct reason), then it is marked as skipped.
  If it fails for any other reason, it is marked as failed.
  If the test passes, then it is also marked as failed."""
  def decorator( test ):
    @functools.wraps( test )
    def Wrapper( *args, **kwargs ):
      try:
        test( *args, **kwargs )
      except Exception as test_exception:
        # Ensure that we failed for the right reason
        test_exception_message = ToUnicode( test_exception )
        try:
          for matcher in exception_matchers:
            assert_that( test_exception_message, matcher )
        except AssertionError:
          # Failed for the wrong reason!
          import traceback
          print( 'Test failed for the wrong reason: ' + traceback.format_exc() )
          # Real failure reason is the *original* exception, we're only trapping
          # and ignoring the exception that is expected.
          raise test_exception

        # Failed for the right reason
        raise nose.SkipTest( reason )
      else:
        raise AssertionError( 'Test was expected to fail: {0}'.format(
          reason ) )
    return Wrapper

  return decorator
