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

#ifndef CLANGUTILS_H_9MVHQLJS
#define CLANGUTILS_H_9MVHQLJS

#include <vector>
#include <string>

namespace YouCompleteMe
{

// TODO: move most of the anon funcs in ClangCompleter.cpp to here
// TODO: remove these functions

// Removes flags that are either unnecessary or cause clang to crash
std::vector< std::string > SanitizeClangFlags(
    const std::vector< std::string > &flags );

std::vector< std::string > SplitFlags( const std::string &flags_string );

std::string GetNearestClangOptions( const std::string &filename );

} // namespace YouCompleteMe

#endif /* end of include guard: CLANGUTILS_H_9MVHQLJS */

