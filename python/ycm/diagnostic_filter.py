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
from ycm import vimsupport
import re


class DiagnosticFilter( object ):
  def __init__( self, config_or_filters ):
    if isinstance( config_or_filters, list ):
      self._filters = config_or_filters

    else:
      self._filters = _CompileFilters( config_or_filters )


  def IsAllowed( self, diagnostic ):
    # NOTE: a diagnostic IsAllowed() ONLY if NO filters match it
    for filterMatches in self._filters:
      if filterMatches( diagnostic ):
        return False

    return True


  def SubsetForTypes( self, filetypes ):
    """Return a sub-filter limited to the given filetypes"""
    # NOTE: actually, this class is already filtered
    return self


  @staticmethod
  def CreateFromOptions( user_options ):
    all_filters = dict( user_options.get( 'filter_diagnostics', {} ) )
    compiled_by_type = {}
    for type_spec, filter_value in iteritems( dict( all_filters ) ):
      filetypes = [ type_spec ]
      if type_spec.find( ',' ) != -1:
        filetypes = type_spec.split( ',' )
      for filetype in filetypes:
        compiled_by_type[ filetype ] = _CompileFilters( filter_value )

    return _MasterDiagnosticFilter( compiled_by_type )


class _MasterDiagnosticFilter( object ):

  def __init__( self, all_filters ):
    self._all_filters = all_filters
    self._cache = {}


  def IsAllowed( self, diagnostic ):
    # NOTE: in this class's implementation, we ask vimsupport for
    #  the current filetypes and delegate automatically; it is probably,
    #  more efficient, however, to call SubsetForTypes() and reuse
    #  the returned DiagnosticFilter if it will be checked repeatedly.
    filetypes = vimsupport.CurrentFiletypes()
    return self.SubsetForTypes( filetypes ).IsAllowed( diagnostic )


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

  if config_entry is None:
    return []

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

  for filter_type in iterkeys( config ):
    compiler = FILTER_COMPILERS.get( filter_type )

    if compiler is not None:
      for filter_config in _ListOf( config[ filter_type ] ):
        compiledFilter = compiler( filter_config )
        filters.append( compiledFilter )

  return filters
