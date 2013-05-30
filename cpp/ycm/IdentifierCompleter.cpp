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

#include "Candidate.h"
#include "IdentifierUtils.h"
#include "Result.h"
#include "Utils.h"

#include <boost/bind.hpp>
#include <boost/make_shared.hpp>
#include <algorithm>

using boost::packaged_task;
using boost::unique_future;
using boost::shared_ptr;
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
  : threading_enabled_( false ) {
}


IdentifierCompleter::IdentifierCompleter(
  const std::vector< std::string > &candidates )
  : threading_enabled_( false ) {
  identifier_database_.AddIdentifiers( candidates, "", "" );
}


IdentifierCompleter::IdentifierCompleter(
  const std::vector< std::string > &candidates,
  const std::string &filetype,
  const std::string &filepath )
  : threading_enabled_( false ) {
  identifier_database_.AddIdentifiers( candidates, filetype, filepath );
}


IdentifierCompleter::~IdentifierCompleter() {
  query_threads_.interrupt_all();
  query_threads_.join_all();

  if ( buffer_identifiers_thread_ ) {
    buffer_identifiers_thread_->interrupt();
    buffer_identifiers_thread_->join();
  }
}


// We need this mostly so that we can not use it in tests. Apparently the
// GoogleTest framework goes apeshit on us if we enable threads by default.
void IdentifierCompleter::EnableThreading() {
  threading_enabled_ = true;
  InitThreads();
}


void IdentifierCompleter::AddIdentifiersToDatabase(
  const std::vector< std::string > &new_candidates,
  const std::string &filetype,
  const std::string &filepath ) {
  identifier_database_.AddIdentifiers( new_candidates,
                                       filetype,
                                       filepath );
}


void IdentifierCompleter::AddIdentifiersToDatabaseFromTagFiles(
  const std::vector< std::string > &absolute_paths_to_tag_files ) {
  foreach( const std::string & path, absolute_paths_to_tag_files ) {
    identifier_database_.AddIdentifiers(
      ExtractIdentifiersFromTagsFile( path ) );
  }
}


void IdentifierCompleter::AddIdentifiersToDatabaseFromTagFilesAsync(
  std::vector< std::string > absolute_paths_to_tag_files ) {
  // TODO: throw exception when threading is not enabled and this is called
  if ( !threading_enabled_ )
    return;

  boost::function< void() > functor =
    boost::bind( &IdentifierCompleter::AddIdentifiersToDatabaseFromTagFiles,
                 boost::ref( *this ),
                 boost::move( absolute_paths_to_tag_files ) );

  buffer_identifiers_task_stack_.Push(
    boost::make_shared< packaged_task< void > >( boost::move( functor ) ) );
}


void IdentifierCompleter::AddIdentifiersToDatabaseFromBuffer(
  const std::string &buffer_contents,
  const std::string &filetype,
  const std::string &filepath,
  bool collect_from_comments_and_strings ) {
  identifier_database_.ClearCandidatesStoredForFile( filetype, filepath );

  std::string new_contents =
    collect_from_comments_and_strings ?
    buffer_contents :
    RemoveIdentifierFreeText( buffer_contents );

  identifier_database_.AddIdentifiers(
    ExtractIdentifiersFromText( new_contents ),
    filetype,
    filepath );
}


void IdentifierCompleter::AddIdentifiersToDatabaseFromBufferAsync(
  std::string buffer_contents,
  std::string filetype,
  std::string filepath,
  bool collect_from_comments_and_strings ) {
  // TODO: throw exception when threading is not enabled and this is called
  if ( !threading_enabled_ )
    return;

  boost::function< void() > functor =
    boost::bind( &IdentifierCompleter::AddIdentifiersToDatabaseFromBuffer,
                 boost::ref( *this ),
                 boost::move( buffer_contents ),
                 boost::move( filetype ),
                 boost::move( filepath ),
                 collect_from_comments_and_strings );

  buffer_identifiers_task_stack_.Push(
    boost::make_shared< packaged_task< void > >( boost::move( functor ) ) );
}


std::vector< std::string > IdentifierCompleter::CandidatesForQuery(
  const std::string &query ) const {
  return CandidatesForQueryAndType( query, "" );
}


std::vector< std::string > IdentifierCompleter::CandidatesForQueryAndType(
  const std::string &query,
  const std::string &filetype ) const {
  std::vector< Result > results;
  identifier_database_.ResultsForQueryAndType( query, filetype, results );

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
    boost::bind( &IdentifierCompleter::CandidatesForQueryAndType,
                 boost::cref( *this ),
                 query,
                 filetype );

  QueryTask task =
    boost::make_shared< packaged_task< AsyncResults > >(
      boost::bind( ReturnValueAsShared< std::vector< std::string > >,
                   boost::move( functor ) ) );

  unique_future< AsyncResults > future = task->get_future();

  latest_query_task_.Set( task );
  return Future< AsyncResults >( boost::move( future ) );
}


void IdentifierCompleter::InitThreads() {
  int query_threads_to_create =
    std::max( MIN_ASYNC_THREADS,
              std::min( MAX_ASYNC_THREADS, thread::hardware_concurrency() ) );

  for ( int i = 0; i < query_threads_to_create; ++i ) {
    query_threads_.create_thread(
      boost::bind( QueryThreadMain,
                   boost::ref( latest_query_task_ ) ) );
  }

  buffer_identifiers_thread_.reset(
    new boost::thread( BufferIdentifiersThreadMain,
                       boost::ref( buffer_identifiers_task_stack_ ) ) );
}


} // namespace YouCompleteMe
