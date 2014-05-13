// Copyright (C) 2011, 2012  Google Inc.
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

#include "IdentifierDatabase.h"

#include <boost/utility.hpp>
#include <boost/unordered_map.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/scoped_ptr.hpp>

#include <vector>
#include <string>


namespace YouCompleteMe {

class Candidate;


class IdentifierCompleter : boost::noncopyable {
public:
  IdentifierCompleter();
  IdentifierCompleter( const std::vector< std::string > &candidates );
  IdentifierCompleter( const std::vector< std::string > &candidates,
                       const std::string &filetype,
                       const std::string &filepath );

  void AddIdentifiersToDatabase(
    const std::vector< std::string > &new_candidates,
    const std::string &filetype,
    const std::string &filepath );

  void AddIdentifiersToDatabaseFromTagFiles(
    const std::vector< std::string > &absolute_paths_to_tag_files );

  void AddIdentifiersToDatabaseFromBuffer(
    const std::string &buffer_contents,
    const std::string &filetype,
    const std::string &filepath,
    bool collect_from_comments_and_strings );

  // Only provided for tests!
  std::vector< std::string > CandidatesForQuery(
    const std::string &query ) const;

  std::vector< std::string > CandidatesForQueryAndType(
    const std::string &query,
    const std::string &filetype ) const;

private:

  /////////////////////////////
  // PRIVATE MEMBER VARIABLES
  /////////////////////////////

  IdentifierDatabase identifier_database_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: COMPLETER_H_7AR4UGXE */
