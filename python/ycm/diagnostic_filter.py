# Copyright (C) 2016  YouCompleteMe contributors
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

from future.utils import iterkeys
import re


class DiagnosticFilter( object ):
  def __init__( self, config ):
    self._filters = []

    for filter_type in iterkeys( config ):
      wrapper = _AsIs
      actual_filter_type = filter_type

      if filter_type[ 0 ] == '!':
        wrapper = _Not
        filter_type = filter_type[ 1 : ]
      compiler = FILTER_COMPILERS.get( filter_type )

      if compiler is not None:
        for filter_config in _ListOf( config[ actual_filter_type ] ):
          fn = wrapper( compiler( filter_config ) )
          self._filters.append( fn )


  def IsAllowed( self, diagnostic ):
    # NOTE: a diagnostic IsAllowed() ONLY if
    #  no filters match it
    for f in self._filters:
      if f( diagnostic ):
        return False

    return True


  @staticmethod
  def from_filetype( user_options, filetypes ):
    base = dict( user_options.get( 'quiet_messages', {} ) )

    for filetype in filetypes:
      type_specific = user_options.get( filetype + '_quiet_messages', {} )
      base.update( type_specific )
    return DiagnosticFilter( base )


def _ListOf( config_entry ):
  if isinstance( config_entry, list ):
    return config_entry

  return [ config_entry ]


def _AsIs( fn ):
  return fn


def _Not( fn ):
  def Inverted( diagnostic ):
    return not fn( diagnostic )

  return Inverted


def _CompileRegex( raw_regex ):
  pattern = re.compile( raw_regex, re.IGNORECASE )

  def FilterRegex( diagnostic ):
    return pattern.search( diagnostic[ 'text' ] ) is not None

  return FilterRegex


def _CompileLevel( level ):
  # valid kinds are WARNING and ERROR;
  #  expected input levels are `warnings` and `errors`
  # NB: we don't validate the input...
  expected_kind = level.upper()[ : -1 ]

  def FilterLevel( diagnostic ):
    return diagnostic[ 'kind' ] == expected_kind

  return FilterLevel


FILTER_COMPILERS  = { 'regex' : _CompileRegex,
                      'level' : _CompileLevel }
