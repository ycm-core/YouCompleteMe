// Copyright (C) 2011, 2012  Strahinja Val Markovic  <val@markovic.io>
//
// This file is part of YouCompleteMe.
//
// YouCompleteMe is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// YouCompleteMe is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

#include "standard.h"
#include "Completer.h"
#include "Utils.h"

namespace YouCompleteMe
{

Completer::Completer( const Pylist &candidates )
{
  AddCandidatesToDatabase( candidates, "" );
}


Completer::Completer( const Pylist &candidates, const std::string &filepath)
{
  AddCandidatesToDatabase( candidates, filepath );
}


Completer::~Completer()
{
  foreach ( const CandidateRepository::value_type &pair,
            candidate_repository_ )
  {
    delete pair.second;
  }
}


void Completer::AddCandidatesToDatabase( const Pylist &candidates,
                                         const std::string &filepath )
{
  std::string candidate_text;
  for (int i = 0; i < boost::python::len( candidates ); ++i)
  {
    candidate_text = boost::python::extract< std::string >( candidates[ i ] );
    Candidate *&candidate = GetValueElseInsert( candidate_repository_,
                                                candidate_text, NULL );
    if ( !candidate )
    {
      candidate = new Candidate( candidate_text );
      candidates_.insert( candidate );
    }
  }
}


void Completer::GetCandidatesForQuery(
    const std::string &query, Pylist &candidates ) const
{
  Bitset query_bitset = LetterBitsetFromString( query );
  std::vector< Result > results;

  foreach ( Candidate* candidate, candidates_ )
  {
    if ( !candidate->MatchesQueryBitset( query_bitset ) )
      continue;

    Result result = candidate->QueryMatchResult( query );
    if ( result.IsSubsequence() )
      results.push_back( result );
  }

  // Needs to be stable to preserve the lexical sort of the candidates from the
  // candidates_ container
  std::stable_sort( results.begin(), results.end() );

  foreach ( const Result& result, results )
  {
    candidates.append( *result.Text() );
  }
}


} // namespace YouCompleteMe
