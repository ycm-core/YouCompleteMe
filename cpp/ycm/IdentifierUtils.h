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

#ifndef IDENTIFIERUTILS_CPP_WFFUZNET
#define IDENTIFIERUTILS_CPP_WFFUZNET

#include <vector>
#include <string>

namespace YouCompleteMe
{

std::string RemoveIdentifierFreeText( const std::string &text );

std::vector< std::string > ExtractIdentifiersFromText(
    const std::string &text );

} // namespace YouCompleteMe

#endif /* end of include guard: IDENTIFIERUTILS_CPP_WFFUZNET */
