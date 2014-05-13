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

#ifndef IDENTIFIERUTILS_CPP_WFFUZNET
#define IDENTIFIERUTILS_CPP_WFFUZNET

#include "IdentifierDatabase.h"

#include <vector>
#include <string>

#include <boost/filesystem.hpp>

namespace YouCompleteMe {

// NOTE: this function accepts the text param by value on purpose; it internally
// needs a copy before processing the text so the copy might as well be made on
// the parameter BUT if this code is compiled in C++11 mode a move constructor
// can be called on the passed-in value. This is not possible if we accept the
// param by const ref.
std::string RemoveIdentifierFreeText( std::string text );

std::vector< std::string > ExtractIdentifiersFromText(
  const std::string &text );

FiletypeIdentifierMap ExtractIdentifiersFromTagsFile(
  const boost::filesystem::path &path_to_tag_file );

} // namespace YouCompleteMe

#endif /* end of include guard: IDENTIFIERUTILS_CPP_WFFUZNET */
