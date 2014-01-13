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
from copy import deepcopy
import os

DEFAULT_FILETYPE_TRIGGERS = {
  'c' : ['->', '.'],
  'objc' : ['->', '.'],
  'ocaml' : ['.', '#'],
  'cpp,objcpp' : ['->', '.', '::'],
  'perl' : ['->'],
  'php' : ['->', '::'],
  'cs,java,javascript,d,vim,python,perl6,scala,vb,elixir,go' : ['.'],
  'ruby' : ['.', '::'],
  'lua' : ['.', ':'],
  'erlang' : [':'],
}


def _FiletypeTriggerDictFromSpec( trigger_dict_spec ):
  triggers_for_filetype = defaultdict( set )

  for key, value in trigger_dict_spec.iteritems():
    filetypes = key.split( ',' )
    for filetype in filetypes:
      triggers_for_filetype[ filetype ].update( value )

  return triggers_for_filetype


def _FiletypeDictUnion( dict_one, dict_two ):
  """Returns a new filetye dict that's a union of the provided two dicts.
  Dict params are supposed to be type defaultdict(set)."""

  final_dict = deepcopy( dict_one )

  for key, value in dict_two.iteritems():
    final_dict[ key ].update( value )

  return final_dict


def TriggersForFiletype( user_triggers ):
  default_triggers = _FiletypeTriggerDictFromSpec(
    DEFAULT_FILETYPE_TRIGGERS )

  return _FiletypeDictUnion( default_triggers, dict( user_triggers ) )


def _PathToCompletersFolder():
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script )


def PathToFiletypeCompleterPluginLoader( filetype ):
  return os.path.join( _PathToCompletersFolder(), filetype, 'hook.py' )


def FiletypeCompleterExistsForFiletype( filetype ):
  return os.path.exists( PathToFiletypeCompleterPluginLoader( filetype ) )
