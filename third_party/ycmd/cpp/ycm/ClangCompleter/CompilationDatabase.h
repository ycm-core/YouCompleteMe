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

#ifndef COMPILATIONDATABASE_H_ZT7MQXPG
#define COMPILATIONDATABASE_H_ZT7MQXPG

#include <vector>
#include <string>
#include <boost/utility.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/thread/mutex.hpp>
#include <clang-c/CXCompilationDatabase.h>


namespace YouCompleteMe {

struct CompilationInfoForFile {
  std::vector< std::string > compiler_flags_;
  std::string compiler_working_dir_;
};


// Access to Clang's internal CompilationDatabase. This class is thread-safe.
class CompilationDatabase : boost::noncopyable {
public:
  CompilationDatabase( const std::string &path_to_directory );
  ~CompilationDatabase();

  bool DatabaseSuccessfullyLoaded();

  // Returns true when a separate thread is already getting flags; this is
  // useful so that the caller doesn't need to block.
  bool AlreadyGettingFlags();

  // NOTE: Multiple calls to this function from separate threads will be
  // serialized since Clang internals are not thread-safe.
  CompilationInfoForFile GetCompilationInfoForFile(
    const std::string &path_to_file );

private:

  bool is_loaded_;
  CXCompilationDatabase compilation_database_;
  boost::mutex compilation_database_mutex_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: COMPILATIONDATABASE_H_ZT7MQXPG */
