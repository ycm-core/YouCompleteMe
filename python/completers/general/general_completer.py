#!/usr/bin/env python
#
# Copyright (C) 2013  Stanislav Golovanov <stgolovanov@gmail.com>
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
from completers.all.identifier_completer import IdentifierCompleter
from threading import Thread, Event
import vimsupport
import inspect
import fnmatch
import os


class GeneralCompleterStore( Completer ):
  """
  Main class that holds a list of completers that can be used in all filetypes.
  This class creates a single GeneralCompleterInstance() class instance
  for each general completer and makes a separate thread for each completer.

  It overrides all Competer API methods so that specific calls to
  GeneralCompleterStore are passed to all general completers.

  This class doesnt maintain a cache because it will make a problems for
  some completers like identifier completer. Caching is done in a general
  completers itself.
  """
  def __init__( self ):
    super( GeneralCompleterStore, self ).__init__()
    self.completers = self.InitCompleters()
    self.query = None
    self._candidates = []
    self.threads = []
    self.StartThreads()


  def _start_completion_thread( self, completer ):
    thread = Thread( target=self.SetCandidates, args=(completer,) )
    thread.daemon = True
    thread.start()
    self.threads.append( thread )


  def InitCompleters( self ):
    # This method creates objects of main completers class.
    completers = []
    modules = [ module for module in os.listdir( os.path.dirname(__file__) )
                if fnmatch.fnmatch(module, '*.py')
                and not 'general_completer' in module
                and not '__init__' in module
                and not 'hook' in module ]

    for module in modules:

      # We need to specify full path to the module
      fullpath = 'completers.general.' + module[:-3]

      try:
        module = __import__( fullpath, fromlist=[''] )
      except ImportError as error:
        vimsupport.PostVimMessage( 'Import of general completer "{0}" has '
                                   'failed, skipping. Full error: {1}'.format(
                                     module, str( error ) ) )
        continue

      for _, ClassObject in inspect.getmembers( module, inspect.isclass ):
        # Iterate over all classes in a module and select main class
        if hasattr( ClassObject, 'CandidatesForQueryAsyncInner' ):
          classInstance = ClassObject

      # Init selected class and store class object
      completers.append( GeneralCompleterInstance( classInstance() ) )

    # append IdentifierCompleter
    completers.append( GeneralCompleterInstance( IdentifierCompleter() ) )
    return completers


  def SupportedFiletypes( self ):
    # magic token meaning all filetypes
    return set( [ 'ycm_all' ] )


  def ShouldUseNow( self, start_column ):
    # Query all completers and set flag to True if any of completers returns
    # True. Also update flags in completers classes
    flag = False
    for completer in self.completers:
      ShouldUse = completer.completer.ShouldUseNow( start_column )
      completer.ShouldUse = ShouldUse
      if ShouldUse:
        flag = True

    return flag


  def CandidatesForQueryAsync( self, query, start_column ):
    self.query = query
    self._candidates = []

    # if completer should be used start thread by setting Event flag
    for completer in self.completers:
      completer.finished.clear()
      if completer.ShouldUse and not completer.should_start.is_set():
        completer.should_start.set()


  def AsyncCandidateRequestReady( self ):
    # Return True when all completers that should be used are finished their work.
    for completer in self.completers:
        if not completer.finished.is_set() and completer.ShouldUse:
            return False
    return True


  def CandidatesFromStoredRequest( self ):
    for completer in self.completers:
      if completer.ShouldUse and completer.finished.is_set():
          self._candidates += completer.results.pop()

    return self._candidates


  def SetCandidates( self, completer ):
    while True:

      # sleep until ShouldUseNow returns True
      WaitAndClear( completer.should_start )

      completer.completer.CandidatesForQueryAsync( self.query,
                                                   self.completion_start_column )

      while not completer.completer.AsyncCandidateRequestReady():
          continue

      completer.results.append( completer.completer.CandidatesFromStoredRequest() )

      completer.finished.set()


  def StartThreads( self ):
    for completer in self.completers:
      self._start_completion_thread( completer )


  def OnFileReadyToParse( self ):
    # Process all parsing methods of completers. Needed by identifier completer
    for completer in self.completers:
      # clear all stored completion results
      completer.results = []
      completer.completer.OnFileReadyToParse()


  def OnCursorMovedInsertMode( self ):
    for completer in self.completers:
      completer.completer.OnCursorMovedInsertMode()


  def OnCursorMovedNormalMode( self ):
    for completer in self.completers:
      completer.completer.OnCursorMovedNormalMode()


  def OnBufferVisit( self ):
    for completer in self.completers:
      completer.completer.OnBufferVisit()


  def OnBufferDelete( self, deleted_buffer_file ):
    for completer in self.completers:
      completer.completer.OnBufferDelete( deleted_buffer_file )


  def OnCursorHold( self ):
    for completer in self.completers:
      completer.completer.OnCursorHold()


  def OnInsertLeave( self ):
    for completer in self.completers:
      completer.completer.OnInsertLeave()


class GeneralCompleterInstance( object ):
  """
  Class that holds all meta information about specific general completer
  """
  def __init__( self, completer ):
    self.completer = completer
    self.should_start = Event()
    self.ShouldUse = False
    self.finished = Event()
    self.results = []


def WaitAndClear( event, timeout=None ):
    flag_is_set = event.wait( timeout )
    if flag_is_set:
      event.clear()
    return flag_is_set
