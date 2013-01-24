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

#include "Future.h"
#include "ConcurrentStack.h"

#include <vector>
#include <string>
#include <boost/utility.hpp>
#include <boost/shared_ptr.hpp>
#include <clang-c/CXCompilationDatabase.h>

namespace YouCompleteMe {

struct CompilationInfoForFile {
  std::vector< std::string > compiler_flags_;
  std::string compiler_working_dir_;
};

typedef boost::shared_ptr< CompilationInfoForFile >
AsyncCompilationInfoForFile;

class CompilationDatabase : boost::noncopyable {
public:
  CompilationDatabase( const std::string &path_to_directory );
  ~CompilationDatabase();

  bool DatabaseSuccessfullyLoaded();

  void EnableThreading();

  CompilationInfoForFile GetCompilationInfoForFile(
      const std::string &path_to_file );

  Future< AsyncCompilationInfoForFile > GetCompilationInfoForFileAsync(
      const std::string &path_to_file );

  typedef boost::shared_ptr <
  boost::packaged_task< AsyncCompilationInfoForFile > > InfoTask;

  typedef ConcurrentStack< InfoTask > InfoTaskStack;

private:
  void InitThreads();

  bool threading_enabled_;
  bool is_loaded_;
  CXCompilationDatabase compilation_database_;

  boost::thread info_thread_;
  InfoTaskStack info_task_stack_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: COMPILATIONDATABASE_H_ZT7MQXPG */
