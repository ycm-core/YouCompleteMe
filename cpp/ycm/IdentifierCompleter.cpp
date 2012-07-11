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
#include "Utils.h"

#include <boost/bind.hpp>
#include <boost/make_shared.hpp>
#include <algorithm>

using boost::python::len;
using boost::python::extract;
using boost::packaged_task;
using boost::bind;
using boost::unique_future;
using boost::make_shared;
using boost::shared_ptr;
using boost::bind;
using boost::thread;

namespace YouCompleteMe
{

namespace
{

const unsigned int MAX_ASYNC_THREADS = 4;
const unsigned int MIN_ASYNC_THREADS = 2;

void ThreadMain( LatestTask &latest_task )
{
  while ( true )
  {
    ( *latest_task.Get() )();
  }
}

} // unnamed namespace


IdentifierCompleter::IdentifierCompleter(
    const std::vector< std::string > &candidates )
  : threading_enabled_( false )
{
  AddCandidatesToDatabase( candidates, "", "", true );
}


IdentifierCompleter::IdentifierCompleter(
    const std::vector< std::string > &candidates,
    const std::string &filetype,
    const std::string &filepath )
  : threading_enabled_( false )
{
  AddCandidatesToDatabase( candidates, filetype, filepath, true );
}


IdentifierCompleter::~IdentifierCompleter()
{
  foreach ( const CandidateRepository::value_type &pair,
            candidate_repository_ )
  {
    delete pair.second;
  }
}


// We need this mostly so that we can not use it in tests. Apparently the
// GoogleTest framework goes apeshit on us if we enable threads by default.
void IdentifierCompleter::EnableThreading()
{
  threading_enabled_ = true;
  InitThreads();
}


void IdentifierCompleter::AddCandidatesToDatabase(
    const std::vector< std::string > &new_candidates,
    const std::string &filetype,
    const std::string &filepath,
    bool clear_database )
{
  std::list< const Candidate *> &candidates =
    GetCandidateList( filetype, filepath );

  if ( clear_database )
    candidates.clear();

  foreach ( const std::string &candidate_text, new_candidates )
  {
    const Candidate *&candidate = GetValueElseInsert( candidate_repository_,
                                                      candidate_text, NULL );
    if ( !candidate )
      candidate = new Candidate( candidate_text );

    candidates.push_back( candidate );
  }
}


std::vector< std::string > IdentifierCompleter::CandidatesForQuery(
    const std::string &query ) const
{
  return CandidatesForQueryAndType( query, "" );
}


std::vector< std::string > IdentifierCompleter::CandidatesForQueryAndType(
    const std::string &query,
    const std::string &filetype ) const
{
  std::vector< Result > results;
  ResultsForQueryAndType( query, filetype, results );

  std::vector< std::string > candidates;
  foreach ( const Result& result, results )
  {
    candidates.push_back( *result.Text() );
  }
  return candidates;
}


Future IdentifierCompleter::CandidatesForQueryAndTypeAsync(
    const std::string &query,
    const std::string &filetype ) const
{
  // TODO: throw exception when threading is not enabled and this is called
  if (!threading_enabled_)
    return Future();

  // Try not to look at this too hard, it may burn your eyes.
  shared_ptr< packaged_task< AsyncResults > > task =
    make_shared< packaged_task< AsyncResults > >(
      bind( &IdentifierCompleter::ResultsForQueryAndType,
            boost::cref( *this ),
            query,
            filetype ) );

  unique_future< AsyncResults > future = task->get_future();

  latest_task_.Set( task );
  return Future( move( future ) );
}


AsyncResults IdentifierCompleter::ResultsForQueryAndType(
    const std::string &query,
    const std::string &filetype ) const
{
  AsyncResults results = boost::make_shared< std::vector< Result > >();
  ResultsForQueryAndType( query, filetype, *results );
  return results;
}


void IdentifierCompleter::ResultsForQueryAndType(
    const std::string &query,
    const std::string &filetype,
    std::vector< Result > &results ) const
{
  FiletypeMap::const_iterator it = filetype_map_.find( filetype );
  if ( it == filetype_map_.end() )
    return;

  Bitset query_bitset = LetterBitsetFromString( query );

  foreach ( const FilepathToCandidates::value_type &path_and_candidates,
            *it->second )
  {
    foreach ( const Candidate* candidate, *path_and_candidates.second )
    {
      if ( !candidate->MatchesQueryBitset( query_bitset ) )
        continue;

      Result result = candidate->QueryMatchResult( query );
      if ( result.IsSubsequence() )
        results.push_back( result );
    }
  }

  std::sort( results.begin(), results.end() );
}


std::list< const Candidate* >& IdentifierCompleter::GetCandidateList(
    const std::string &filetype,
    const std::string &filepath )
{
  boost::shared_ptr< FilepathToCandidates > &path_to_candidates =
    filetype_map_[ filetype ];

  if ( !path_to_candidates )
    path_to_candidates.reset( new FilepathToCandidates() );

  boost::shared_ptr< std::list< const Candidate* > > &candidates =
    (*path_to_candidates)[ filepath ];

  if ( !candidates )
    candidates.reset( new std::list< const Candidate* >() );

  return *candidates;
}


void IdentifierCompleter::InitThreads()
{
  int threads_to_create =
    std::max( MIN_ASYNC_THREADS,
      std::min( MAX_ASYNC_THREADS, thread::hardware_concurrency() ) );

  for ( int i = 0; i < threads_to_create; ++i )
  {
    threads_.create_thread( bind( ThreadMain, boost::ref( latest_task_ ) ) );
  }
}


} // namespace YouCompleteMe
