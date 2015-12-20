#!/usr/bin/env python
#
# Copyright (C) 2015 YouCompleteMe contributors
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

import vimrunner
from os import path
from ycmd.utils import OnMac
from unittest import TestCase
from hamcrest import assert_that
from hamcrest.core.core.isequal import equal_to

DIR_OF_YCM = path.abspath( path.join( path.dirname( path.abspath( __file__ ) ),
                                      '..', '..', '..', '..' ) )


class OmnifuncTest( TestCase ):

  def omnifunc_is_set_as_soon_as_we_enter_insert_mode_test( self ):
    vim = self.prepare_editor()
    vim.edit( 'python/ycm/base.py' )
    vim.normal( 'i' )
    assert_that( vim.eval( '&omnifunc' ), equal_to( 'youcompleteme#OmniComplete' ) )


  def omnifunc_is_set_after_re_edit_file_test( self ):
    vim = self.prepare_editor()
    vim.edit( 'python/ycm/base.py' )
    vim.command( 'autocmd FileType python :setlocal omnifunc=noycm' )
    vim.normal( 'i' )
    vim.feedkeys( '\<Esc>' )
    vim.command( 'e!' )
    assert_that( vim.eval( '&omnifunc' ), equal_to( 'youcompleteme#OmniComplete' ) )


  def prepare_editor( self ):
    self.vim = self._get_proper_editor()
    self.vim.prepend_runtimepath( DIR_OF_YCM )
    self.vim.command( 'runtime! plugin/youcompleteme.vim' )
    self.vim.command( 'call youcompleteme#Enable()' )
    return self.vim


  def _get_proper_editor( self ):
    if OnMac():
      return self.server.start_gvim()
    else:
      return self.server.start_in_other_terminal()


  def setUp( self ):
    self.server = vimrunner.Server()


  def tearDown( self ):
    self.vim.feedkeys( '\<Esc>' )
    self.vim.quit()
    self.server.kill()
