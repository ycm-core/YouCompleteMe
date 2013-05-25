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

#ifndef COMPLETER_H_7AR4UGXE
#define COMPLETER_H_7AR4UGXE

#include "ConcurrentLatestValue.h"
#include "ConcurrentStack.h"
#include "IdentifierDatabase.h"
#include "Future.h"

#include <boost/utility.hpp>
#include <boost/unordered_map.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/scoped_ptr.hpp>

#include <vector>
#include <string>


namespace YouCompleteMe {

class Candidate;

typedef boost::shared_ptr< std::vector< std::string > > AsyncResults;


class IdentifierCompleter : boost::noncopyable {
public:
  IdentifierCompleter();
  IdentifierCompleter( const std::vector< std::string > &candidates );
  IdentifierCompleter( const std::vector< std::string > &candidates,
                       const std::string &filetype,
                       const std::string &filepath );

  ~IdentifierCompleter();

  void EnableThreading();

  void AddCandidatesToDatabase(
    const std::vector< std::string > &new_candidates,
    const std::string &filetype,
    const std::string &filepath );

  void AddCandidatesToDatabaseFromBuffer(
    const std::string &buffer_contents,
    const std::string &filetype,
    const std::string &filepath,
    bool collect_from_comments_and_strings );

  // NOTE: params are taken by value on purpose! With a C++11 compiler we can
  // avoid an expensive copy of buffer_contents if the param is taken by value
  // (move ctors FTW)
  void AddCandidatesToDatabaseFromBufferAsync(
    std::string buffer_contents,
    std::string filetype,
    std::string filepath,
    bool collect_from_comments_and_strings );

  // Only provided for tests!
  std::vector< std::string > CandidatesForQuery(
    const std::string &query ) const;

  std::vector< std::string > CandidatesForQueryAndType(
    const std::string &query,
    const std::string &filetype ) const;

  Future< AsyncResults > CandidatesForQueryAndTypeAsync(
    const std::string &query,
    const std::string &filetype ) const;

  typedef boost::shared_ptr <
  boost::packaged_task< AsyncResults > > QueryTask;

  typedef ConcurrentLatestValue< QueryTask > LatestQueryTask;

  typedef ConcurrentStack< VoidTask > BufferIdentifiersTaskStack;

private:

  void InitThreads();


  /////////////////////////////
  // PRIVATE MEMBER VARIABLES
  /////////////////////////////

  IdentifierDatabase identifier_database_;

  bool threading_enabled_;

  boost::thread_group query_threads_;

  boost::scoped_ptr< boost::thread > buffer_identifiers_thread_;

  mutable LatestQueryTask latest_query_task_;

  BufferIdentifiersTaskStack buffer_identifiers_task_stack_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: COMPLETER_H_7AR4UGXE */
