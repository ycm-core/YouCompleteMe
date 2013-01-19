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

#ifndef COMPILATIONDATABASE_H_ZT7MQXPG
#define COMPILATIONDATABASE_H_ZT7MQXPG

#include <vector>
#include <string>
#include <boost/utility.hpp>
#include <clang-c/CXCompilationDatabase.h>

namespace YouCompleteMe
{

class CompilationDatabase : boost::noncopyable
{
public:
  CompilationDatabase( const std::string& path_to_directory );
  ~CompilationDatabase();

  bool DatabaseSuccessfullyLoaded();

  std::vector< std::string > FlagsForFile( const std::string &path_to_file );

  std::string CompileCommandWorkingDirectoryForFile(
      const std::string &path_to_file );

private:
  bool is_loaded_;
  CXCompilationDatabase compilation_database_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: COMPILATIONDATABASE_H_ZT7MQXPG */
