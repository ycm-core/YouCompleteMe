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
import collections
from threading import Thread, Event


class GeneralCompleter( Completer ):
  def __init__( self, *args ):
    super( GeneralCompleter, self ).__init__()

    # args type is ([]) so we select a list inside a tuple
    self.complList = self.InitCompleters( args[0] )
    self.query = None
    self._query_ready = Event()
    self._candidates = []
    self.flag = False
    self.threads = []
    self.StartThreads()

  def _start_completion_thread( self, completer ):
    thread = Thread( target=self.SetCandidates, args=(completer.completer, completer.event) )
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


  def ShouldUseNowInner( self, start_column ):
    # Query all completers and set flag to True if any of completers returns
    # True. Also update flags in completers classes and make a list with a flags
    # This list is needed to know whether update cache or not
    flag = False
    self.flags = []
    for completer in self.complList:
      ShouldUse = completer.completer.ShouldUseNow( start_column )
      completer.ShouldUse = ShouldUse
      self.flags.append( ShouldUse )
      if ShouldUse:
        flag = True

    return flag

  def CandidatesForQueryAsyncInner( self, query ):
    self.flag = False
    self.query = query
    self._candidates = collections.deque()
    self._query_ready.set()

    # Store a flags list copy. We need this to know when we should
    # run this method again because another returned True from ShouldUseNow
    # method
    self.flags_backup = list( self.flags )

    # if completer should be used start thread by setting Event flag
    for completer in self.complList:
      if completer.ShouldUse and not completer.event.is_set():
        completer.event.set()


  def AsyncCandidateRequestReadyInner( self ):
    return self.flag


  def OnFileReadyToParse( self ):
    # Process all parsing methods of completers. Needed by identifier completer
    for completer in self.complList:
      completer.completer.OnFileReadyToParse()


  def CandidatesForQueryAsync( self, query ):
    # We need to override this method because we are using collections.Deque
    # as a completions container while sorting need a List.
    # TODO actually this can be done in a CandidatesFromStoredRequestInner
    # method but for some reason it will only show identifier completer results
    # and ignore all other completers.
    # Also we need to compare ShouldUseNow with a previous version to know
    # when we need to update cache because another completer returned True
    if (query and self.completions_cache and self.completions_cache.CacheValid()
        and self.flags == self.flags_backup):

      self.completions_cache.filtered_completions = (
        self.FilterAndSortCandidates(
          list(self.completions_cache.raw_completions),
          query ) )
    else:
      self.completions_cache = None
      self.CandidatesForQueryAsyncInner( query )


  def CandidatesFromStoredRequestInner( self ):
    return self._candidates


  def SetCandidates( self, completer, event ):
    while True:
      WaitAndClear( self._query_ready )

      # sleep until ShouldUseNow returns True
      WaitAndClear( event )

      completer.CandidatesForQueryAsync( self.query )

      while not completer.AsyncCandidateRequestReady():
        continue

      # We are using collections.deque as a container because it allows
      # easy and efficient prepending to a list. We need this because we
      # want identifier completions at the end of the list because if there are
      # multiple matches with the same name sort method will keep only match
      # that is closer to the beginning of the list and remove other matches.
      self._candidates.extendleft( completer.CandidatesFromStoredRequest() )

      self.flag = True


  def StartThreads( self ):
    for completer in self.complList:
      self._start_completion_thread( completer )


class CompleterInstance(object):
  def __init__( self, completer):
    self.completer = completer
    self.event = Event()
    self.ShouldUse = False


def WaitAndClear( event, timeout=None ):
    flag_is_set = event.wait( timeout )
    if flag_is_set:
      event.clear()
    return flag_is_set
