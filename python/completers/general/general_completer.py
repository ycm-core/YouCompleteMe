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

from completers.completer import Completer
import inspect
import importlib
import Queue
from threading import Thread, Event


class GeneralCompleter( Completer ):
  def __init__( self, *args ):
    super( GeneralCompleter, self ).__init__()

    # args type is ([]) so we select a list inside a tuple
    self.complList = self.InitCompleters( args[0] )
    self.query = None
    self._query_ready = Event()
    self._candidates = []
    self.queue = Queue.Queue()
    self.threads = []
    self.StartThreads()


  def _start_completion_thread( self, completer ):
    thread = Thread( target=self.SetCandidates,
                    args=(completer.completer, completer.event,
                          completer.finished) )
    thread.daemon = True
    thread.start()
    self.threads.append( thread )


  def InitCompleters( self, completers ):
    # This method creates objects of main completers class.
    complList = []
    for compl in completers:

      # We need to specify full path to the module
      fullpath = 'completers.general.' + compl

      module = importlib.import_module( fullpath )

      for _, ClassObject in inspect.getmembers( module, inspect.isclass ):
        # Iterate over all classes in a module and select main class
        if hasattr( ClassObject,'CandidatesForQueryAsyncInner' ):
          classInstance = ClassObject

      # Init selected class and store class object
      complList.append( CompleterInstance( classInstance() ) )
    return complList

  def SupportedFiletypes( self ):
    # TODO this is useless here. Change?
    # magic token meaning all filetypes
    return set( [ 'ycm_all' ] )


  def ShouldUseNow( self, start_column ):
    # Query all completers and set flag to True if any of completers returns
    # True. Also update flags in completers classes and make a list with a flags
    # This list is needed to know whether update cache or not
    flag = False
    for completer in self.complList:
      ShouldUse = completer.completer.ShouldUseNow( start_column )
      completer.ShouldUse = ShouldUse
      if ShouldUse:
        flag = True

    return flag

  def CandidatesForQueryAsync( self, query ):
    self.query = query
    self._candidates = []
    self._query_ready.set()

    # if completer should be used start thread by setting Event flag
    for completer in self.complList:
      completer.finished.clear()
      if completer.ShouldUse and not completer.event.is_set():
        completer.event.set()


  def AsyncCandidateRequestReady( self ):
    for completer in self.complList:
        if completer.finished.is_set():
            return True
    return False


  def OnFileReadyToParse( self ):
    # Process all parsing methods of completers. Needed by identifier completer
    for completer in self.complList:
      completer.completer.OnFileReadyToParse()


  def CandidatesFromStoredRequest( self ):
    while not self.queue.empty():
        self._candidates += self.queue.get()

    return self._candidates


  def SetCandidates( self, completer, event, finished ):
    while True:
      WaitAndClear( self._query_ready )

      # sleep until ShouldUseNow returns True
      WaitAndClear( event )

      completer.CandidatesForQueryAsync( self.query )

      while not completer.AsyncCandidateRequestReady():
        continue

      self.queue.put(completer.CandidatesFromStoredRequest())

      finished.set()


  def StartThreads( self ):
    for completer in self.complList:
      self._start_completion_thread( completer )


class CompleterInstance(object):
  def __init__( self, completer):
    self.completer = completer
    self.event = Event()
    self.ShouldUse = False
    self.finished = Event()


def WaitAndClear( event, timeout=None ):
    flag_is_set = event.wait( timeout )
    if flag_is_set:
      event.clear()
    return flag_is_set
