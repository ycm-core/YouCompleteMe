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

#ifndef CLANGUTILS_H_9MVHQLJS
#define CLANGUTILS_H_9MVHQLJS

#include "Diagnostic.h"
#include "CompletionData.h"
#include "UnsavedFile.h"

#include <vector>
#include <clang-c/Index.h>
#include <boost/shared_ptr.hpp>
#include <boost/type_traits/remove_pointer.hpp>

namespace YouCompleteMe {

typedef boost::shared_ptr <
boost::remove_pointer< CXDiagnostic >::type > DiagnosticWrap;

std::string CXStringToString( CXString text );

std::vector< CompletionData > ToCompletionDataVector(
  CXCodeCompleteResults *results );

// NOTE: CXUnsavedFiles store pointers to data in UnsavedFiles, so UnsavedFiles
// need to outlive CXUnsavedFiles!
std::vector< CXUnsavedFile > ToCXUnsavedFiles(
  const std::vector< UnsavedFile > &unsaved_files );

Diagnostic DiagnosticWrapToDiagnostic( DiagnosticWrap diagnostic_wrap );

bool CursorIsValid( CXCursor cursor );

bool CursorIsReference( CXCursor cursor );

bool CursorIsDeclaration( CXCursor cursor );

std::string CXFileToFilepath( CXFile file );

std::string ClangVersion();

} // namespace YouCompleteMe

#endif /* end of include guard: CLANGUTILS_H_9MVHQLJS */

