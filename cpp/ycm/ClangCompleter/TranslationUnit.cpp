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

#include "TranslationUnit.h"
#include "CompletionData.h"
#include "standard.h"
#include "exceptions.h"
#include "ClangUtils.h"
#include "ClangHelpers.h"

#include <boost/shared_ptr.hpp>
#include <boost/type_traits/remove_pointer.hpp>

using boost::unique_lock;
using boost::mutex;
using boost::try_to_lock_t;
using boost::shared_ptr;
using boost::remove_pointer;

namespace YouCompleteMe {

namespace {

unsigned editingOptions() {
  return CXTranslationUnit_DetailedPreprocessingRecord |
      clang_defaultEditingTranslationUnitOptions();
}

}  // unnamed namespace

typedef shared_ptr <
remove_pointer< CXCodeCompleteResults >::type > CodeCompleteResultsWrap;

TranslationUnit::TranslationUnit()
  : filename_( "" ),
    clang_translation_unit_( NULL ) {
}

TranslationUnit::TranslationUnit(
  const std::string &filename,
  const std::vector< UnsavedFile > &unsaved_files,
  const std::vector< std::string > &flags,
  CXIndex clang_index )
  : filename_( filename ),
    clang_translation_unit_( NULL ) {
  std::vector< const char * > pointer_flags;
  pointer_flags.reserve( flags.size() );

  foreach ( const std::string & flag, flags ) {
    pointer_flags.push_back( flag.c_str() );
  }

  std::vector< CXUnsavedFile > cxunsaved_files =
    ToCXUnsavedFiles( unsaved_files );
  const CXUnsavedFile *unsaved = cxunsaved_files.size() > 0
                                 ? &cxunsaved_files[ 0 ] : NULL;

  clang_translation_unit_ = clang_parseTranslationUnit(
                              clang_index,
                              filename.c_str(),
                              &pointer_flags[ 0 ],
                              pointer_flags.size(),
                              const_cast<CXUnsavedFile *>( unsaved ),
                              cxunsaved_files.size(),
                              editingOptions() );

  if ( !clang_translation_unit_ )
    boost_throw( ClangParseError() );

  // Only with a reparse is the preable precompiled. I do not know why...
  // TODO: report this bug on the clang tracker
  Reparse( cxunsaved_files );
}


TranslationUnit::~TranslationUnit() {
  Destroy();
}

void TranslationUnit::Destroy() {
  unique_lock< mutex > lock( clang_access_mutex_ );

  if ( clang_translation_unit_ ) {
    clang_disposeTranslationUnit( clang_translation_unit_ );
    clang_translation_unit_ = NULL;
  }
}


std::vector< Diagnostic > TranslationUnit::LatestDiagnostics() {
  if ( !clang_translation_unit_ )
    return std::vector< Diagnostic >();

  unique_lock< mutex > lock( diagnostics_mutex_ );
  return latest_diagnostics_;
}


bool TranslationUnit::IsCurrentlyUpdating() const {
  // We return true when the TU is invalid; an invalid TU also acts a sentinel,
  // preventing other threads from trying to use it.
  if ( !clang_translation_unit_ )
    return true;

  unique_lock< mutex > lock( clang_access_mutex_, try_to_lock_t() );
  return !lock.owns_lock();
}


std::vector< Diagnostic > TranslationUnit::Reparse(
  const std::vector< UnsavedFile > &unsaved_files ) {
  std::vector< CXUnsavedFile > cxunsaved_files =
    ToCXUnsavedFiles( unsaved_files );

  Reparse( cxunsaved_files );

  unique_lock< mutex > lock( diagnostics_mutex_ );
  return latest_diagnostics_;
}


void TranslationUnit::ReparseForIndexing(
  const std::vector< UnsavedFile > &unsaved_files ) {
  std::vector< CXUnsavedFile > cxunsaved_files =
    ToCXUnsavedFiles( unsaved_files );

  Reparse( cxunsaved_files,
           CXTranslationUnit_PrecompiledPreamble |
           CXTranslationUnit_SkipFunctionBodies );
}


std::vector< CompletionData > TranslationUnit::CandidatesForLocation(
  int line,
  int column,
  const std::vector< UnsavedFile > &unsaved_files ) {
  unique_lock< mutex > lock( clang_access_mutex_ );

  if ( !clang_translation_unit_ )
    return std::vector< CompletionData >();

  std::vector< CXUnsavedFile > cxunsaved_files =
    ToCXUnsavedFiles( unsaved_files );
  const CXUnsavedFile *unsaved = cxunsaved_files.size() > 0
                                 ? &cxunsaved_files[ 0 ] : NULL;

  // codeCompleteAt reparses the TU if the underlying source file has changed on
  // disk since the last time the TU was updated and there are no unsaved files.
  // If there are unsaved files, then codeCompleteAt will parse the in-memory
  // file contents we are giving it. In short, it is NEVER a good idea to call
  // clang_reparseTranslationUnit right before a call to clang_codeCompleteAt.
  // This only makes clang reparse the whole file TWICE, which has a huge impact
  // on latency. At the time of writing, it seems that most users of libclang
  // in the open-source world don't realize this (I checked). Some don't even
  // call reparse*, but parse* which is even less efficient.

  CodeCompleteResultsWrap results(
    clang_codeCompleteAt( clang_translation_unit_,
                          filename_.c_str(),
                          line,
                          column,
                          const_cast<CXUnsavedFile *>( unsaved ),
                          cxunsaved_files.size(),
                          clang_defaultCodeCompleteOptions() ),
    clang_disposeCodeCompleteResults );

  std::vector< CompletionData > candidates = ToCompletionDataVector(
                                               results.get() );
  return candidates;
}

Location TranslationUnit::GetDeclarationLocation(
  int line,
  int column,
  const std::vector< UnsavedFile > &unsaved_files,
  bool reparse ) {
  if (reparse)
    ReparseForIndexing( unsaved_files );
  unique_lock< mutex > lock( clang_access_mutex_ );

  if ( !clang_translation_unit_ )
    return Location();

  CXCursor cursor = GetCursor( line, column );

  if ( !CursorIsValid( cursor ) )
    return Location();

  CXCursor referenced_cursor = clang_getCursorReferenced( cursor );

  if ( !CursorIsValid( referenced_cursor ) )
    return Location();

  return Location( clang_getCursorLocation( referenced_cursor ) );
}

Location TranslationUnit::GetDefinitionLocation(
  int line,
  int column,
  const std::vector< UnsavedFile > &unsaved_files,
  bool reparse ) {
  if (reparse)
    ReparseForIndexing( unsaved_files );
  unique_lock< mutex > lock( clang_access_mutex_ );

  if ( !clang_translation_unit_ )
    return Location();

  CXCursor cursor = GetCursor( line, column );

  if ( !CursorIsValid( cursor ) )
    return Location();

  CXCursor definition_cursor = clang_getCursorDefinition( cursor );

  if ( !CursorIsValid( definition_cursor ) )
    return Location();

  return Location( clang_getCursorLocation( definition_cursor ) );
}


// Argument taken as non-const ref because we need to be able to pass a
// non-const pointer to clang. This function (and clang too) will not modify the
// param though.
void TranslationUnit::Reparse(
  std::vector< CXUnsavedFile > &unsaved_files ) {
  Reparse( unsaved_files, editingOptions() );
}


// Argument taken as non-const ref because we need to be able to pass a
// non-const pointer to clang. This function (and clang too) will not modify the
// param though.
void TranslationUnit::Reparse( std::vector< CXUnsavedFile > &unsaved_files,
                               uint parse_options ) {
  int failure = 0;
  {
    unique_lock< mutex > lock( clang_access_mutex_ );

    if ( !clang_translation_unit_ )
      return;

    CXUnsavedFile *unsaved = unsaved_files.size() > 0
                             ? &unsaved_files[ 0 ] : NULL;

    failure = clang_reparseTranslationUnit( clang_translation_unit_,
                                            unsaved_files.size(),
                                            unsaved,
                                            parse_options );
  }

  if ( failure ) {
    Destroy();
    boost_throw( ClangParseError() );
  }

  UpdateLatestDiagnostics();
}


void TranslationUnit::UpdateLatestDiagnostics() {
  unique_lock< mutex > lock1( clang_access_mutex_ );
  unique_lock< mutex > lock2( diagnostics_mutex_ );

  latest_diagnostics_.clear();
  uint num_diagnostics = clang_getNumDiagnostics( clang_translation_unit_ );
  latest_diagnostics_.reserve( num_diagnostics );

  for ( uint i = 0; i < num_diagnostics; ++i ) {
    Diagnostic diagnostic =
      BuildDiagnostic(
        DiagnosticWrap( clang_getDiagnostic( clang_translation_unit_, i ),
                        clang_disposeDiagnostic ),
        clang_translation_unit_ );

    if ( diagnostic.kind_ != 'I' )
      latest_diagnostics_.push_back( diagnostic );
  }
}

CXCursor TranslationUnit::GetCursor( int line, int column ) {
  // ASSUMES A LOCK IS ALREADY HELD ON clang_access_mutex_!
  if ( !clang_translation_unit_ )
    return clang_getNullCursor();

  CXFile file = clang_getFile( clang_translation_unit_, filename_.c_str() );
  CXSourceLocation source_location = clang_getLocation(
                                       clang_translation_unit_,
                                       file,
                                       line,
                                       column );

  return clang_getCursor( clang_translation_unit_, source_location );
}

} // namespace YouCompleteMe
