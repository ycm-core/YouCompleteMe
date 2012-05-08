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

void ThreadMain( TaskStack &task_stack )
{
  while ( true )
  {
    ( *task_stack.Pop() )();
  }
}

} // unnamed namespace


Completer::Completer( const std::vector< std::string > &candidates )
  : threading_enabled_( false )
{
  AddCandidatesToDatabase( candidates, "", "" );
}


Completer::Completer( const std::vector< std::string > &candidates,
                      const std::string &filetype,
                      const std::string &filepath )
  : threading_enabled_( false )
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


// We need this mostly so that we can not use it in tests. Apparently the
// GoogleTest framework goes apeshit on us if we enable threads by default.
void Completer::EnableThreading()
{
  threading_enabled_ = true;
  InitThreads();
}


void Completer::AddCandidatesToDatabase( const Pylist &new_candidates,
                                         const std::string &filetype,
                                         const std::string &filepath )
{
  int num_candidates = len( new_candidates );
  std::vector< std::string > candidates;
  candidates.reserve( num_candidates );

  for (int i = 0; i < num_candidates; ++i)
  {
    candidates.push_back( extract< std::string >( new_candidates[ i ] ) );
  }

  AddCandidatesToDatabase( candidates, filetype, filepath );
}


void Completer::AddCandidatesToDatabase(
    const std::vector< std::string > &new_candidates,
    const std::string &filetype,
    const std::string &filepath )
{
  std::vector< const Candidate *> &candidates =
    GetCandidateVector( filetype, filepath );

  int num_candidates = new_candidates.size();
  candidates.clear();
  candidates.reserve( num_candidates );

  for (int i = 0; i < num_candidates; ++i)
  {
    const std::string &candidate_text = new_candidates[ i ];
    const Candidate *&candidate = GetValueElseInsert( candidate_repository_,
                                                      candidate_text, NULL );
    if ( !candidate )
      candidate = new Candidate( candidate_text );

    candidates.push_back( candidate );
  }
}


std::vector< std::string > Completer::CandidatesForQuery(
    const std::string &query ) const
{
  return CandidatesForQueryAndType( query, "" );
}


std::vector< std::string > Completer::CandidatesForQueryAndType(
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


Future Completer::CandidatesForQueryAndTypeAsync(
    const std::string &query,
    const std::string &filetype ) const
{
  // TODO: throw exception when threading is not enabled and this is called
  if (!threading_enabled_)
    return Future();

  // Try not to look at this too hard, it may burn your eyes.
  shared_ptr< packaged_task< AsyncResults > > task =
    make_shared< packaged_task< AsyncResults > >(
      bind( &Completer::ResultsForQueryAndType,
                   boost::cref( *this ),
                   query,
                   filetype ) );

  unique_future< AsyncResults > future = task->get_future();

  task_stack_.Push( task );
  return Future( move( future ) );
}


AsyncResults Completer::ResultsForQueryAndType(
    const std::string &query,
    const std::string &filetype ) const
{
  AsyncResults results = boost::make_shared< std::vector< Result > >();
  ResultsForQueryAndType( query, filetype, *results );
  return results;
}


void Completer::ResultsForQueryAndType( const std::string &query,
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


std::vector< const Candidate* >& Completer::GetCandidateVector(
    const std::string &filetype,
    const std::string &filepath )
{
  boost::shared_ptr< FilepathToCandidates > &path_to_candidates =
    filetype_map_[ filetype ];

  if ( !path_to_candidates )
    path_to_candidates.reset( new FilepathToCandidates() );

  boost::shared_ptr< std::vector< const Candidate* > > &candidates =
    (*path_to_candidates)[ filepath ];

  if ( !candidates )
    candidates.reset( new std::vector< const Candidate* >() );

  return *candidates;
}


void Completer::InitThreads()
{
  int threads_to_create =
    std::max( MIN_ASYNC_THREADS,
      std::min( MAX_ASYNC_THREADS, thread::hardware_concurrency() ) );

  for ( int i = 0; i < threads_to_create; ++i )
  {
    threads_.create_thread( bind( ThreadMain, boost::ref( task_stack_ ) ) );
  }
}


} // namespace YouCompleteMe
