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

#include "IdentifierCompleter.h"
#include "standard.h"

#include "Candidate.h"
#include "IdentifierUtils.h"
#include "Result.h"
#include "Utils.h"
#include "ReleaseGil.h"

#include <algorithm>

namespace YouCompleteMe {


IdentifierCompleter::IdentifierCompleter() {}


IdentifierCompleter::IdentifierCompleter(
  const std::vector< std::string > &candidates ) {
  identifier_database_.AddIdentifiers( candidates, "", "" );
}


IdentifierCompleter::IdentifierCompleter(
  const std::vector< std::string > &candidates,
  const std::string &filetype,
  const std::string &filepath ) {
  identifier_database_.AddIdentifiers( candidates, filetype, filepath );
}


void IdentifierCompleter::AddIdentifiersToDatabase(
  const std::vector< std::string > &new_candidates,
  const std::string &filetype,
  const std::string &filepath ) {
  ReleaseGil unlock;
  identifier_database_.AddIdentifiers( new_candidates,
                                       filetype,
                                       filepath );
}


void IdentifierCompleter::AddIdentifiersToDatabaseFromTagFiles(
  const std::vector< std::string > &absolute_paths_to_tag_files ) {
  ReleaseGil unlock;
  foreach( const std::string & path, absolute_paths_to_tag_files ) {
    identifier_database_.AddIdentifiers(
      ExtractIdentifiersFromTagsFile( path ) );
  }
}


void IdentifierCompleter::AddIdentifiersToDatabaseFromBuffer(
  const std::string &buffer_contents,
  const std::string &filetype,
  const std::string &filepath,
  bool collect_from_comments_and_strings ) {
  ReleaseGil unlock;
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


std::vector< std::string > IdentifierCompleter::CandidatesForQuery(
  const std::string &query ) const {
  return CandidatesForQueryAndType( query, "" );
}


std::vector< std::string > IdentifierCompleter::CandidatesForQueryAndType(
  const std::string &query,
  const std::string &filetype ) const {
  ReleaseGil unlock;
  std::vector< Result > results;
  identifier_database_.ResultsForQueryAndType( query, filetype, results );

  std::vector< std::string > candidates;
  candidates.reserve( results.size() );

  foreach ( const Result & result, results ) {
    candidates.push_back( *result.Text() );
  }
  return candidates;
}


} // namespace YouCompleteMe
