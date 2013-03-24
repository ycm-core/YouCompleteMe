#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Stephen Sugden <me@stephensugden.com>
#                           Strahinja Val Markovic <val@markovic.io>
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
from threading import Thread, Event
from completers.completer import Completer
from vimsupport import CurrentLineAndColumn

import sys
from os.path import join, abspath, dirname

# We need to add the jedi package to sys.path, but it's important that we clean
# up after ourselves, because ycm.YouCompletMe.GetFiletypeCompleterForFiletype
# removes sys.path[0] after importing completers.python.hook
sys.path.insert(0, join(abspath(dirname(__file__)), 'jedi'))
from jedi import Script
sys.path.pop(0)


class JediCompleter(Completer):
  """
  A Completer that uses the Jedi completion engine.
  https://jedi.readthedocs.org/en/latest/
  """

  def __init__(self):
    super(JediCompleter, self).__init__()
    self._query_ready = Event()
    self._candidates_ready = Event()
    self._query = None
    self._candidates = None
    self._exit = False
    self._start_completion_thread()


  def _start_completion_thread(self):
    self._completion_thread = Thread(target=self.SetCandidates)
    self._completion_thread.start()


  def SupportedFiletypes(self):
    """ Just python """
    return ['python']


  def CandidatesForQueryAsyncInner(self, query):
    self._query = query
    self._candidates = None
    self._candidates_ready.clear()
    self._query_ready.set()


  def AsyncCandidateRequestReadyInner(self):
    if self._completion_thread.is_alive():
      return WaitAndClear(self._candidates_ready, timeout=0.005)
    else:
      self._start_completion_thread()
      return False


  def CandidatesFromStoredRequestInner(self):
    return self._candidates or []


  def SetCandidates(self):
    while True:
      WaitAndClear(self._query_ready)

      if self._exit:
        return

      filename = vim.current.buffer.name
      query = self._query
      line, column = CurrentLineAndColumn()
      lines = map(str, vim.current.buffer)
      if query is not None and lines[line]:
        before, after = lines[line].rsplit('.', 1)
        lines[line] = before + '.'
        column = len(before) + 1

      source = "\n".join(lines)
      script = Script(source, line + 1, column, filename)

      self._candidates = [{'word': str(completion.word),
                            'menu': str(completion.description),
                            'info': str(completion.doc)}
                          for completion in script.complete()]

      self._candidates_ready.set()


def WaitAndClear(event, timeout=None):
    ret = event.wait(timeout)
    if ret:
        event.clear()
    return ret
