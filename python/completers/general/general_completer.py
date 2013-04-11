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
from threading import Thread
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
                and not '__init__' in module ]

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
        if not __name__ in str(ClassObject) and 'general' in str(ClassObject):

          classInstance = ClassObject


      # Init selected class and store class object
      completers.append( classInstance() )
    
    completers.append( IdentifierCompleter() )

    return completers


  def SupportedFiletypes( self ):
    return set()


  def ShouldUseNow( self, start_column ):
    # Query all completers and set flag to True if any of completers returns
    # True. Also update flags in completers classes
    flag = False
    for completer in self.completers:
      _should_use = completer.ShouldUseNow( start_column )
      completer._should_use = _should_use
      if _should_use:
        flag = True

    return flag


  def CandidatesForQueryAsync( self, query, start_column ):
    self.query = query
    self._candidates = []

    # if completer should be used start thread by setting Event flag
    for completer in self.completers:
      completer._finished.clear()
      if completer._should_use and not completer._should_start.is_set():
        completer._should_start.set()


  def AsyncCandidateRequestReady( self ):
    # Return True when all completers that should be used are finished their work.
    for completer in self.completers:
        if not completer._finished.is_set() and completer._should_use:
            return False
    return True


  def CandidatesFromStoredRequest( self ):
    for completer in self.completers:
      if completer._should_use and completer._finished.is_set():
          self._candidates += completer._results.pop()

    return self._candidates


  def SetCandidates( self, completer ):
    while True:

      # sleep until ShouldUseNow returns True
      WaitAndClear( completer._should_start )

      completer.CandidatesForQueryAsync( self.query,
                                                   self.completion_start_column )

      while not completer.AsyncCandidateRequestReady():
          continue

      completer._results.append( completer.CandidatesFromStoredRequest() )

      completer._finished.set()


  def StartThreads( self ):
    for completer in self.completers:
      self._start_completion_thread( completer )


  def OnFileReadyToParse( self ):
    # Process all parsing methods of completers. Needed by identifier completer
    for completer in self.completers:
      # clear all stored completion results
      completer._results = []
      completer.OnFileReadyToParse()


  def OnCursorMovedInsertMode( self ):
    for completer in self.completers:
      completer.OnCursorMovedInsertMode()


  def OnCursorMovedNormalMode( self ):
    for completer in self.completers:
      completer.OnCursorMovedNormalMode()


  def OnBufferVisit( self ):
    for completer in self.completers:
      completer.OnBufferVisit()


  def OnBufferDelete( self, deleted_buffer_file ):
    for completer in self.completers:
      completer.OnBufferDelete( deleted_buffer_file )


  def OnCursorHold( self ):
    for completer in self.completers:
      completer.OnCursorHold()


  def OnInsertLeave( self ):
    for completer in self.completers:
      completer.OnInsertLeave()


def WaitAndClear( event, timeout=None ):
    flag_is_set = event.wait( timeout )
    if flag_is_set:
      event.clear()
    return flag_is_set
