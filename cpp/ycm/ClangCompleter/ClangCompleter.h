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
#include "ConcurrentStack.h"
#include "Future.h"
#include "UnsavedFile.h"
#include "Diagnostic.h"
#include "ClangResultsCache.h"
#include "TranslationUnitStore.h"

#include <boost/utility.hpp>
#include <boost/thread/future.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/unordered_map.hpp>

#include <string>

typedef struct CXTranslationUnitImpl *CXTranslationUnit;

namespace YouCompleteMe {

class CandidateRepository;
class TranslationUnit;
struct CompletionData;
struct Location;

typedef std::vector< CompletionData > CompletionDatas;

typedef boost::shared_ptr< CompletionDatas > AsyncCompletions;

typedef boost::unordered_map < std::string,
        boost::shared_ptr <
        std::vector< std::string > > > FlagsForFile;


// TODO: document that all filename parameters must be absolute paths
class ClangCompleter : boost::noncopyable {
public:
  ClangCompleter();
  ~ClangCompleter();

  void EnableThreading();

  std::vector< Diagnostic > DiagnosticsForFile( const std::string &filename );

  bool UpdatingTranslationUnit( const std::string &filename );

  // Public because of unit tests (gtest is not very thread-friendly)
  void UpdateTranslationUnit(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags );

  // NOTE: params are taken by value on purpose! With a C++11 compiler we can
  // avoid internal copies if params are taken by value (move ctors FTW)
  Future< void > UpdateTranslationUnitAsync(
    std::string filename,
    std::vector< UnsavedFile > unsaved_files,
    std::vector< std::string > flags );

  // Public because of unit tests (gtest is not very thread-friendly)
  std::vector< CompletionData > CandidatesForLocationInFile(
    const std::string &filename,
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags );

  Future< AsyncCompletions > CandidatesForQueryAndLocationInFileAsync(
    const std::string &query,
    const std::string &filename,
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags );

  Location GetDeclarationLocation(
    const std::string &filename,
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags );

  Location GetDefinitionLocation(
    const std::string &filename,
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags );

  void DeleteCachesForFileAsync( const std::string &filename );

private:

  void DeleteCaches();

  // This is basically a union. Only one of the two tasks is set to something
  // valid, the other task is invalid. Which one is valid depends on the caller.
  struct ClangPackagedTask {
    boost::packaged_task< AsyncCompletions > completions_task_;
    boost::packaged_task< void > parsing_task_;
  };

  typedef ConcurrentLatestValue <
  boost::shared_ptr <
  boost::packaged_task< AsyncCompletions > > > LatestSortingTask;

  typedef ConcurrentLatestValue <
  boost::shared_ptr< ClangPackagedTask > > LatestClangTask;

  typedef ConcurrentStack< std::string > FileCacheDeleteStack;

  bool ShouldSkipClangResultCache( const std::string &query,
                                   int line,
                                   int column );

  void CreateSortingTask( const std::string &query,
                          boost::unique_future< AsyncCompletions > &future );

  // NOTE: params are taken by value on purpose! With a C++11 compiler we can
  // avoid internal copies if params are taken by value (move ctors FTW)
  void CreateClangTask(
    std::string filename,
    int line,
    int column,
    std::vector< UnsavedFile > unsaved_files,
    std::vector< std::string > flags );

  std::vector< CompletionData > SortCandidatesForQuery(
    const std::string &query,
    const std::vector< CompletionData > &completion_datas );

  void InitThreads();

  void ClangThreadMain();

  void SortingThreadMain();


  /////////////////////////////
  // PRIVATE MEMBER VARIABLES
  /////////////////////////////

  CXIndex clang_index_;

  TranslationUnitStore translation_unit_store_;

  CandidateRepository &candidate_repository_;

  bool threading_enabled_;

  // TODO: use boost.atomic for time_to_die_
  bool time_to_die_;
  boost::shared_mutex time_to_die_mutex_;

  // TODO: use boost.atomic for clang_data_ready_
  bool clang_data_ready_;
  boost::mutex clang_data_ready_mutex_;
  boost::condition_variable clang_data_ready_condition_variable_;

  ClangResultsCache latest_clang_results_;

  FileCacheDeleteStack file_cache_delete_stack_;

  // Unfortunately clang is not thread-safe so we need to be careful when we
  // access it. Only one thread at a time is allowed to access any single
  // translation unit. Currently we only use one thread to access clang and that
  // is the thread represented by clang_thread_.
  boost::scoped_ptr< boost::thread > clang_thread_;

  boost::thread_group sorting_threads_;

  mutable LatestClangTask clang_task_;

  mutable LatestSortingTask sorting_task_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: CLANGCOMPLETE_H_WLKDU0ZV */
