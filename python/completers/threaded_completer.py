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

import abc
from threading import Thread, Event
from completer import Completer

class ThreadedCompleter( Completer ):
  def __init__( self ):
    super( ThreadedCompleter, self ).__init__()
    self._query_ready = Event()
    self._candidates_ready = Event()
    self._candidates = None
    self._start_completion_thread()


  def _start_completion_thread( self ):
    self._completion_thread = Thread( target=self.SetCandidates )
    self._completion_thread.daemon = True
    self._completion_thread.start()


  def CandidatesForQueryAsyncInner( self, query, start_column ):
    self._candidates = None
    self._candidates_ready.clear()
    self._query = query
    self._start_column = start_column
    self._query_ready.set()


  def AsyncCandidateRequestReadyInner( self ):
    return WaitAndClearIfSet( self._candidates_ready, timeout=0.005 )


  def CandidatesFromStoredRequestInner( self ):
    return self._candidates or []


  @abc.abstractmethod
  def ComputeCandidates( self, query, start_column ):
    pass


  def SetCandidates( self ):
    while True:
      try:
        WaitAndClearIfSet( self._query_ready )
        self._candidates = self.ComputeCandidates( self._query,
                                                   self._start_column )
      except:
        self._query_ready.clear()
        self._candidates = []
      self._candidates_ready.set()


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
