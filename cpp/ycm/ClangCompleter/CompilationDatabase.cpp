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

#include "CompilationDatabase.h"
#include "ClangUtils.h"
#include "standard.h"

#include <boost/shared_ptr.hpp>
#include <boost/type_traits/remove_pointer.hpp>

using boost::shared_ptr;
using boost::shared_ptr;
using boost::remove_pointer;

namespace YouCompleteMe {
typedef shared_ptr<
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


std::vector< std::string > CompilationDatabase::FlagsForFile(
  const std::string &path_to_file ) {
  std::vector< std::string > flags;

  if ( !is_loaded_ )
    return flags;

  CompileCommandsWrap commands(
    clang_CompilationDatabase_getCompileCommands(
      compilation_database_,
      path_to_file.c_str() ), clang_CompileCommands_dispose );

  uint num_commands = clang_CompileCommands_getSize( commands.get() );

  if ( num_commands < 1 ) {
    return flags;
  }

  // We always pick the first command offered
  CXCompileCommand command = clang_CompileCommands_getCommand(
                               commands.get(),
                               0 );

  uint num_flags = clang_CompileCommand_getNumArgs( command );
  flags.reserve( num_flags );

  for ( uint i = 0; i < num_flags; ++i ) {
    flags.push_back( CXStringToString(
                       clang_CompileCommand_getArg( command, i ) ) );
  }

  return flags;
}


std::string CompilationDatabase::CompileCommandWorkingDirectoryForFile(
  const std::string &path_to_file ) {
  std::string path_to_directory;

  if ( !is_loaded_ )
    return path_to_directory;

  CompileCommandsWrap commands(
    clang_CompilationDatabase_getCompileCommands(
      compilation_database_,
      path_to_file.c_str() ), clang_CompileCommands_dispose );

  uint num_commands = clang_CompileCommands_getSize( commands.get() );

  if ( num_commands < 1 ) {
    return path_to_directory;
  }

  // We always pick the first command offered
  CXCompileCommand command = clang_CompileCommands_getCommand(
                               commands.get(),
                               0 );

  path_to_directory = CXStringToString( clang_CompileCommand_getDirectory(
                                          command ) );

  return path_to_directory;
}

} // namespace YouCompleteMe

