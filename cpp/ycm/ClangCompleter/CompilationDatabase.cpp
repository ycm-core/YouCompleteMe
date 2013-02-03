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
#include <boost/bind.hpp>
#include <boost/make_shared.hpp>
#include <boost/type_traits/remove_pointer.hpp>

using boost::bind;
using boost::make_shared;
using boost::packaged_task;
using boost::remove_pointer;
using boost::shared_ptr;
using boost::thread;
using boost::unique_future;
using boost::function;

namespace YouCompleteMe {

typedef shared_ptr <
remove_pointer< CXCompileCommands >::type > CompileCommandsWrap;


void QueryThreadMain( CompilationDatabase::InfoTaskStack &info_task_stack ) {
  while ( true ) {
    try {
      ( *info_task_stack.Pop() )();
    } catch ( boost::thread_interrupted & ) {
      return;
    }
  }

}


CompilationDatabase::CompilationDatabase(
  const std::string &path_to_directory )
  : threading_enabled_( false ),
    is_loaded_( false ) {
  CXCompilationDatabase_Error status;
  compilation_database_ = clang_CompilationDatabase_fromDirectory(
                            path_to_directory.c_str(),
                            &status );
  is_loaded_ = status == CXCompilationDatabase_NoError;
}


CompilationDatabase::~CompilationDatabase() {
  clang_CompilationDatabase_dispose( compilation_database_ );
}


// We need this mostly so that we can not use it in tests. Apparently the
// GoogleTest framework goes apeshit on us if we enable threads by default.
void CompilationDatabase::EnableThreading() {
  threading_enabled_ = true;
  InitThreads();
}


bool CompilationDatabase::DatabaseSuccessfullyLoaded() {
  return is_loaded_;
}


CompilationInfoForFile CompilationDatabase::GetCompilationInfoForFile(
  const std::string &path_to_file ) {
  CompilationInfoForFile info;

  if ( !is_loaded_ )
    return info;

  // TODO: mutex protect calls to getCompileCommands and getDirectory

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


Future< AsyncCompilationInfoForFile >
CompilationDatabase::GetCompilationInfoForFileAsync(
  const std::string &path_to_file ) {
  // TODO: throw exception when threading is not enabled and this is called
  if ( !threading_enabled_ )
    return Future< AsyncCompilationInfoForFile >();

  function< CompilationInfoForFile() > functor =
    bind( &CompilationDatabase::GetCompilationInfoForFile,
          boost::ref( *this ),
          path_to_file );

  InfoTask task =
    make_shared< packaged_task< AsyncCompilationInfoForFile > >(
      bind( ReturnValueAsShared< CompilationInfoForFile >,
            functor ) );

  unique_future< AsyncCompilationInfoForFile > future = task->get_future();
  info_task_stack_.Push( task );
  return Future< AsyncCompilationInfoForFile >( boost::move( future ) );
}


void CompilationDatabase::InitThreads() {
  info_thread_ = boost::thread( QueryThreadMain,
                                boost::ref( info_task_stack_ ) );
}

} // namespace YouCompleteMe

