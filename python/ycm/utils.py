#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Strahinja Val Markovic  <val@markovic.io>
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

import tempfile
import os

def IsIdentifierChar( char ):
  return char.isalnum() or char == '_'


def SanitizeQuery( query ):
  return query.strip()


def ToUtf8IfNeeded( string_or_unicode ):
  if isinstance( string_or_unicode, unicode ):
    return string_or_unicode.encode( 'utf8' )
  return string_or_unicode


def PathToTempDir():
  return os.path.join( tempfile.gettempdir(), 'ycm_temp' )
