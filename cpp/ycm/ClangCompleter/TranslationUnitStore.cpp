// Copyright (C) 2013  Google Inc.
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

#include "TranslationUnitStore.h"
#include "TranslationUnit.h"
#include "Utils.h"
#include "exceptions.h"

#include <boost/thread/locks.hpp>
#include <boost/make_shared.hpp>
#include <boost/functional/hash.hpp>

using boost::lock_guard;
using boost::shared_ptr;
using boost::make_shared;
using boost::mutex;

namespace YouCompleteMe {

namespace {

std::size_t HashForFlags( const std::vector< std::string > &flags ) {
  return boost::hash< std::vector< std::string > >()( flags );
}

}  // unnamed namespace


TranslationUnitStore::TranslationUnitStore( CXIndex clang_index )
  : clang_index_( clang_index ) {
}


TranslationUnitStore::~TranslationUnitStore() {
  RemoveAll();
}


shared_ptr< TranslationUnit > TranslationUnitStore::GetOrCreate(
  const std::string &filename,
  const std::vector< UnsavedFile > &unsaved_files,
  const std::vector< std::string > &flags ) {
  bool dont_care;
  return GetOrCreate( filename, unsaved_files, flags, dont_care );
}


shared_ptr< TranslationUnit > TranslationUnitStore::GetOrCreate(
  const std::string &filename,
  const std::vector< UnsavedFile > &unsaved_files,
  const std::vector< std::string > &flags,
  bool &translation_unit_created ) {
  translation_unit_created = false;
  {
    lock_guard< mutex > lock( filename_to_translation_unit_and_flags_mutex_ );
    shared_ptr< TranslationUnit > current_unit = GetNoLock( filename );

    if ( current_unit &&
         HashForFlags( flags ) == filename_to_flags_hash_[ filename ] ) {
      return current_unit;
    }

    // We create and store an invalid, sentinel TU so that other threads don't
    // try to create a TU for the same file while we are trying to create this
    // TU object. When we are done creating the TU, we will overwrite this value
    // with the valid object.
    filename_to_translation_unit_[ filename ] =
      make_shared< TranslationUnit >();

    // We need to store the flags for the sentinel TU so that other threads end
    // up returning the sentinel TU while the real one is being created.
    filename_to_flags_hash_[ filename ] = HashForFlags( flags );
  }

  boost::shared_ptr< TranslationUnit > unit;

  try {
    unit = boost::make_shared< TranslationUnit >( filename,
                                                  unsaved_files,
                                                  flags,
                                                  clang_index_ );
  } catch ( ClangParseError & ) {
    Remove( filename );
    return unit;
  }

  {
    lock_guard< mutex > lock( filename_to_translation_unit_and_flags_mutex_ );
    filename_to_translation_unit_[ filename ] = unit;
    // Flags have already been stored.
  }

  translation_unit_created = true;
  return unit;
}


shared_ptr< TranslationUnit > TranslationUnitStore::Get(
  const std::string &filename ) {
  lock_guard< mutex > lock( filename_to_translation_unit_and_flags_mutex_ );
  return GetNoLock( filename );
}


bool TranslationUnitStore::Remove( const std::string &filename ) {
  lock_guard< mutex > lock( filename_to_translation_unit_and_flags_mutex_ );
  Erase( filename_to_flags_hash_, filename );
  return Erase( filename_to_translation_unit_, filename );
}


void TranslationUnitStore::RemoveAll() {
  lock_guard< mutex > lock( filename_to_translation_unit_and_flags_mutex_ );
  filename_to_translation_unit_.clear();
  filename_to_flags_hash_.clear();
}


shared_ptr< TranslationUnit > TranslationUnitStore::GetNoLock(
  const std::string &filename ) {
  return FindWithDefault( filename_to_translation_unit_,
                          filename,
                          shared_ptr< TranslationUnit >() );
}

} // namespace YouCompleteMe
