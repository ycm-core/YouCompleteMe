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

#ifndef TRANSLATIONUNITSTORE_H_NGN0MCKB
#define TRANSLATIONUNITSTORE_H_NGN0MCKB

#include "TranslationUnit.h"
#include "UnsavedFile.h"

#include <string>
#include <vector>

#include <boost/utility.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/unordered_map.hpp>

typedef void *CXIndex;

namespace YouCompleteMe {

class TranslationUnitStore : boost::noncopyable {
public:
  TranslationUnitStore( CXIndex clang_index );
  ~TranslationUnitStore();

  // You can even call this function for the same filename from multiple
  // threads; the TU store will ensure only one TU is created.
  boost::shared_ptr< TranslationUnit > GetOrCreate(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags );

  boost::shared_ptr< TranslationUnit > GetOrCreate(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags,
    bool &translation_unit_created );

  // Careful here! While GetOrCreate makes sure to take into account the flags
  // for the file before returning a stored TU (if the flags changed, the TU is
  // not really valid anymore and a new one should be built), this function does
  // not. You might end up getting a stale TU.
  boost::shared_ptr< TranslationUnit > Get( const std::string &filename );

  bool Remove( const std::string &filename );

  void RemoveAll();

private:

  // WARNING: This accesses filename_to_translation_unit_ without a lock!
  boost::shared_ptr< TranslationUnit > GetNoLock( const std::string &filename );


  typedef boost::unordered_map < std::string,
          boost::shared_ptr< TranslationUnit > > TranslationUnitForFilename;

  typedef boost::unordered_map < std::string,
          std::size_t > FlagsHashForFilename;

  CXIndex clang_index_;
  TranslationUnitForFilename filename_to_translation_unit_;
  FlagsHashForFilename filename_to_flags_hash_;
  boost::mutex filename_to_translation_unit_and_flags_mutex_;
};

} // namespace YouCompleteMe

#endif  // TRANSLATIONUNITSTORE_H_NGN0MCKB
