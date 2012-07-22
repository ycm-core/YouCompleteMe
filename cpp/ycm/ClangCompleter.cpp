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

#include "ClangCompleter.h"
#include "Candidate.h"
#include "CompletionData.h"
#include "standard.h"
#include "CandidateRepository.h"
#include "ConcurrentLatestValue.h"
#include "Utils.h"
#include "ClangUtils.h"

#include <clang-c/Index.h>
#include <boost/make_shared.hpp>

namespace fs = boost::filesystem;
using boost::packaged_task;
using boost::bind;
using boost::unique_future;
using boost::make_shared;
using boost::shared_ptr;
using boost::bind;
using boost::thread;

namespace YouCompleteMe
{

typedef boost::function< std::vector< CompletionData >() >
  FunctionReturnsCompletionDataVector;

extern const unsigned int MAX_ASYNC_THREADS;
extern const unsigned int MIN_ASYNC_THREADS;

namespace
{

struct CompletionDataAndResult
{
  CompletionDataAndResult( const CompletionData *completion_data,
                           const Result &result )
    : completion_data_( completion_data ), result_( result ) {}

  bool operator< ( const CompletionDataAndResult &other ) const
  {
    return result_ < other.result_;
  }

  const CompletionData *completion_data_;
  Result result_;
};


std::vector< CXUnsavedFile > ToCXUnsavedFiles(
    const std::vector< UnsavedFile > &unsaved_files )
{
  std::vector< CXUnsavedFile > clang_unsaved_files( unsaved_files.size() );
  for ( uint i = 0; i < unsaved_files.size(); ++i )
  {
    // TODO: assert non-null
    clang_unsaved_files[ i ].Filename = unsaved_files[ i ].filename_;
    clang_unsaved_files[ i ].Contents = unsaved_files[ i ].contents_;
    clang_unsaved_files[ i ].Length   = unsaved_files[ i ].length_;
  }

  return clang_unsaved_files;
}


std::string CXStringToString( CXString text )
{
  std::string final_string( clang_getCString( text ) );
  clang_disposeString( text );
  return final_string;
}


std::string ChunkToString( CXCompletionString completion_string, int chunk_num )
{
  return CXStringToString(
      clang_getCompletionChunkText( completion_string, chunk_num ) );
}


// Returns true when the provided completion string is available to the user;
// unavailable completion strings refer to entities that are private/protected,
// deprecated etc.
bool CompletionStringAvailable( CXCompletionString completion_string )
{
  return clang_getCompletionAvailability( completion_string ) ==
    CXAvailability_Available;
}


bool IsChunkKindForExtraMenuInfo( CXCompletionChunkKind kind )
{
  return
    kind == CXCompletionChunk_Optional     ||
    kind == CXCompletionChunk_TypedText    ||
    kind == CXCompletionChunk_Placeholder  ||
    kind == CXCompletionChunk_LeftParen    ||
    kind == CXCompletionChunk_RightParen   ||
    kind == CXCompletionChunk_RightBracket ||
    kind == CXCompletionChunk_LeftBracket  ||
    kind == CXCompletionChunk_LeftBrace    ||
    kind == CXCompletionChunk_RightBrace   ||
    kind == CXCompletionChunk_RightAngle   ||
    kind == CXCompletionChunk_LeftAngle    ||
    kind == CXCompletionChunk_Comma        ||
    kind == CXCompletionChunk_ResultType   ||
    kind == CXCompletionChunk_Colon        ||
    kind == CXCompletionChunk_SemiColon    ||
    kind == CXCompletionChunk_Equal        ||
    kind == CXCompletionChunk_HorizontalSpace;

}


char CursorKindToVimKind( CXCursorKind kind )
{
  // TODO: actually it appears that Vim will show returned kinds even when they
  // do not match the "approved" list, so let's use that
  switch ( kind )
  {
    case CXCursor_UnexposedDecl:
    case CXCursor_StructDecl:
    case CXCursor_UnionDecl:
    case CXCursor_ClassDecl:
    case CXCursor_EnumDecl:
    case CXCursor_TypedefDecl:
      return 't';

    case CXCursor_FieldDecl:
      return 'm';

    case CXCursor_FunctionDecl:
    case CXCursor_CXXMethod:
    case CXCursor_FunctionTemplate:
      return 'f';

    case CXCursor_VarDecl:
      return 'v';

    case CXCursor_MacroDefinition:
      return 'd';

    default:
      return 'u'; // for 'unknown', 'unsupported'... whatever you like
  }
}


CompletionData CompletionResultToCompletionData(
    const CXCompletionResult &completion_result )
{
  CompletionData data;
  CXCompletionString completion_string = completion_result.CompletionString;

  uint num_chunks = clang_getNumCompletionChunks( completion_string );
  for ( uint j = 0; j < num_chunks; ++j )
  {
    CXCompletionChunkKind kind = clang_getCompletionChunkKind(
        completion_string, j );

    if ( IsChunkKindForExtraMenuInfo( kind ) )
    {
      data.extra_menu_info_.append( ChunkToString( completion_string, j ) );

      // by default, there's no space after the return type
      if ( kind == CXCompletionChunk_ResultType )
        data.extra_menu_info_.append( " " );
    }

    if ( kind == CXCompletionChunk_TypedText )
      data.original_string_ = ChunkToString( completion_string, j );

    if ( kind == CXCompletionChunk_Informative )
      data.detailed_info_ = ChunkToString( completion_string, j );
  }

  data.kind_ = CursorKindToVimKind( completion_result.CursorKind );
  return data;
}


std::vector< CompletionData > ToCompletionDataVector(
    CXCodeCompleteResults *results )
{
  std::vector< CompletionData > completions;
  completions.reserve( results->NumResults );

  for ( uint i = 0; i < results->NumResults; ++i )
  {
    CXCompletionResult completion_result = results->Results[ i ];

    if ( !CompletionStringAvailable( completion_result.CompletionString ) )
      continue;

    completions.push_back(
        CompletionResultToCompletionData( completion_result ) );
  }

  return completions;
}


} // unnamed namespace


ClangCompleter::ClangCompleter()
  : candidate_repository_( CandidateRepository::Instance() ),
    threading_enabled_( false ),
    clang_data_ready_( false )
{
  clang_index_ = clang_createIndex( 0, 0 );
}


ClangCompleter::~ClangCompleter()
{
  foreach ( const TranslationUnitForFilename::value_type &filename_unit,
            filename_to_translation_unit_ )
  {
    clang_disposeTranslationUnit( filename_unit.second );
  }

  clang_disposeIndex( clang_index_ );
}


// We need this mostly so that we can not use it in tests. Apparently the
// GoogleTest framework goes apeshit on us if we enable threads by default.
void ClangCompleter::EnableThreading()
{
  threading_enabled_ = true;
  InitThreads();
}


void ClangCompleter::SetGlobalCompileFlags(
    const std::vector< std::string > &flags )
{
  global_flags_ = flags;
}


void ClangCompleter::SetFileCompileFlags(
    const std::string &filename,
    const std::vector< std::string > &flags )
{
  flags_for_file_[ filename ] =
    make_shared< std::vector< std::string > >( flags );
}


void ClangCompleter::UpdateTranslationUnit(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files )
{
  TranslationUnitForFilename::iterator it =
    filename_to_translation_unit_.find( filename );

  if ( it != filename_to_translation_unit_.end() )
  {
    std::vector< CXUnsavedFile > cxunsaved_files = ToCXUnsavedFiles(
        unsaved_files );

    clang_reparseTranslationUnit(
        it->second,
        cxunsaved_files.size(),
        &cxunsaved_files[ 0 ],
        clang_defaultEditingTranslationUnitOptions() );
  }

  else
  {
    filename_to_translation_unit_[ filename ] =
      CreateTranslationUnit( filename, unsaved_files );
  }
}


std::vector< CompletionData > ClangCompleter::CandidatesForLocationInFile(
    const std::string &filename,
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files )
{
  std::vector< CXUnsavedFile > cxunsaved_files = ToCXUnsavedFiles(
      unsaved_files );

  // codeCompleteAt reparses the TU if the underlying source file has changed on
  // disk since the last time the TU was updated and there are no unsaved files.
  // If there are unsaved files, then codeCompleteAt will parse the in-memory
  // file contents we are giving it. In short, it is NEVER a good idea to call
  // clang_reparseTranslationUnit right before a call to clang_codeCompleteAt.
  // This only makes clang reparse the whole file TWICE, which has a huge impact
  // on latency. At the time of writing, it seems that most users of libclang
  // in the open-source world don't realize this (I checked). Some don't even
  // call reparse*, but parse* which is even less efficient.

  CXCodeCompleteResults *results =
    clang_codeCompleteAt( GetTranslationUnitForFile( filename, unsaved_files ),
                          filename.c_str(),
                          line,
                          column,
                          &cxunsaved_files[ 0 ],
                          cxunsaved_files.size(),
                          clang_defaultCodeCompleteOptions());

  std::vector< CompletionData > candidates = ToCompletionDataVector( results );
  clang_disposeCodeCompleteResults( results );
  return candidates;
}


Future< AsyncCompletions >
ClangCompleter::CandidatesForQueryAndLocationInFileAsync(
    const std::string &query,
    const std::string &filename,
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files )
{
  // TODO: throw exception when threading is not enabled and this is called
  if ( !threading_enabled_ )
    return Future< AsyncCompletions >();

  if ( query.empty() )
  {
    {
      boost::lock_guard< boost::mutex > lock( clang_data_ready_mutex_ );
      clang_data_ready_ = false;
    }

    // Needed to "reset" the sorting threads to the start of their loop. This
    // way any threads blocking on a read in sorting_task_.Get() are reset to
    // wait on the clang_data_ready_condition_variable_.
    sorting_threads_.interrupt_all();
  }

  // the sorting task needs to be set before the clang task (if any) just in
  // case the clang task finishes (and therefore notifies a sorting thread to
  // consume a sorting task) before the sorting task is set

  FunctionReturnsCompletionDataVector sort_candidates_for_query_functor =
    bind( &ClangCompleter::SortCandidatesForQuery,
          boost::ref( *this ),
          query,
          boost::cref( latest_clang_results_ ) );

  shared_ptr< packaged_task< AsyncCompletions > > task =
    make_shared< packaged_task< AsyncCompletions > >(
      bind( ReturnValueAsShared< std::vector< CompletionData > >,
            sort_candidates_for_query_functor ) );

  unique_future< AsyncCompletions > future = task->get_future();
  sorting_task_.Set( task );

  if ( query.empty() )
  {
    FunctionReturnsCompletionDataVector
      candidates_for_location_in_file_functor =
      bind( &ClangCompleter::CandidatesForLocationInFile,
            boost::ref( *this ),
            filename,
            line,
            column,
            unsaved_files );

    shared_ptr< packaged_task< AsyncCompletions > > task =
      make_shared< packaged_task< AsyncCompletions > >(
        bind( ReturnValueAsShared< std::vector< CompletionData > >,
              candidates_for_location_in_file_functor ) );

    clang_task_.Set( task );
  }

  return Future< AsyncCompletions >( boost::move( future ) );
}


CXTranslationUnit ClangCompleter::CreateTranslationUnit(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files )
{
  std::vector< const char* > flags = FlagsForFilename( filename );
  flags.reserve( flags.size() + global_flags_.size() );

  foreach ( const std::string &flag, global_flags_ )
  {
    flags.push_back( flag.c_str() );
  }

  std::vector< CXUnsavedFile > cxunsaved_files = ToCXUnsavedFiles(
      unsaved_files );

  return clang_parseTranslationUnit(
      clang_index_,
      filename.c_str(),
      &flags[ 0 ],
      flags.size(),
      &cxunsaved_files[ 0 ],
      cxunsaved_files.size(),
      clang_defaultEditingTranslationUnitOptions() );
}


// The implementation of this function is somewhat non-obvious because we need
// to make sure that the data pointed to by the const char* pointers returned
// outlives this function. We want to make sure that we are calling c_str on the
// string objects that are actually stored in flags_for_file_
std::vector< const char* > ClangCompleter::FlagsForFilename(
    const std::string &filename)
{
  FlagsForFile::iterator it =
    flags_for_file_.find( filename );

  if ( it == flags_for_file_.end() )
  {
    flags_for_file_[ filename ] = make_shared< std::vector< std::string > >(
        SanitizeClangFlags(
            SplitFlags(
                GetNearestClangOptions( filename ) ) ) );

    it = flags_for_file_.find( filename );
  }

  // TODO: assert it != end

  std::vector< const char* > flags;
  foreach ( const std::string &flag, *it->second )
  {
    flags.push_back( flag.c_str() );
  }

  return flags;
}


CXTranslationUnit ClangCompleter::GetTranslationUnitForFile(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files )
{
  TranslationUnitForFilename::iterator it =
    filename_to_translation_unit_.find( filename );

  if ( it != filename_to_translation_unit_.end() )
    return it->second;

  CXTranslationUnit unit = CreateTranslationUnit( filename, unsaved_files );
  filename_to_translation_unit_[ filename ] = unit;
  return unit;
}


std::vector< CompletionData > ClangCompleter::SortCandidatesForQuery(
    const std::string &query,
    const std::vector< CompletionData > &completion_datas )
{
  Bitset query_bitset = LetterBitsetFromString( query );

  std::vector< const Candidate* > repository_candidates =
    candidate_repository_.GetCandidatesForStrings( completion_datas );

  std::vector< CompletionDataAndResult > data_and_results;

  for ( uint i = 0; i < repository_candidates.size(); ++i )
  {
    const Candidate* candidate = repository_candidates[ i ];
    if ( !candidate->MatchesQueryBitset( query_bitset ) )
      continue;

    Result result = candidate->QueryMatchResult( query );
    if ( result.IsSubsequence() )
    {
      CompletionDataAndResult data_and_result( &completion_datas[ i ], result );
      data_and_results.push_back( data_and_result );
    }
  }

  std::sort( data_and_results.begin(), data_and_results.end() );

  std::vector< CompletionData > sorted_completion_datas;
  sorted_completion_datas.reserve( data_and_results.size() );

  foreach ( const CompletionDataAndResult& data_and_result, data_and_results )
  {
    sorted_completion_datas.push_back( *data_and_result.completion_data_ );
  }

  return sorted_completion_datas;
}


void ClangCompleter::InitThreads()
{
  int threads_to_create =
    std::max( MIN_ASYNC_THREADS,
      std::min( MAX_ASYNC_THREADS, thread::hardware_concurrency() ) );

  for ( int i = 0; i < threads_to_create; ++i )
  {
    sorting_threads_.create_thread(
        bind( &ClangCompleter::SortingThreadMain,
              boost::ref( *this ),
              boost::ref( sorting_task_ ) ) );
  }

  clang_thread_ = boost::thread( &ClangCompleter::ClangThreadMain,
                                 boost::ref( *this ),
                                 boost::ref( clang_task_ ) );
}


void ClangCompleter::ClangThreadMain( LatestTask &clang_task )
{
  while ( true )
  {
    shared_ptr< packaged_task< AsyncCompletions > > task = clang_task.Get();
    ( *task )();
    unique_future< AsyncCompletions > future = task->get_future();

    {
      boost::unique_lock< boost::shared_mutex > writer_lock(
          latest_clang_results_shared_mutex_ );
      latest_clang_results_ = *future.get();
    }

    {
      boost::lock_guard< boost::mutex > lock( clang_data_ready_mutex_ );
      clang_data_ready_ = true;
    }

    clang_data_ready_condition_variable_.notify_all();
  }
}


void ClangCompleter::SortingThreadMain( LatestTask &sorting_task )
{
  while ( true )
  {
    try
    {
      {
        boost::unique_lock< boost::mutex > lock( clang_data_ready_mutex_ );

        while ( !clang_data_ready_ )
        {
          clang_data_ready_condition_variable_.wait( lock );
        }
      }

      shared_ptr< packaged_task< AsyncCompletions > > task = sorting_task.Get();

      {
        boost::shared_lock< boost::shared_mutex > reader_lock(
            latest_clang_results_shared_mutex_ );

        ( *task )();
      }
    }

    catch ( boost::thread_interrupted& )
    {
      // Do nothing and re-enter the loop
    }
  }
}


} // namespace YouCompleteMe
