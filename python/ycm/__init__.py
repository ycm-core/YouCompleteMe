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

from youcompleteme import (
  YouCompleteMe, CompatibleWithYcmCore, CurrentIdentifierFinished,
  CompletionStartColumn )

# We don't really need to do this, but if we don't, pyflakes complains that we
# have unused imports. Pyflakes should ignore unused imports in __init__.py
# files, but doesn't. See this bug report:
# https://bugs.launchpad.net/pyflakes/+bug/1178905
__all__ = [
  YouCompleteMe.__name__,
  CompatibleWithYcmCore.__name__,
  CurrentIdentifierFinished.__name__,
  CompletionStartColumn.__name__
]
