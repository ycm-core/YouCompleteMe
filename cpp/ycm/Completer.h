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

#include "Candidate.h"
#include "ConcurrentStack.h"
#include "Future.h"

#include <boost/utility.hpp>
#include <boost/python.hpp>
#include <boost/unordered_map.hpp>
#include <boost/shared_ptr.hpp>

#include <vector>
#include <string>


namespace YouCompleteMe
{

typedef boost::python::list Pylist;

// candidate text string -> candidate objects
typedef boost::unordered_map< std::string, const Candidate* >
          CandidateRepository;

// filepath -> *( *candidate )
typedef boost::unordered_map< std::string,
          boost::shared_ptr< std::list< const Candidate* > > >
            FilepathToCandidates;

// filetype -> *( filepath -> *( *candidate ) )
typedef boost::unordered_map< std::string,
          boost::shared_ptr< FilepathToCandidates > > FiletypeMap;

typedef ConcurrentStack<
          boost::shared_ptr<
            boost::packaged_task< AsyncResults > > > TaskStack;


class Completer : boost::noncopyable
{
public:
  Completer() {}
  Completer( const std::vector< std::string > &candidates );
  Completer( const std::vector< std::string > &candidates,
             const std::string &filetype,
             const std::string &filepath );
  ~Completer();

  void EnableThreading();

  void AddCandidatesToDatabase(
      const std::vector< std::string > &new_candidates,
      const std::string &filetype,
      const std::string &filepath );

  void AddCandidatesToDatabase( const Pylist &new_candidates,
                                const std::string &filetype,
                                const std::string &filepath );

  // Only provided for tests!
	std::vector< std::string > CandidatesForQuery(
	    const std::string &query ) const;

  std::vector< std::string > CandidatesForQueryAndType(
      const std::string &query,
      const std::string &filetype ) const;

	Future CandidatesForQueryAndTypeAsync( const std::string &query,
                                         const std::string &filetype ) const;

private:

  AsyncResults ResultsForQueryAndType( const std::string &query,
                                       const std::string &filetype ) const;

  void ResultsForQueryAndType( const std::string &query,
                               const std::string &filetype,
                               std::vector< Result > &results ) const;

  std::list< const Candidate* >& GetCandidateList(
      const std::string &filetype,
      const std::string &filepath );

  void InitThreads();


  /////////////////////////////
  // PRIVATE MEMBER VARIABLES
  /////////////////////////////

  // This data structure owns all the Candidate pointers
  CandidateRepository candidate_repository_;

  FiletypeMap filetype_map_;

  mutable TaskStack task_stack_;

  bool threading_enabled_;

  boost::thread_group threads_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: COMPLETER_H_7AR4UGXE */
