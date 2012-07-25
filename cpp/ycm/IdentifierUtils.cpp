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

#include "IdentifierUtils.h"
#include "standard.h"

#include <boost/regex.hpp>
#include <boost/algorithm/string/regex.hpp>

namespace YouCompleteMe
{

const char* COMMENT_AND_STRING_REGEX =
  "//.*?$" // Anything following '//'
  "|"
  "#.*?$"  // Anything following '#'
  "|"
  "/\\*.*?\\*/"  // C-style comments, '/* ... */'
  "|"
  "'[^']*'" // Anything inside single quotes, '...'
  "|"
  "\"[^\"]*\""; // Anything inside double quotes, "..."

const char* IDENTIFIER_REGEX = "[_a-zA-Z]\\w*";


std::string RemoveIdentifierFreeText( std::string text )
{
  boost::erase_all_regex( text, boost::regex( COMMENT_AND_STRING_REGEX ) );
  return text;
}


std::vector< std::string > ExtractIdentifiersFromText(
    const std::string &text )
{
  std::string::const_iterator start = text.begin();
  std::string::const_iterator end   = text.end();

  boost::match_results< std::string::const_iterator > matches;
  boost::regex expression( IDENTIFIER_REGEX );

  std::vector< std::string > identifiers;
  while ( boost::regex_search( start, end, matches, expression ) )
  {
    identifiers.push_back( matches[ 0 ] );
    start = matches[ 0 ].second;
  }

  return identifiers;
}

} // namespace YouCompleteMe
