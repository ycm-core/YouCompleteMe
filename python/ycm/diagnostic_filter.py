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

from future.utils import iterkeys, iteritems
import re


class DiagnosticFilter( object ):
  def __init__( self, config ):
    self._filters = []

    for filter_type in iterkeys( config ):
      actual_filter_type = filter_type
      compiler = FILTER_COMPILERS.get( filter_type )

      if compiler is not None:
        for filter_config in _ListOf( config[ actual_filter_type ] ):
          fn = compiler( filter_config )
          self._filters.append( fn )


  def IsAllowed( self, diagnostic ):
    # NOTE: a diagnostic IsAllowed() ONLY if
    #  NO filters match it
    for f in self._filters:
      if f( diagnostic ):
        return False

    return True


  @staticmethod
  def from_filetype( user_options, filetypes ):
    spec = {}
    all_filters = dict( user_options.get( 'filter_diagnostics', {} ) )
    for typeSpec, filterValue in iteritems( dict( all_filters ) ):
      if typeSpec.find(',') != -1:
        for ft in typeSpec.split(','):
          all_filters[ ft ] = filterValue

    for filetype in filetypes:
      type_specific = all_filters.get( filetype, {} )
      spec = _Merge( spec, type_specific )
    return DiagnosticFilter( spec )


def _ListOf( config_entry ):
  if isinstance( config_entry, list ):
    return config_entry

  if config_entry is None:
    return []

  return [ config_entry ]


def _Merge( into, other ):
  for k in iterkeys( other ):
    into[k] = _ListOf( into.get( k ) ) + _ListOf( other[ k ] )

  return into


def _CompileRegex( raw_regex ):
  pattern = re.compile( raw_regex, re.IGNORECASE )

  def FilterRegex( diagnostic ):
    return pattern.search( diagnostic[ 'text' ] ) is not None

  return FilterRegex


def _CompileLevel( level ):
  # valid kinds are WARNING and ERROR;
  #  expected input levels are `warning` and `error`
  # NB: we don't validate the input...
  expected_kind = level.upper()

  def FilterLevel( diagnostic ):
    return diagnostic[ 'kind' ] == expected_kind

  return FilterLevel


FILTER_COMPILERS = { 'regex' : _CompileRegex,
                     'level' : _CompileLevel }
