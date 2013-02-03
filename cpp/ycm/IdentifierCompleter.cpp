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

#include "IdentifierCompleter.h"
#include "standard.h"
#include "CandidateRepository.h"
#include "Candidate.h"
#include "Result.h"
#include "Utils.h"
#include "IdentifierUtils.h"

#include <boost/unordered_set.hpp>
#include <boost/bind.hpp>
#include <boost/make_shared.hpp>
#include <algorithm>

using boost::packaged_task;
using boost::bind;
using boost::unique_future;
using boost::make_shared;
using boost::shared_ptr;
using boost::bind;
using boost::thread;

namespace YouCompleteMe {

typedef boost::function< std::vector< std::string >() >
FunctionReturnsStringVector;


extern const unsigned int MAX_ASYNC_THREADS = 4;
extern const unsigned int MIN_ASYNC_THREADS = 2;

namespace {

void QueryThreadMain(
  IdentifierCompleter::LatestQueryTask &latest_query_task ) {
  while ( true ) {
    try {
      ( *latest_query_task.Get() )();
    } catch ( boost::thread_interrupted & ) {
      return;
    }
  }

}

void BufferIdentifiersThreadMain(
  IdentifierCompleter::BufferIdentifiersTaskStack
  &buffer_identifiers_task_stack ) {
  while ( true ) {
    try {
      ( *buffer_identifiers_task_stack.Pop() )();
    } catch ( boost::thread_interrupted & ) {
      return;
    }
  }
}


} // unnamed namespace


IdentifierCompleter::IdentifierCompleter()
  : candidate_repository_( CandidateRepository::Instance() ),
    threading_enabled_( false ) {
}


IdentifierCompleter::IdentifierCompleter(
  const std::vector< std::string > &candidates )
  : candidate_repository_( CandidateRepository::Instance() ),
    threading_enabled_( false ) {
  AddCandidatesToDatabase( candidates, "", "" );
}


IdentifierCompleter::IdentifierCompleter(
  const std::vector< std::string > &candidates,
  const std::string &filetype,
  const std::string &filepath )
  : candidate_repository_( CandidateRepository::Instance() ),
    threading_enabled_( false ) {
  AddCandidatesToDatabase( candidates, filetype, filepath );
}


IdentifierCompleter::~IdentifierCompleter() {
  query_threads_.interrupt_all();
  query_threads_.join_all();

  buffer_identifiers_thread_.interrupt();
  buffer_identifiers_thread_.join();
}


// We need this mostly so that we can not use it in tests. Apparently the
// GoogleTest framework goes apeshit on us if we enable threads by default.
void IdentifierCompleter::EnableThreading() {
  threading_enabled_ = true;
  InitThreads();
}


void IdentifierCompleter::AddCandidatesToDatabase(
  const std::vector< std::string > &new_candidates,
  const std::string &filetype,
  const std::string &filepath ) {
  std::list< const Candidate *> &candidates =
    GetCandidateList( filetype, filepath );

  std::vector< const Candidate * > repository_candidates =
    candidate_repository_.GetCandidatesForStrings( new_candidates );

  candidates.insert( candidates.end(),
                     repository_candidates.begin(),
                     repository_candidates.end() );
}


void IdentifierCompleter::AddCandidatesToDatabaseFromBuffer(
  const std::string &buffer_contents,
  const std::string &filetype,
  const std::string &filepath ) {
  ClearCandidatesStoredForFile( filetype, filepath );

  AddCandidatesToDatabase(
    ExtractIdentifiersFromText( RemoveIdentifierFreeText( buffer_contents ) ),
    filetype,
    filepath );
}


void IdentifierCompleter::AddCandidatesToDatabaseFromBufferAsync(
  std::string buffer_contents,
  std::string filetype,
  std::string filepath ) {
  // TODO: throw exception when threading is not enabled and this is called
  if ( !threading_enabled_ )
    return;

  boost::function< void() > functor =
    bind( &IdentifierCompleter::AddCandidatesToDatabaseFromBuffer,
          boost::ref( *this ),
          boost::move( buffer_contents ),
          boost::move( filetype ),
          boost::move( filepath ) );

  buffer_identifiers_task_stack_.Push(
    make_shared< packaged_task< void > >( functor ) );
}


std::vector< std::string > IdentifierCompleter::CandidatesForQuery(
  const std::string &query ) const {
  return CandidatesForQueryAndType( query, "" );
}


std::vector< std::string > IdentifierCompleter::CandidatesForQueryAndType(
  const std::string &query,
  const std::string &filetype ) const {
  std::vector< Result > results;
  ResultsForQueryAndType( query, filetype, results );

  std::vector< std::string > candidates;
  candidates.reserve( results.size() );

  foreach ( const Result & result, results ) {
    candidates.push_back( *result.Text() );
  }
  return candidates;
}


Future< AsyncResults > IdentifierCompleter::CandidatesForQueryAndTypeAsync(
  const std::string &query,
  const std::string &filetype ) const {
  // TODO: throw exception when threading is not enabled and this is called
  if ( !threading_enabled_ )
    return Future< AsyncResults >();

  FunctionReturnsStringVector functor =
    bind( &IdentifierCompleter::CandidatesForQueryAndType,
          boost::cref( *this ),
          query,
          filetype );

  QueryTask task = make_shared< packaged_task< AsyncResults > >(
                     bind( ReturnValueAsShared< std::vector< std::string > >,
                           functor ) );

  unique_future< AsyncResults > future = task->get_future();

  latest_query_task_.Set( task );
  return Future< AsyncResults >( boost::move( future ) );
}


void IdentifierCompleter::ResultsForQueryAndType(
  const std::string &query,
  const std::string &filetype,
  std::vector< Result > &results ) const {
  FiletypeMap::const_iterator it = filetype_map_.find( filetype );

  if ( it == filetype_map_.end() || query.empty() )
    return;

  Bitset query_bitset = LetterBitsetFromString( query );

  boost::unordered_set< const Candidate * > seen_candidates;
  seen_candidates.reserve( candidate_repository_.NumStoredCandidates() );

  foreach ( const FilepathToCandidates::value_type & path_and_candidates,
            *it->second ) {
    foreach ( const Candidate * candidate, *path_and_candidates.second ) {
      if ( ContainsKey( seen_candidates, candidate ) )
        continue;
      else
        seen_candidates.insert( candidate );

      if ( !candidate->MatchesQueryBitset( query_bitset ) )
        continue;

      Result result = candidate->QueryMatchResult( query );

      if ( result.IsSubsequence() )
        results.push_back( result );
    }
  }

  std::sort( results.begin(), results.end() );
}


void IdentifierCompleter::ClearCandidatesStoredForFile(
  const std::string &filetype,
  const std::string &filepath ) {
  GetCandidateList( filetype, filepath ).clear();
}


std::list< const Candidate * > &IdentifierCompleter::GetCandidateList(
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


void IdentifierCompleter::InitThreads() {
  int query_threads_to_create =
    std::max( MIN_ASYNC_THREADS,
              std::min( MAX_ASYNC_THREADS, thread::hardware_concurrency() ) );

  for ( int i = 0; i < query_threads_to_create; ++i ) {
    query_threads_.create_thread( bind( QueryThreadMain,
                                        boost::ref( latest_query_task_ ) ) );
  }

  buffer_identifiers_thread_ = boost::thread(
                                 BufferIdentifiersThreadMain,
                                 boost::ref( buffer_identifiers_task_stack_ ) );
}


} // namespace YouCompleteMe
