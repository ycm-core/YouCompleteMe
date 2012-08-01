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

#ifndef CLANGCOMPLETE_H_WLKDU0ZV
#define CLANGCOMPLETE_H_WLKDU0ZV

#include "ConcurrentLatestValue.h"
#include "Future.h"
#include "UnsavedFile.h"
#include "Diagnostic.h"

#include <boost/utility.hpp>
#include <boost/unordered_map.hpp>

#include <string>

typedef void *CXIndex;
typedef struct CXTranslationUnitImpl *CXTranslationUnit;

namespace YouCompleteMe
{

class CandidateRepository;
struct CompletionData;

typedef boost::shared_ptr< std::vector< CompletionData > > AsyncCompletions;

typedef boost::unordered_map< std::string,
          boost::shared_ptr<
            std::vector< std::string > > > FlagsForFile;

typedef boost::unordered_map< std::string, CXTranslationUnit >
  TranslationUnitForFilename;


// TODO: document that all filename parameters must be absolute paths
class ClangCompleter : boost::noncopyable
{
public:
  ClangCompleter();
  ~ClangCompleter();

  void EnableThreading();

  std::vector< Diagnostic > DiagnosticsForFile( const std::string &filename );

  bool UpdatingTranslationUnit();

  void UpdateTranslationUnit( const std::string &filename,
                              const std::vector< UnsavedFile > &unsaved_files,
                              const std::vector< std::string > &flags );

  // NOTE: params are taken by value on purpose! With a C++11 compiler we can
  // avoid internal copies if params are taken by value (move ctors FTW)
  void UpdateTranslationUnitAsync(
      std::string filename,
      std::vector< UnsavedFile > unsaved_files,
      std::vector< std::string > flags );

  std::vector< CompletionData > CandidatesForLocationInFile(
      const std::string &filename,
      int line,
      int column,
      const std::vector< UnsavedFile > &unsaved_files,
      const std::vector< std::string > &flags );

  // NOTE: params are taken by value on purpose! With a C++11 compiler we can
  // avoid internal copies if params are taken by value (move ctors FTW)
  Future< AsyncCompletions > CandidatesForQueryAndLocationInFileAsync(
      std::string query,
      std::string filename,
      int line,
      int column,
      std::vector< UnsavedFile > unsaved_files,
      std::vector< std::string > flags );

private:
  typedef ConcurrentLatestValue<
            boost::shared_ptr<
              boost::packaged_task< AsyncCompletions > > > LatestTask;

  // caller takes ownership of translation unit
  CXTranslationUnit CreateTranslationUnit(
      const std::string &filename,
      const std::vector< UnsavedFile > &unsaved_files,
      const std::vector< std::string > &flags );

  CXTranslationUnit GetTranslationUnitForFile(
      const std::string &filename,
      const std::vector< UnsavedFile > &unsaved_files,
      const std::vector< std::string > &flags );

  std::vector< CompletionData > SortCandidatesForQuery(
      const std::string &query,
      const std::vector< CompletionData > &completion_datas );

  void InitThreads();

  void FileParseThreadMain();

  void ClangCompletionsThreadMain();

  void SortingThreadMain();


  /////////////////////////////
  // PRIVATE MEMBER VARIABLES
  /////////////////////////////

  CXIndex clang_index_;

  TranslationUnitForFilename filename_to_translation_unit_;

  CandidateRepository &candidate_repository_;

  // TODO: move everything thread-related into a separated helper class
  mutable LatestTask clang_completions_task_;

  mutable LatestTask sorting_task_;

  // Only the clang thread can make this NULL and only the GUI thread can make
  // it non-NULL. The file_parse_task_mutex_ is used before checking the state
  // of NULL. [ NULL for a shared_ptr naturally means default-constructed
  // shared_ptr]
  VoidTask file_parse_task_;
  boost::mutex file_parse_task_mutex_;
  boost::condition_variable file_parse_task_condition_variable_;

  bool threading_enabled_;

  // TODO: use boost.atomic for clang_data_ready_
  bool clang_data_ready_;
  boost::mutex clang_data_ready_mutex_;
  boost::condition_variable clang_data_ready_condition_variable_;

  std::vector< CompletionData > latest_clang_results_;
  boost::shared_mutex latest_clang_results_shared_mutex_;

  // Unfortunately clang is not thread-safe so we need to be careful when we
  // access it. Only one thread at a time is allowed to access any single
  // translation unit.
  boost::thread clang_completions_thread_;

  boost::thread file_parse_thread_;

  boost::thread_group sorting_threads_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: CLANGCOMPLETE_H_WLKDU0ZV */
