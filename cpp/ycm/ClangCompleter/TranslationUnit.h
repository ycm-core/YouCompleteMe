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

#ifndef TRANSLATIONUNIT_H_XQ7I6SVA
#define TRANSLATIONUNIT_H_XQ7I6SVA

#include "ConcurrentLatestValue.h"
#include "Future.h"
#include "UnsavedFile.h"
#include "Diagnostic.h"

#include <boost/utility.hpp>
#include <boost/thread/mutex.hpp>

#include <string>
#include <vector>

typedef void *CXIndex;
typedef struct CXTranslationUnitImpl *CXTranslationUnit;
struct CXUnsavedFile;

namespace YouCompleteMe {

struct CompletionData;
typedef boost::shared_ptr< std::vector< CompletionData > > AsyncCompletions;

class TranslationUnit : boost::noncopyable {
public:

  TranslationUnit(
    const std::string &filename,
    const std::vector< UnsavedFile > &unsaved_files,
    const std::vector< std::string > &flags,
    CXIndex clang_index );

  ~TranslationUnit();

  std::vector< Diagnostic > LatestDiagnostics();

  bool IsCurrentlyUpdating() const;

  void Reparse( const std::vector< UnsavedFile > &unsaved_files );

  std::vector< CompletionData > CandidatesForLocation(
    int line,
    int column,
    const std::vector< UnsavedFile > &unsaved_files );

private:

  void Reparse( std::vector< CXUnsavedFile > &unsaved_files );

  void UpdateLatestDiagnostics();

  /////////////////////////////
  // PRIVATE MEMBER VARIABLES
  /////////////////////////////

  std::string filename_;

  boost::mutex diagnostics_mutex_;
  std::vector< Diagnostic > latest_diagnostics_;

  mutable boost::mutex clang_access_mutex_;
  CXTranslationUnit clang_translation_unit_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: TRANSLATIONUNIT_H_XQ7I6SVA */

