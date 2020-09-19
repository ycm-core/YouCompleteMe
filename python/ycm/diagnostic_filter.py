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

import re


class DiagnosticFilter:
  def __init__( self, config_or_filters ):
    self._filters : list = config_or_filters


  def IsAllowed( self, diagnostic ):
    return not any( filterMatches( diagnostic )
                    for filterMatches in self._filters )


  @staticmethod
  def CreateFromOptions( user_options ):
    all_filters = user_options[ 'filter_diagnostics' ]
    compiled_by_type = {}
    for type_spec, filter_value in all_filters.items():
      filetypes = type_spec.split( ',' )
      for filetype in filetypes:
        compiled_by_type[ filetype ] = _CompileFilters( filter_value )

    return _MasterDiagnosticFilter( compiled_by_type )


class _MasterDiagnosticFilter:

  def __init__( self, all_filters ):
    self._all_filters = all_filters
    self._cache = {}


  def SubsetForTypes( self, filetypes ):
    # check cache
    cache_key = ','.join( filetypes )
    cached = self._cache.get( cache_key )
    if cached is not None:
      return cached

    # build a new DiagnosticFilter merging all filters
    #  for the provided filetypes
    spec = []
    for filetype in filetypes:
      type_specific = self._all_filters.get( filetype, [] )
      spec.extend( type_specific )

    new_filter = DiagnosticFilter( spec )
    self._cache[ cache_key ] = new_filter
    return new_filter


def _ListOf( config_entry ):
  if isinstance( config_entry, list ):
    return config_entry

  return [ config_entry ]


def CompileRegex( raw_regex ):
  pattern = re.compile( raw_regex, re.IGNORECASE )

  def FilterRegex( diagnostic ):
    return pattern.search( diagnostic[ 'text' ] ) is not None

  return FilterRegex


def CompileLevel( level ):
  # valid kinds are WARNING and ERROR;
  #  expected input levels are `warning` and `error`
  # NOTE: we don't validate the input...
  expected_kind = level.upper()

  def FilterLevel( diagnostic ):
    return diagnostic[ 'kind' ] == expected_kind

  return FilterLevel


FILTER_COMPILERS = { 'regex' : CompileRegex,
                     'level' : CompileLevel }


def _CompileFilters( config ):
  """Given a filter config dictionary, return a list of compiled filters"""
  filters = []

  for filter_type, filter_pattern in config.items():
    compiler = FILTER_COMPILERS.get( filter_type )

    if compiler is not None:
      for filter_config in _ListOf( filter_pattern ):
        compiledFilter = compiler( filter_config )
        filters.append( compiledFilter )

  return filters
