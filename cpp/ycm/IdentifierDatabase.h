// Copyright (C) 2013  Google Inc.
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

#ifndef IDENTIFIERDATABASE_H_ZESX3CVR
#define IDENTIFIERDATABASE_H_ZESX3CVR

#include <boost/utility.hpp>
#include <boost/unordered_map.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/shared_ptr.hpp>

#include <vector>
#include <string>
#include <map>
#include <set>

namespace YouCompleteMe {

class Candidate;
class Result;
class CandidateRepository;


// filepath -> identifiers
typedef std::map< std::string, std::vector< std::string > >
FilepathToIdentifiers;

// filetype -> (filepath -> identifiers)
typedef std::map< std::string, FilepathToIdentifiers >
FiletypeIdentifierMap;


// This class stores the database of identifiers the identifier completer has
// seen. It stores them in a data structure that makes it easy to tell which
// identifier came from which file and what files have which filetypes.
//
// The main point of this class is to isolate the parts of the code that need
// access to this internal data structure so that it's easier to confirm that
// mutexes are used correctly to protect concurrent access.
//
// This class is thread-safe.
class IdentifierDatabase : boost::noncopyable {
public:
  IdentifierDatabase();

  void AddIdentifiers( const FiletypeIdentifierMap &filetype_identifier_map );

  void AddIdentifiers(
    const std::vector< std::string > &new_candidates,
    const std::string &filetype,
    const std::string &filepath );

  void ClearCandidatesStoredForFile( const std::string &filetype,
                                     const std::string &filepath );

  void ResultsForQueryAndType( const std::string &query,
                               const std::string &filetype,
                               std::vector< Result > &results ) const;

private:
  std::set< const Candidate * > &GetCandidateSet(
    const std::string &filetype,
    const std::string &filepath );

  void AddIdentifiersNoLock(
    const std::vector< std::string > &new_candidates,
    const std::string &filetype,
    const std::string &filepath );


  // filepath -> *( *candidate )
  typedef boost::unordered_map < std::string,
          boost::shared_ptr< std::set< const Candidate * > > >
          FilepathToCandidates;

  // filetype -> *( filepath -> *( *candidate ) )
  typedef boost::unordered_map < std::string,
          boost::shared_ptr< FilepathToCandidates > > FiletypeCandidateMap;


  CandidateRepository &candidate_repository_;

  FiletypeCandidateMap filetype_candidate_map_;
  mutable boost::mutex filetype_candidate_map_mutex_;
};

} // namespace YouCompleteMe


#endif /* end of include guard: IDENTIFIERDATABASE_H_ZESX3CVR */

