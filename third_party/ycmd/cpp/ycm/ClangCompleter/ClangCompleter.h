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

#ifndef CLANGCOMPLETE_H_WLKDU0ZV
#define CLANGCOMPLETE_H_WLKDU0ZV

#include "UnsavedFile.h"
#include "Diagnostic.h"
#include "TranslationUnitStore.h"

#include <boost/utility.hpp>

#include <string>

typedef struct CXTranslationUnitImpl *CXTranslationUnit;

namespace YouCompleteMe {

class TranslationUnit;
struct CompletionData;
struct Location;

typedef std::vector< CompletionData > CompletionDatas;


// All filename parameters must be absolute paths.
class ClangCompleter : boost::noncopyable {
public:
  ClangCompleter();
  ~ClangCompleter();

  bool UpdatingTranslationUnit( const std::string &filename );

  std::vector< Diagnostic > UpdateTranslationUnit(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags );

  std::vector< CompletionData > CandidatesForLocationInFile(
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
    const std::vector< std::string > &flags,
    bool reparse = true );

  Location GetDefinitionLocation(
    const std::string &filename,
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags,
    bool reparse = true );

  void DeleteCachesForFile( const std::string &filename );

private:

  /////////////////////////////
  // PRIVATE MEMBER VARIABLES
  /////////////////////////////

  CXIndex clang_index_;

  TranslationUnitStore translation_unit_store_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: CLANGCOMPLETE_H_WLKDU0ZV */
