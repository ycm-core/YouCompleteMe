#!/usr/bin/env python
#
# Copyright (C) 2013 Zhao Cai <caizhaoff@gmail.com>
#                    Strahinja Val Markovic  <val@markovic.io>
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

from completers.general_completer import GeneralCompleter
import vim
import vimsupport


class SpellCompleter( GeneralCompleter ):
  """
  General completer that provides spell suggestions completions.
  """

  def __init__( self ):
    super( SpellCompleter, self ).__init__()
    self._candidates = []


  def ShouldUseNowInner( self, start_column ):
    return self.QueryLengthAboveMinThreshold( start_column ) and self.is_spell_on()


  def SupportedFiletypes( self ):
    return []


  def CandidatesForQueryAsync( self, query, unused_start_column ):
    self._candidates = self._GetCandidates(query)



  def AsyncCandidateRequestReady( self ):
    return True


  def CandidatesFromStoredRequest( self ):
    return self._candidates


  def _GetCandidates( self, query):
    return  [ { 'word': str( ss ),
                'menu': str( '<spell> ' + ss ) }
              for ss in vim.eval('spellsuggest("'
                + vimsupport.EscapeForVim( query )
                + '", ' + self.max_candidates()
                + ')')
            ]

  @classmethod
  def is_spell_on(cls):
    return vimsupport.GetBoolValue('&spell') and vimsupport.GetBoolValue('g:ycm_spellsuggest_enable')

  @classmethod
  def max_candidates(cls):
    return vimsupport.GetVariableValue('g:ycm_spellsuggest_max_candidates')
