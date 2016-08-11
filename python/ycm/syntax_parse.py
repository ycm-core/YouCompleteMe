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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from future.utils import itervalues
import re
import vim
from ycm import vimsupport

SYNTAX_GROUP_REGEX = re.compile(
  r"""^
      (?P<group_name>\w+)
      \s+
      xxx
      \s+
      (?P<content>.+?)
      $""",
  re.VERBOSE )

KEYWORD_REGEX = re.compile( r'^(\w+),?$' )

SYNTAX_ARGUMENT_REGEX = re.compile(
  r"^\w+=.*$" )

SYNTAX_REGION_ARGUMENT_REGEX = re.compile(
  r"^(?:matchgroup|start)=.*$")

# See ":h syn-nextgroup".
SYNTAX_NEXTGROUP_ARGUMENTS = set([
  'skipwhite',
  'skipnl',
  'skipempty'
])

# These are the parent groups from which we want to extract keywords.
ROOT_GROUPS = set([
  'Boolean',
  'Identifier',
  'Statement',
  'PreProc',
  'Type'
])


class SyntaxGroup( object ):
  def __init__( self, name, lines = None ):
    self.name     = name
    self.lines    = lines if lines else []
    self.children = []


def SyntaxKeywordsForCurrentBuffer():
  vim.command( 'redir => b:ycm_syntax' )
  vim.command( 'silent! syntax list' )
  vim.command( 'redir END' )
  syntax_output = vimsupport.VimExpressionToPythonType( 'b:ycm_syntax' )
  return _KeywordsFromSyntaxListOutput( syntax_output )


def _KeywordsFromSyntaxListOutput( syntax_output ):
  group_name_to_group = _SyntaxGroupsFromOutput( syntax_output )
  _ConnectGroupChildren( group_name_to_group )

  groups_with_keywords = []
  for root_group in ROOT_GROUPS:
    groups_with_keywords.extend(
      _GetAllDescendentats( group_name_to_group[ root_group ] ) )

  keywords = []
  for group in groups_with_keywords:
    keywords.extend( _ExtractKeywordsFromGroup( group ) )
  return set( keywords )


def _SyntaxGroupsFromOutput( syntax_output ):
  group_name_to_group = _CreateInitialGroupMap()
  lines               = syntax_output.split( '\n' )
  looking_for_group   = True

  current_group = None
  for line in lines:
    if not line:
      continue

    match = SYNTAX_GROUP_REGEX.search( line )
    if match:
      if looking_for_group:
        looking_for_group = False
      else:
        group_name_to_group[ current_group.name ] = current_group

      current_group = SyntaxGroup( match.group( 'group_name' ),
                                   [ match.group( 'content').strip() ] )
    else:
      if looking_for_group:
        continue

      if line[ 0 ] == ' ' or line[ 0 ] == '\t':
        current_group.lines.append( line.strip() )

  if current_group:
    group_name_to_group[ current_group.name ] = current_group
  return group_name_to_group


def _CreateInitialGroupMap():
  def AddToGroupMap( name, parent ):
    new_group = SyntaxGroup( name )
    group_name_to_group[ name ] = new_group
    parent.children.append( new_group )

  identifier_group = SyntaxGroup( 'Identifier' )
  statement_group  = SyntaxGroup( 'Statement' )
  type_group       = SyntaxGroup( 'Type' )
  preproc_group    = SyntaxGroup( 'PreProc' )

  # See ":h group-name" for details on how the initial group hierarchy is built.
  group_name_to_group = {
    'Boolean': SyntaxGroup( 'Boolean' ),
    'Identifier': identifier_group,
    'Statement': statement_group,
    'PreProc': preproc_group,
    'Type': type_group
  }

  AddToGroupMap( 'Function', identifier_group )

  AddToGroupMap( 'Conditional', statement_group )
  AddToGroupMap( 'Repeat'     , statement_group )
  AddToGroupMap( 'Label'      , statement_group )
  AddToGroupMap( 'Operator'   , statement_group )
  AddToGroupMap( 'Keyword'    , statement_group )
  AddToGroupMap( 'Exception'  , statement_group )

  AddToGroupMap( 'StorageClass', type_group )
  AddToGroupMap( 'Structure'   , type_group )
  AddToGroupMap( 'Typedef'     , type_group )

  AddToGroupMap( 'Include'  , preproc_group )
  AddToGroupMap( 'Define'   , preproc_group )
  AddToGroupMap( 'Macro'    , preproc_group )
  AddToGroupMap( 'PreCondit', preproc_group )

  return group_name_to_group


def _ConnectGroupChildren( group_name_to_group ):
  def GetParentNames( group ):
    links_to     = 'links to '
    parent_names = []
    for line in group.lines:
      if line.startswith( links_to ):
        parent_names.append( line[ len( links_to ): ] )
    return parent_names

  for group in itervalues( group_name_to_group ):
    parent_names = GetParentNames( group )

    for parent_name in parent_names:
      try:
        parent_group = group_name_to_group[ parent_name ]
      except KeyError:
        continue
      parent_group.children.append( group )


def _GetAllDescendentats( root_group ):
  descendants = []
  for child in root_group.children:
    descendants.append( child )
    descendants.extend( _GetAllDescendentats( child ) )
  return descendants


def _ExtractKeywordsFromLine( line ):
  if line.startswith( 'links to ' ):
    return []

  # Ignore "syntax match" lines (see ":h syn-match").
  if line.startswith( 'match ' ):
    return []

  words = line.split()
  if not words:
    return []

  # Ignore "syntax region" lines (see ":h syn-region"). They always start
  # with matchgroup= or start= in the syntax list.
  if SYNTAX_REGION_ARGUMENT_REGEX.match( words[ 0 ] ):
    return []

  # Ignore "nextgroup=" argument in first position and the arguments
  # "skipwhite", "skipnl", and "skipempty" that immediately come after.
  nextgroup_at_start = False
  if words[ 0 ].startswith( 'nextgroup=' ):
    nextgroup_at_start = True
    words = words[ 1: ]

  # Ignore "contained" argument in first position.
  if words[ 0 ] == 'contained':
    words = words[ 1: ]

  keywords = []
  for word in words:
    if nextgroup_at_start and word in SYNTAX_NEXTGROUP_ARGUMENTS:
      continue

    nextgroup_at_start = False

    keyword_matched = KEYWORD_REGEX.match( word )
    if keyword_matched:
      keywords.append( keyword_matched.group( 1 ) )
  return keywords


def _ExtractKeywordsFromGroup( group ):
  keywords = []
  for line in group.lines:
    keywords.extend( _ExtractKeywordsFromLine( line ) )
  return keywords
