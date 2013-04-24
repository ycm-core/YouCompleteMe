#!/usr/bin/env python
#
# Copyright (C) 2013 Stanislav Golovanov <stgolovanov@gmail.com>
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

from threading import Thread, Event
from flake8 import main as flake8
from cStringIO import StringIO
import sys
import vim
import re


class SyntaxChecker( object ):

  def __init__( self ):
    self._should_check_syntax = Event()
    self._checking_finished = Event()
    self._checking_thread = Thread( target=self.SyntaxCheck )
    self._checking_thread.daemon = True
    self._checking_thread.start()
    # parses a string like:
    # stdin:10:10 E201 Whitespace after '('
    self._parsing_regex = re.compile( """
                                     (\S+?):(\d+):(\d+): ([a-zA-Z])(\d+?) (.*)
                                     """, re.X )


  def PerformSyntaxChecking( self, query, start_column ):
      self.diagnostics = []
      self._should_check_syntax.set()


  def SyntaxCheckingReady( self ):
      return self._checking_finished.is_set()


  def ReturnSyntaxCheckingResults( self ):
      return self.diagnostics or []


  def SyntaxCheck( self ):
    while True:
      WaitAndClearIfSet( self._should_check_syntax )

      # This is a stdout redirecting hack. This is needed because flake8, pep8,
      # all syntax checking tools pass their results to stdout...
      # so we need to capture it
      try:
        old_stdout = sys.stdout
        sys.stdout = redirected_stdout = StringIO()

        buffer_contents = '\n'.join( vim.current.buffer )
        flake8.check_code( buffer_contents )

        sys.stdout = old_stdout
      except BaseException:
        self.diagnostics = []
        return

      diagnostics = redirected_stdout.getvalue()
      bufnr = vim.current.buffer.number

      # _parsing regex returns a tuple where:
      # x[0] is a 'stdin' string
      # x[1] is a line number
      # x[2] is a column
      # x[3] is a error type. Its s letter from string like 'E401'
      # x[4] is a error number from string like 'E401'
      # x[5] is a error text. E.g. "whitespace after '('"
      self.diagnostics = [ {'lnum': x[1],
                            'col': x[2],
                            'type': x[3],
                            'nr': x[4],
                            'text': x[5],
                            'valid': 1,
                            'bufnr': bufnr}
                          for x in self._parsing_regex.findall(diagnostics) ]
      self._checking_finished.set()


def WaitAndClearIfSet( event, timeout=None ):
  """Given an |event| and a |timeout|, waits for the event a maximum of timeout
  seconds. After waiting, clears the event if it's set and returns the state of
  the event before it was cleared."""

  # We can't just do flag_is_set = event.wait( timeout ) because that breaks on
  # Python 2.6
  event.wait( timeout )
  flag_is_set = event.is_set()
  if flag_is_set:
      event.clear()
  return flag_is_set
