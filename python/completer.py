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


class Completer( object ):
  __metaclass__ = abc.ABCMeta


  def __init__( self ):
    self.future = None


  def AsyncCandidateRequestReady( self ):
    if not self.future:
      # We return True so that the caller can extract the default value from the
      # future
      return True
    return self.future.ResultsReady()


  def CandidatesFromStoredRequest( self ):
    if not self.future:
      return []
    return self.future.GetResults()


  def OnFileReadyToParse( self ):
    pass


  def OnCursorMovedInsertMode( self ):
    pass


  def OnCursorMovedNormalMode( self ):
    pass


  def OnBufferVisit( self ):
    pass


  def OnCursorHold( self ):
    pass


  def OnInsertLeave( self ):
    pass


  def OnCurrentIdentifierFinished( self ):
    pass


  def DiagnosticsForCurrentFileReady( self ):
    return False


  def GetDiagnosticsForCurrentFile( self ):
    return []


  @abc.abstractmethod
  def SupportedFiletypes( self ):
    pass


  @abc.abstractmethod
  def ShouldUseNow( self, start_column ):
    pass
