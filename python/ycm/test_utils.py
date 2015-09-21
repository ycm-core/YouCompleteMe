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

from mock import MagicMock
import sys

# One-and only instance of mocked Vim object. The first 'import vim' that is
# executed binds the vim module to the instance of MagicMock that is created,
# and subsquent assignments to sys.modules[ 'vim' ] don't retrospectively update
# them. The result is that while running the tests, we must assign only one
# instance of MagicMock to sys.modules[ 'vim' ] and always return it.
#
# More explanation is available:
# https://github.com/Valloric/YouCompleteMe/pull/1694
VIM_MOCK = MagicMock()

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

  def VimEval( value ):
    if value == "g:ycm_min_num_of_chars_for_completion":
      return 0
    return ''

  VIM_MOCK.eval = MagicMock( side_effect = VimEval )
  sys.modules[ 'vim' ] = VIM_MOCK

  return VIM_MOCK
