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

// TODO: remove all explicit uses of the boost:: prefix by adding explicit using
// directives for the stuff we need
namespace fs = boost::filesystem;
using boost::packaged_task;
using boost::bind;
using boost::unique_future;
using boost::make_shared;
using boost::shared_ptr;
using boost::bind;
using boost::thread;
using boost::lock_guard;
using boost::unique_lock;
using boost::mutex;
using boost::unordered_map;

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


char DiagnosticSeverityToType( CXDiagnosticSeverity severity )
{
  switch ( severity )
  {
    case CXDiagnostic_Ignored:
    case CXDiagnostic_Note:
      return 'I';

    case CXDiagnostic_Warning:
      return 'W';

    case CXDiagnostic_Error:
    case CXDiagnostic_Fatal:
      return 'E';

    default:
      return 'E';
  }
}


// TODO: this should be a constructor
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

  unordered_map< std::string, uint > seen_data;

  for ( uint i = 0; i < results->NumResults; ++i )
  {
    CXCompletionResult completion_result = results->Results[ i ];

    if ( !CompletionStringAvailable( completion_result.CompletionString ) )
      continue;

    CompletionData data = CompletionResultToCompletionData( completion_result );
    uint index = GetValueElseInsert( seen_data,
                                     data.original_string_,
                                     completions.size() );

    if ( index == completions.size() )
    {
      completions.push_back( data );
    }

    else
    {
      completions[ index ].detailed_info_
        .append( "\n" )
        .append( data.extra_menu_info_ );
    }
  }

  return completions;
}


Diagnostic CXDiagnosticToDiagnostic( CXDiagnostic cxdiagnostic )
{
  Diagnostic diagnostic;
  diagnostic.kind_ = DiagnosticSeverityToType(
      clang_getDiagnosticSeverity( cxdiagnostic ) );

  // If this is an "ignored" diagnostic, there's no point in continuing since we
  // won't display those to the user
  if ( diagnostic.kind_ == 'I' )
    return diagnostic;

  CXSourceLocation location = clang_getDiagnosticLocation( cxdiagnostic );
  CXFile file;
  uint unused_offset;
  clang_getSpellingLocation( location,
                             &file,
                             &diagnostic.line_number_,
                             &diagnostic.column_number_,
                             &unused_offset );
  diagnostic.filename_ = CXStringToString( clang_getFileName( file ) );
  diagnostic.text_ = CXStringToString(
      clang_getDiagnosticSpelling( cxdiagnostic ) );

  clang_disposeDiagnostic( cxdiagnostic );
  return diagnostic;
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


std::vector< Diagnostic > ClangCompleter::DiagnosticsForFile(
    const std::string &filename )
{
  std::vector< Diagnostic > diagnostics;
  unique_lock< mutex > lock( file_parse_task_mutex_, boost::try_to_lock_t );
  if ( !lock.owns_lock() )
    return diagnostics;

  CXTranslationUnit unit = FindWithDefault( filename_to_translation_unit_,
                                            filename,
                                            NULL );
  if ( !unit )
    return diagnostics;

  uint num_diagnostics = clang_getNumDiagnostics( unit );
  diagnostics.reserve( num_diagnostics );

  for ( uint i = 0; i < num_diagnostics; ++i )
  {
    Diagnostic diagnostic = CXDiagnosticToDiagnostic(
        clang_getDiagnostic( unit, i ) );

    if ( diagnostic.kind_ != 'I' )
      diagnostics.push_back( diagnostic );
  }

  return diagnostics;
}


bool ClangCompleter::UpdatingTranslationUnit()
{
  lock_guard< mutex > lock( file_parse_task_mutex_ );
  return bool( file_parse_task_ );
}


void ClangCompleter::UpdateTranslationUnit(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags )
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
      CreateTranslationUnit( filename, unsaved_files, flags );
  }
}


void ClangCompleter::UpdateTranslationUnitAsync(
    std::string filename,
    std::vector< UnsavedFile > unsaved_files,
    std::vector< std::string > flags )
{
  boost::function< void() > functor =
    bind( &ClangCompleter::UpdateTranslationUnit,
          boost::ref( *this ),
          boost::move( filename ),
          boost::move( unsaved_files ),
          boost::move( flags ) );

  boost::lock_guard< boost::mutex > lock( file_parse_task_mutex_ );

  // Only ever set the task when it's NULL; if it's not, that means that the
  // clang thread is working on it
  if ( file_parse_task_ )
    return;

  file_parse_task_ = make_shared< packaged_task< void > >( functor );
  file_parse_task_condition_variable_.notify_all();
}


std::vector< CompletionData > ClangCompleter::CandidatesForLocationInFile(
    const std::string &filename,
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags )
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
    clang_codeCompleteAt( GetTranslationUnitForFile( filename,
                                                     unsaved_files,
                                                     flags ),
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
    std::string query,
    std::string filename,
    int line,
    int column,
    std::vector< UnsavedFile > unsaved_files,
    std::vector< std::string > flags )
{
  // TODO: throw exception when threading is not enabled and this is called
  if ( !threading_enabled_ )
    return Future< AsyncCompletions >();

  if ( query.empty() )
  {
    // The clang thread is busy, return nothing
    if ( UpdatingTranslationUnit() )
      return Future< AsyncCompletions >();

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
            boost::move( filename ),
            line,
            column,
            boost::move( unsaved_files ),
            boost::move( flags ) );

    shared_ptr< packaged_task< AsyncCompletions > > task =
      make_shared< packaged_task< AsyncCompletions > >(
        bind( ReturnValueAsShared< std::vector< CompletionData > >,
              candidates_for_location_in_file_functor ) );

    clang_completions_task_.Set( task );
  }

  return Future< AsyncCompletions >( boost::move( future ) );
}


CXTranslationUnit ClangCompleter::CreateTranslationUnit(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags )
{
  std::vector< const char* > pointer_flags;
  pointer_flags.reserve( flags.size() );

  foreach ( const std::string &flag, flags )
  {
    pointer_flags.push_back( flag.c_str() );
  }

  std::vector< CXUnsavedFile > cxunsaved_files = ToCXUnsavedFiles(
      unsaved_files );

  CXTranslationUnit unit = clang_parseTranslationUnit(
      clang_index_,
      filename.c_str(),
      &pointer_flags[ 0 ],
      pointer_flags.size(),
      &cxunsaved_files[ 0 ],
      cxunsaved_files.size(),
      clang_defaultEditingTranslationUnitOptions() );

  // Only with a reparse is the preable precompiled. I do not know why...
  // TODO: report this bug on the clang tracker
  clang_reparseTranslationUnit(
      unit,
      cxunsaved_files.size(),
      &cxunsaved_files[ 0 ],
      clang_defaultEditingTranslationUnitOptions() );

  return unit;
}


CXTranslationUnit ClangCompleter::GetTranslationUnitForFile(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags )
{
  TranslationUnitForFilename::iterator it =
    filename_to_translation_unit_.find( filename );

  if ( it != filename_to_translation_unit_.end() )
    return it->second;

  CXTranslationUnit unit = CreateTranslationUnit( filename,
                                                  unsaved_files,
                                                  flags );
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
              boost::ref( *this ) ) );
  }

  clang_completions_thread_ = boost::thread(
      &ClangCompleter::ClangCompletionsThreadMain,
      boost::ref( *this ) );

  file_parse_thread_ = boost::thread(
      &ClangCompleter::FileParseThreadMain,
      boost::ref( *this ) );
}


void ClangCompleter::FileParseThreadMain()
{
  while ( true )
  {
    {
      boost::unique_lock< boost::mutex > lock( file_parse_task_mutex_ );

      while ( !file_parse_task_ )
      {
        file_parse_task_condition_variable_.wait( lock );
      }
    }

    ( *file_parse_task_ )();

    lock_guard< mutex > lock( file_parse_task_mutex_ );
    file_parse_task_ = VoidTask();
  }
}


void ClangCompleter::ClangCompletionsThreadMain()
{
  while ( true )
  {
    // TODO: this should be a separate func, much like the file_parse_task_ part
    shared_ptr< packaged_task< AsyncCompletions > > task =
      clang_completions_task_.Get();

    // If the file parse thread is accessing clang by parsing a file, then drop
    // the current completion request
    {
      lock_guard< mutex > lock( file_parse_task_mutex_ );
      if ( file_parse_task_ )
        continue;
    }

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


void ClangCompleter::SortingThreadMain()
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

      shared_ptr< packaged_task< AsyncCompletions > > task =
        sorting_task_.Get();

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
