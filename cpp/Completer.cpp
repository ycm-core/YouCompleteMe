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

using boost::python::len;
using boost::python::extract;

namespace YouCompleteMe
{


Completer::Completer( const Pylist &candidates )
{
  AddCandidatesToDatabase( candidates, "", "" );
}


Completer::Completer( const Pylist &candidates,
                      const std::string &filetype,
                      const std::string &filepath)
{
  AddCandidatesToDatabase( candidates, filetype, filepath );
}


Completer::~Completer()
{
  foreach ( const CandidateRepository::value_type &pair,
            candidate_repository_ )
  {
    delete pair.second;
  }
}


void Completer::AddCandidatesToDatabase( const Pylist &new_candidates,
                                         const std::string &filetype,
                                         const std::string &filepath )
{
  std::vector< Candidate *> &candidates =
    GetCandidateVector( filetype, filepath );

  int num_candidates = len( new_candidates );
  candidates.clear();
  candidates.reserve( num_candidates );

  std::string candidate_text;
  for (int i = 0; i < num_candidates; ++i)
  {
    candidate_text = extract< std::string >( new_candidates[ i ] );
    Candidate *&candidate = GetValueElseInsert( candidate_repository_,
                                                candidate_text, NULL );
    if ( !candidate )
      candidate = new Candidate( candidate_text );

    candidates.push_back( candidate );
  }
}


void Completer::CandidatesForQuery( const std::string &query,
                                    Pylist &candidates ) const
{
  CandidatesForQueryAndType( query, "", candidates );
}


void Completer::CandidatesForQueryAndType( const std::string &query,
                                           const std::string &filetype,
                                           Pylist &candidates ) const
{
  FiletypeMap::const_iterator it = filetype_map_.find( filetype );
  if ( it == filetype_map_.end() )
    return;

  Bitset query_bitset = LetterBitsetFromString( query );
  std::vector< Result > results;

  foreach ( const FilepathToCandidates::value_type &path_and_candidates,
            *it->second )
  {
    foreach ( Candidate* candidate, *path_and_candidates.second )
    {
      if ( !candidate->MatchesQueryBitset( query_bitset ) )
        continue;

      Result result = candidate->QueryMatchResult( query );
      if ( result.IsSubsequence() )
        results.push_back( result );
    }
  }

  std::sort( results.begin(), results.end() );

  foreach ( const Result& result, results )
  {
    candidates.append( *result.Text() );
  }
}


std::vector< Candidate* >& Completer::GetCandidateVector(
    const std::string &filetype,
    const std::string &filepath )
{
  boost::shared_ptr< FilepathToCandidates > &path_to_candidates =
    filetype_map_[ filetype ];

  if ( !path_to_candidates )
    path_to_candidates.reset( new FilepathToCandidates() );

  boost::shared_ptr< std::vector< Candidate* > > &candidates =
    (*path_to_candidates)[ filepath ];

  if ( !candidates )
    candidates.reset( new std::vector< Candidate* >() );

  return *candidates;
}


} // namespace YouCompleteMe
