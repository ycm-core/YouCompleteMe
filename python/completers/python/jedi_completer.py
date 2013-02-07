# Copyright (C) 2011, 2012  Stephen Sugden <me@stephensugden.com>
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

import vim
from completers.completer import Completer
from vimsupport import PostVimMessage, CurrentLineAndColumn

import sys
from os.path import join, abspath, dirname

# We need to add the jedi package to sys.path, but it's important that we clean
# up after ourselves, because ycm.YouCompletMe.GetFiletypeCompleterForFiletype
# removes sys.path[0] after importing completers.python.hook
sys.path.insert(0, join(abspath(dirname(__file__)), 'jedi'))
from jedi import Script
sys.path.pop(0)

class JediCompleter( Completer ):
    """
    A Completer that uses the Jedi completion engine 
    https://jedi.readthedocs.org/en/latest/
    """

    def __init__( self ):
        self.candidates = None

    def SupportedFiletypes( self ):
        """ Just python """
        return ['python']

    def ShouldUseNow(self, start_column):
        """ Only use jedi-completion after a . """
        line = vim.current.line
        return len(line) >= start_column and line[start_column - 1] == '.'

    def CandidatesFromStoredRequest( self ):
        return self.candidates
    
    def OnFileReadyToParse(self):
        pass

    def AsyncCandidateRequestReady(self):
        return self.candidates is not None

    def CandidatesFromStoredRequest(self):
        return self.candidates

    def CandidatesForQueryAsync( self, query ):
        buffer = vim.current.buffer
        filename = buffer.name
        line, column = CurrentLineAndColumn()
        script = Script("\n".join(buffer), line + 1, column, filename)
        self.candidates = [completion.word for completion
                           in script.complete() if completion.word.startswith(query)]
