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

#include "CompilationDatabase.h"
#include "ClangUtils.h"
#include "standard.h"
#include "ReleaseGil.h"

#include <boost/shared_ptr.hpp>
#include <boost/make_shared.hpp>
#include <boost/type_traits/remove_pointer.hpp>
#include <boost/thread/locks.hpp>

using boost::lock_guard;
using boost::unique_lock;
using boost::try_to_lock_t;
using boost::remove_pointer;
using boost::shared_ptr;
using boost::mutex;

namespace YouCompleteMe {

typedef shared_ptr <
remove_pointer< CXCompileCommands >::type > CompileCommandsWrap;


CompilationDatabase::CompilationDatabase(
  const std::string &path_to_directory )
  : is_loaded_( false ) {
  CXCompilationDatabase_Error status;
  compilation_database_ = clang_CompilationDatabase_fromDirectory(
                            path_to_directory.c_str(),
                            &status );
  is_loaded_ = status == CXCompilationDatabase_NoError;
}


CompilationDatabase::~CompilationDatabase() {
  clang_CompilationDatabase_dispose( compilation_database_ );
}


bool CompilationDatabase::DatabaseSuccessfullyLoaded() {
  return is_loaded_;
}


bool CompilationDatabase::AlreadyGettingFlags() {
  unique_lock< mutex > lock( compilation_database_mutex_, try_to_lock_t() );
  return !lock.owns_lock();
}


CompilationInfoForFile CompilationDatabase::GetCompilationInfoForFile(
  const std::string &path_to_file ) {
  ReleaseGil unlock;
  CompilationInfoForFile info;

  if ( !is_loaded_ )
    return info;

  lock_guard< mutex > lock( compilation_database_mutex_ );

  CompileCommandsWrap commands(
    clang_CompilationDatabase_getCompileCommands(
      compilation_database_,
      path_to_file.c_str() ), clang_CompileCommands_dispose );

  uint num_commands = clang_CompileCommands_getSize( commands.get() );

  if ( num_commands < 1 ) {
    return info;
  }

  // We always pick the first command offered
  CXCompileCommand command = clang_CompileCommands_getCommand(
                               commands.get(),
                               0 );

  info.compiler_working_dir_ = CXStringToString(
                                 clang_CompileCommand_getDirectory( command ) );

  uint num_flags = clang_CompileCommand_getNumArgs( command );
  info.compiler_flags_.reserve( num_flags );

  for ( uint i = 0; i < num_flags; ++i ) {
    info.compiler_flags_.push_back(
      CXStringToString( clang_CompileCommand_getArg( command, i ) ) );
  }

  return info;
}

} // namespace YouCompleteMe

