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

from collections import defaultdict
from nose.tools import eq_
from ycm.test_utils import MockVimModule
vim_mock = MockVimModule()
from ycm.completers import completer_utils


def FiletypeTriggerDictFromSpec_Works_test():
  eq_( defaultdict( set, {
         'foo': set(['zoo', 'bar']),
         'goo': set(['moo']),
         'moo': set(['moo']),
         'qux': set(['q'])
       } ),
       completer_utils._FiletypeTriggerDictFromSpec( {
         'foo': ['zoo', 'bar'],
         'goo,moo': ['moo'],
         'qux': ['q']
       } ) )


def FiletypeDictUnion_Works_test():
  eq_( defaultdict( set, {
         'foo': set(['zoo', 'bar', 'maa']),
         'goo': set(['moo']),
         'bla': set(['boo']),
         'qux': set(['q'])
       } ),
       completer_utils._FiletypeDictUnion( defaultdict( set, {
         'foo': set(['zoo', 'bar']),
         'goo': set(['moo']),
         'qux': set(['q'])
       } ), defaultdict( set, {
         'foo': set(['maa']),
         'bla': set(['boo']),
         'qux': set(['q'])
       } ) ) )


