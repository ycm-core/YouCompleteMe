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

#ifndef TESTUTILS_H_G4RKMGUD
#define TESTUTILS_H_G4RKMGUD

#include <vector>
#include <string>

#include <boost/filesystem.hpp>

namespace YouCompleteMe {

std::vector< std::string > StringVector( const std::string &a,
                                         const std::string &b = std::string(),
                                         const std::string &c = std::string(),
                                         const std::string &d = std::string(),
                                         const std::string &e = std::string(),
                                         const std::string &f = std::string(),
                                         const std::string &g = std::string(),
                                         const std::string &h = std::string(),
                                         const std::string &i = std::string() );

boost::filesystem::path PathToTestFile( const std::string &filepath );

} // namespace YouCompleteMe

#endif /* end of include guard: TESTUTILS_H_G4RKMGUD */

