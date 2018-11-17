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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from future.utils import iteritems
from ycm import vimsupport
from protoycmd import user_options_store
from protoycmd import identifier_utils

YCM_VAR_PREFIX = 'ycm_'


def BuildServerConf():
  """Builds a dictionary mapping YCM Vim user options to values. Option names
  don't have the 'ycm_' prefix."""
  # We only evaluate the keys of the vim globals and not the whole dictionary
  # to avoid unicode issues.
  # See https://github.com/Valloric/YouCompleteMe/pull/2151 for details.
  keys = vimsupport.GetVimGlobalsKeys()
  server_conf = {}
  for key in keys:
    if not key.startswith( YCM_VAR_PREFIX ):
      continue
    new_key = key[ len( YCM_VAR_PREFIX ): ]
    new_value = vimsupport.VimExpressionToPythonType( 'g:' + key )
    server_conf[ new_key ] = new_value

  return server_conf


def LoadJsonDefaultsIntoVim():
  defaults = user_options_store.DefaultOptions()
  for key, value in iteritems( defaults ):
    new_key = 'g:ycm_' + key
    if not vimsupport.VariableExists( new_key ):
      vimsupport.SetVariableValue( new_key, value )


def CurrentIdentifierFinished():
  line, current_column = vimsupport.CurrentLineContentsAndCodepointColumn()
  previous_char_index = current_column - 1
  if previous_char_index < 0:
    return True
  filetype = vimsupport.CurrentFiletypes()[ 0 ]
  regex = identifier_utils.IdentifierRegexForFiletype( filetype )

  for match in regex.finditer( line ):
    if match.end() == previous_char_index:
      return True
  # If the whole line is whitespace, that means the user probably finished an
  # identifier on the previous line.
  return line[ : current_column ].isspace()


def LastEnteredCharIsIdentifierChar():
  line, current_column = vimsupport.CurrentLineContentsAndCodepointColumn()
  if current_column - 1 < 0:
    return False
  filetype = vimsupport.CurrentFiletypes()[ 0 ]
  return (
    identifier_utils.StartOfLongestIdentifierEndingAtIndex(
        line, current_column, filetype ) != current_column )


def AdjustCandidateInsertionText( candidates ):
  """This function adjusts the candidate insertion text to take into account the
  text that's currently in front of the cursor.

  For instance ('|' represents the cursor):
    1. Buffer state: 'foo.|bar'
    2. A completion candidate of 'zoobar' is shown and the user selects it.
    3. Buffer state: 'foo.zoobar|bar' instead of 'foo.zoo|bar' which is what the
    user wanted.

  This function changes candidates to resolve that issue.

  It could be argued that the user actually wants the final buffer state to be
  'foo.zoobar|' (the cursor at the end), but that would be much more difficult
  to implement and is probably not worth doing.
  """

  def NewCandidateInsertionText( to_insert, text_after_cursor ):
    overlap_len = OverlapLength( to_insert, text_after_cursor )
    if overlap_len:
      return to_insert[ :-overlap_len ]
    return to_insert

  text_after_cursor = vimsupport.TextAfterCursor()
  if not text_after_cursor:
    return candidates

  new_candidates = []
  for candidate in candidates:
    new_candidate = candidate.copy()

    if 'abbr' not in new_candidate:
      new_candidate[ 'abbr' ] = new_candidate[ 'word' ]

    new_candidate[ 'word' ] = NewCandidateInsertionText(
      new_candidate[ 'word' ],
      text_after_cursor )

    new_candidates.append( new_candidate )
  return new_candidates


def OverlapLength( left_string, right_string ):
  """Returns the length of the overlap between two strings.
  Example: "foo baro" and "baro zoo" -> 4
  """
  left_string_length = len( left_string )
  right_string_length = len( right_string )

  if not left_string_length or not right_string_length:
    return 0

  # Truncate the longer string.
  if left_string_length > right_string_length:
    left_string = left_string[ -right_string_length: ]
  elif left_string_length < right_string_length:
    right_string = right_string[ :left_string_length ]

  if left_string == right_string:
    return min( left_string_length, right_string_length )

  # Start by looking for a single character match
  # and increase length until no match is found.
  best = 0
  length = 1
  while True:
    pattern = left_string[ -length: ]
    found = right_string.find( pattern )
    if found < 0:
      return best
    length += found
    if left_string[ -length: ] == right_string[ :length ]:
      best = length
      length += 1
