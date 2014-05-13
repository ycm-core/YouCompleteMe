// Copyright (C) 2011-2013  Google Inc.
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
#include "exceptions.h"
#include "Result.h"
#include "Candidate.h"
#include "TranslationUnit.h"
#include "standard.h"
#include "CandidateRepository.h"
#include "CompletionData.h"
#include "Utils.h"
#include "ClangUtils.h"
#include "ReleaseGil.h"

#include <clang-c/Index.h>
#include <boost/shared_ptr.hpp>


using boost::shared_ptr;
using boost::unordered_map;

namespace YouCompleteMe {

ClangCompleter::ClangCompleter()
  : clang_index_( clang_createIndex( 0, 0 ) ),
    translation_unit_store_( clang_index_ ) {
  // The libclang docs don't say what is the default value for crash recovery.
  // I'm pretty sure it's turned on by default, but I'm not going to take any
  // chances.
  clang_toggleCrashRecovery( true );
}


ClangCompleter::~ClangCompleter() {
  // We need to destroy all TUs before calling clang_disposeIndex because
  // the translation units need to be destroyed before the index is destroyed.
  // Technically, a thread could still be holding onto a shared_ptr<TU> object
  // when we destroy the clang index, but since we're shutting down, we don't
  // really care.
  // In practice, this situation shouldn't happen because the server threads are
  // Python deamon threads and will all be killed before the main thread exits.
  translation_unit_store_.RemoveAll();
  clang_disposeIndex( clang_index_ );
}


bool ClangCompleter::UpdatingTranslationUnit( const std::string &filename ) {
  ReleaseGil unlock;
  shared_ptr< TranslationUnit > unit = translation_unit_store_.Get( filename );

  if ( !unit )
    return false;

  // Thankfully, an invalid, sentinel TU always returns true for
  // IsCurrentlyUpdating, so no caller will try to rely on the TU object, even
  // if unit is currently pointing to a sentinel.
  return unit->IsCurrentlyUpdating();
}


std::vector< Diagnostic > ClangCompleter::UpdateTranslationUnit(
  const std::string &filename,
  const std::vector< UnsavedFile > &unsaved_files,
  const std::vector< std::string > &flags ) {
  ReleaseGil unlock;
  bool translation_unit_created;
  shared_ptr< TranslationUnit > unit = translation_unit_store_.GetOrCreate(
                                         filename,
                                         unsaved_files,
                                         flags,
                                         translation_unit_created );

  if ( !unit )
    return std::vector< Diagnostic >();

  try {
    // There's no point in reparsing a TU that was just created, it was just
    // parsed in the TU constructor
    if ( !translation_unit_created )
      return unit->Reparse( unsaved_files );

    return unit->LatestDiagnostics();
  }

  catch ( ClangParseError & ) {
    // If unit->Reparse fails, then the underlying TranslationUnit object is not
    // valid anymore and needs to be destroyed and removed from the filename ->
    // TU map.
    translation_unit_store_.Remove( filename );
  }

  return std::vector< Diagnostic >();
}


std::vector< CompletionData >
ClangCompleter::CandidatesForLocationInFile(
  const std::string &filename,
  int line,
  int column,
  const std::vector< UnsavedFile > &unsaved_files,
  const std::vector< std::string > &flags ) {
  ReleaseGil unlock;
  shared_ptr< TranslationUnit > unit =
    translation_unit_store_.GetOrCreate( filename, unsaved_files, flags );

  if ( !unit )
    return std::vector< CompletionData >();

  return unit->CandidatesForLocation( line,
                                      column,
                                      unsaved_files );
}


Location ClangCompleter::GetDeclarationLocation(
  const std::string &filename,
  int line,
  int column,
  const std::vector< UnsavedFile > &unsaved_files,
  const std::vector< std::string > &flags,
  bool reparse ) {
  ReleaseGil unlock;
  shared_ptr< TranslationUnit > unit =
    translation_unit_store_.GetOrCreate( filename, unsaved_files, flags );

  if ( !unit ) {
    return Location();
  }

  return unit->GetDeclarationLocation( line, column, unsaved_files, reparse );
}


Location ClangCompleter::GetDefinitionLocation(
  const std::string &filename,
  int line,
  int column,
  const std::vector< UnsavedFile > &unsaved_files,
  const std::vector< std::string > &flags,
  bool reparse ) {
  ReleaseGil unlock;
  shared_ptr< TranslationUnit > unit =
    translation_unit_store_.GetOrCreate( filename, unsaved_files, flags );

  if ( !unit ) {
    return Location();
  }

  return unit->GetDefinitionLocation( line, column, unsaved_files, reparse );
}


void ClangCompleter::DeleteCachesForFile( const std::string &filename ) {
  ReleaseGil unlock;
  translation_unit_store_.Remove( filename );
}


} // namespace YouCompleteMe
