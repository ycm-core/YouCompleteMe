// Copyright (C) 2013  Strahinja Val Markovic  <val@markovic.io>
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

#include "IdentifierDatabase.h"
#include "standard.h"

#include "Candidate.h"
#include "CandidateRepository.h"
#include "IdentifierUtils.h"
#include "Result.h"
#include "Utils.h"

#include <boost/thread/locks.hpp>
#include <boost/unordered_set.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/cxx11/any_of.hpp>

using boost::algorithm::any_of;
using boost::algorithm::is_upper;


namespace YouCompleteMe {

IdentifierDatabase::IdentifierDatabase()
  : candidate_repository_( CandidateRepository::Instance() ) {
}


void IdentifierDatabase::AddCandidates(
  const std::vector< std::string > &new_candidates,
  const std::string &filetype,
  const std::string &filepath ) {
  boost::lock_guard< boost::mutex > locker( filetype_map_mutex_ );
  std::list< const Candidate *> &candidates =
    GetCandidateList( filetype, filepath );

  std::vector< const Candidate * > repository_candidates =
    candidate_repository_.GetCandidatesForStrings( new_candidates );

  candidates.insert( candidates.end(),
                     repository_candidates.begin(),
                     repository_candidates.end() );
}


void IdentifierDatabase::ClearCandidatesStoredForFile(
  const std::string &filetype,
  const std::string &filepath ) {
  boost::lock_guard< boost::mutex > locker( filetype_map_mutex_ );
  GetCandidateList( filetype, filepath ).clear();
}


void IdentifierDatabase::ResultsForQueryAndType(
  const std::string &query,
  const std::string &filetype,
  std::vector< Result > &results ) const {
  FiletypeMap::const_iterator it;
  {
    boost::lock_guard< boost::mutex > locker( filetype_map_mutex_ );
    it = filetype_map_.find( filetype );

    if ( it == filetype_map_.end() || query.empty() )
      return;
  }
  Bitset query_bitset = LetterBitsetFromString( query );
  bool query_has_uppercase_letters = any_of( query, is_upper() );

  boost::unordered_set< const Candidate * > seen_candidates;
  seen_candidates.reserve( candidate_repository_.NumStoredCandidates() );

  {
    boost::lock_guard< boost::mutex > locker( filetype_map_mutex_ );
    foreach ( const FilepathToCandidates::value_type & path_and_candidates,
              *it->second ) {
      foreach ( const Candidate * candidate, *path_and_candidates.second ) {
        if ( ContainsKey( seen_candidates, candidate ) )
          continue;
        else
          seen_candidates.insert( candidate );

        if ( !candidate->MatchesQueryBitset( query_bitset ) )
          continue;

        Result result = candidate->QueryMatchResult(
                          query, query_has_uppercase_letters );

        if ( result.IsSubsequence() )
          results.push_back( result );
      }
    }
  }

  std::sort( results.begin(), results.end() );
}


// WARNING: You need to hold the filetype_map_mutex_ before calling this
// function and while using the returned list.
std::list< const Candidate * > &IdentifierDatabase::GetCandidateList(
  const std::string &filetype,
  const std::string &filepath ) {
  boost::shared_ptr< FilepathToCandidates > &path_to_candidates =
    filetype_map_[ filetype ];

  if ( !path_to_candidates )
    path_to_candidates.reset( new FilepathToCandidates() );

  boost::shared_ptr< std::list< const Candidate * > > &candidates =
    ( *path_to_candidates )[ filepath ];

  if ( !candidates )
    candidates.reset( new std::list< const Candidate * >() );

  return *candidates;
}



} // namespace YouCompleteMe
