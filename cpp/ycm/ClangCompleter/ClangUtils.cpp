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

#include "ClangUtils.h"
#include "standard.h"
#include "Utils.h"
#include "UnsavedFile.h"

#include <vector>
#include <string>

#include <boost/unordered_map.hpp>
using boost::unordered_map;

namespace YouCompleteMe {

std::string CXStringToString( CXString text ) {
  std::string final_string;

  if ( !text.data )
    return final_string;

  final_string = std::string( clang_getCString( text ) );
  clang_disposeString( text );
  return final_string;
}

namespace {

// NOTE: The passed in pointer should never be NULL!
std::string FullDiagnosticText( CXDiagnostic cxdiagnostic ) {
  std::string full_text = CXStringToString(
                            clang_formatDiagnostic(
                              cxdiagnostic,
                              clang_defaultDiagnosticDisplayOptions() ) );

  // Note: clang docs say that a CXDiagnosticSet retrieved with
  // clang_getChildDiagnostics do NOT need to be released with
  // clang_diposeDiagnosticSet
  CXDiagnosticSet diag_set = clang_getChildDiagnostics( cxdiagnostic );

  if ( !diag_set )
    return full_text;

  uint num_child_diagnostics = clang_getNumDiagnosticsInSet( diag_set );

  if ( !num_child_diagnostics )
    return full_text;

  for ( uint i = 0; i < num_child_diagnostics; ++i ) {
    CXDiagnostic diagnostic = clang_getDiagnosticInSet( diag_set, i );

    if ( !diagnostic )
      continue;

    full_text.append( FullDiagnosticText( diagnostic ) );
  }

  return full_text;
}


char DiagnosticSeverityToType( CXDiagnosticSeverity severity ) {
  switch ( severity ) {
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


// Returns true when the provided completion string is available to the user;
// unavailable completion strings refer to entities that are private/protected,
// deprecated etc.
bool CompletionStringAvailable( CXCompletionString completion_string ) {
  if ( !completion_string )
    return false;

  return clang_getCompletionAvailability( completion_string ) ==
         CXAvailability_Available;
}

} // unnamed namespace


std::vector< CXUnsavedFile > ToCXUnsavedFiles(
  const std::vector< UnsavedFile > &unsaved_files ) {
  std::vector< CXUnsavedFile > clang_unsaved_files( unsaved_files.size() );

  for ( uint i = 0; i < unsaved_files.size(); ++i ) {
    clang_unsaved_files[ i ].Filename = unsaved_files[ i ].filename_.c_str();
    clang_unsaved_files[ i ].Contents = unsaved_files[ i ].contents_.c_str();
    clang_unsaved_files[ i ].Length   = unsaved_files[ i ].length_;
  }

  return clang_unsaved_files;
}


std::vector< CompletionData > ToCompletionDataVector(
  CXCodeCompleteResults *results ) {
  std::vector< CompletionData > completions;

  if ( !results || !results->Results )
    return completions;

  completions.reserve( results->NumResults );
  unordered_map< std::string, uint > seen_data;

  for ( uint i = 0; i < results->NumResults; ++i ) {
    CXCompletionResult completion_result = results->Results[ i ];

    if ( !CompletionStringAvailable( completion_result.CompletionString ) )
      continue;

    CompletionData data( completion_result );
    uint index = GetValueElseInsert( seen_data,
                                     data.original_string_,
                                     completions.size() );

    if ( index == completions.size() ) {
      completions.push_back( boost::move( data ) );
    }

    else {
      // If we have already seen this completion, then this is an overload of a
      // function we have seen. We add the signature of the overload to the
      // detailed information.
      completions[ index ].detailed_info_
      .append( data.return_type_ )
      .append( " " )
      .append( data.everything_except_return_type_ )
      .append( "\n" );
    }
  }

  return completions;
}


Diagnostic DiagnosticWrapToDiagnostic( DiagnosticWrap diagnostic_wrap ) {
  Diagnostic diagnostic;

  if ( !diagnostic_wrap )
    return diagnostic;

  diagnostic.kind_ = DiagnosticSeverityToType(
                       clang_getDiagnosticSeverity( diagnostic_wrap.get() ) );

  // If this is an "ignored" diagnostic, there's no point in continuing since we
  // won't display those to the user
  if ( diagnostic.kind_ == 'I' )
    return diagnostic;

  CXSourceLocation location = clang_getDiagnosticLocation( diagnostic_wrap.get() );
  CXFile file;
  uint unused_offset;
  clang_getSpellingLocation( location,
                             &file,
                             &diagnostic.line_number_,
                             &diagnostic.column_number_,
                             &unused_offset );

  diagnostic.filename_ = CXFileToFilepath( file );
  diagnostic.text_ = CXStringToString(
                       clang_getDiagnosticSpelling( diagnostic_wrap.get() ) );
  diagnostic.long_formatted_text_ = FullDiagnosticText( diagnostic_wrap.get() );

  return diagnostic;
}

bool CursorIsValid( CXCursor cursor ) {
  return !clang_Cursor_isNull( cursor ) &&
         !clang_isInvalid( clang_getCursorKind( cursor ) );
}

bool CursorIsReference( CXCursor cursor ) {
  return clang_isReference( clang_getCursorKind( cursor ) );
}

bool CursorIsDeclaration( CXCursor cursor ) {
  return clang_isDeclaration( clang_getCursorKind( cursor ) );
}

std::string CXFileToFilepath( CXFile file ) {
  return CXStringToString( clang_getFileName( file ) );
}

std::string ClangVersion() {
  return CXStringToString( clang_getClangVersion() );
}

} // namespace YouCompleteMe
