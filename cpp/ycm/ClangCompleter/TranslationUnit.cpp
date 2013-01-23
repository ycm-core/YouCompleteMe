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

#include "TranslationUnit.h"
#include "CompletionData.h"
#include "standard.h"
#include "exceptions.h"
#include "ClangUtils.h"

#include <clang-c/Index.h>
#include <boost/shared_ptr.hpp>
#include <boost/type_traits/remove_pointer.hpp>

using boost::unique_lock;
using boost::mutex;
using boost::try_to_lock_t;
using boost::shared_ptr;
using boost::remove_pointer;

namespace YouCompleteMe {

typedef shared_ptr<
  remove_pointer< CXCodeCompleteResults >::type > CodeCompleteResultsWrap;

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

  clang_translation_unit_ = clang_parseTranslationUnit(
                              clang_index,
                              filename.c_str(),
                              &pointer_flags[ 0 ],
                              pointer_flags.size(),
                              &cxunsaved_files[ 0 ],
                              cxunsaved_files.size(),
                              clang_defaultEditingTranslationUnitOptions() );

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
  if ( clang_translation_unit_ ) {
    clang_disposeTranslationUnit( clang_translation_unit_ );
    clang_translation_unit_ = NULL;
  }
}


std::vector< Diagnostic > TranslationUnit::LatestDiagnostics() {
  std::vector< Diagnostic > diagnostics;
  unique_lock< mutex > lock( diagnostics_mutex_ );

  // We don't need the latest diags after we return them once so we swap the
  // internal data with a new, empty diag vector. This vector is then returned
  // and on C++11 compilers a move ctor is invoked, thus no copy is created.
  // Theoretically, just returning the value of a
  // [boost::|std::]move(latest_diagnostics_) call _should_ leave the
  // latest_diagnostics_ vector in an emtpy, valid state but I'm not going to
  // rely on that. I just had to look this up in the standard to be sure, and
  // future readers of this code (myself included) should not be forced to do
  // that to understand what the hell is going on.

  std::swap( latest_diagnostics_, diagnostics );
  return diagnostics;
}


bool TranslationUnit::IsCurrentlyUpdating() const {
  unique_lock< mutex > lock( clang_access_mutex_, try_to_lock_t() );
  return !lock.owns_lock();
}


void TranslationUnit::Reparse(
  const std::vector< UnsavedFile > &unsaved_files ) {
  std::vector< CXUnsavedFile > cxunsaved_files =
    ToCXUnsavedFiles( unsaved_files );

  Reparse( cxunsaved_files );
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
                          &cxunsaved_files[ 0 ],
                          cxunsaved_files.size(),
                          clang_defaultCodeCompleteOptions() ),
    clang_disposeCodeCompleteResults );

  std::vector< CompletionData > candidates = ToCompletionDataVector(
      results.get() );
  return candidates;
}


// Argument taken as non-const ref because we need to be able to pass a
// non-const pointer to clang. This function (and clang too) will not modify the
// param though.
void TranslationUnit::Reparse(
  std::vector< CXUnsavedFile > &unsaved_files ) {
  unique_lock< mutex > lock( clang_access_mutex_ );

  if ( !clang_translation_unit_ )
    return;

  int failure = clang_reparseTranslationUnit(
                  clang_translation_unit_,
                  unsaved_files.size(),
                  &unsaved_files[ 0 ],
                  clang_defaultEditingTranslationUnitOptions() );

  if ( failure ) {
    Destroy();
    boost_throw( ClangParseError() );
  }

  UpdateLatestDiagnostics();
}


// Should only be called while holding the clang_access_mutex_
void TranslationUnit::UpdateLatestDiagnostics() {
  unique_lock< mutex > lock( diagnostics_mutex_ );

  latest_diagnostics_.clear();
  uint num_diagnostics = clang_getNumDiagnostics( clang_translation_unit_ );
  latest_diagnostics_.reserve( num_diagnostics );

  for ( uint i = 0; i < num_diagnostics; ++i ) {
    Diagnostic diagnostic =
      DiagnosticWrapToDiagnostic(
        DiagnosticWrap( clang_getDiagnostic( clang_translation_unit_, i ),
                        clang_disposeDiagnostic ) );

    if ( diagnostic.kind_ != 'I' )
      latest_diagnostics_.push_back( diagnostic );
  }
}

} // namespace YouCompleteMe
