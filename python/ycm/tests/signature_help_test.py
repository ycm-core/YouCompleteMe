# Copyright (C) 2019 YouCompleteMe contributors
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

from hamcrest import ( assert_that,
                       empty )
from ycm import signature_help as sh


def MakeSignatureHelpBuffer_Empty_test():
  assert_that( sh._MakeSignatureHelpBuffer( {} ), empty() )
  assert_that( sh._MakeSignatureHelpBuffer( {
    'activeSignature': 0,
    'activeParameter': 0,
    'signatures': []
  } ), empty() )
  assert_that( sh._MakeSignatureHelpBuffer( {
    'activeSignature': 0,
    'activeParameter': 0,
  } ), empty() )
  assert_that( sh._MakeSignatureHelpBuffer( {
    'signatures': []
  } ), empty() )
