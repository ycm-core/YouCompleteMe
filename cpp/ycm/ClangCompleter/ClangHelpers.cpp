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

#include "standard.h"
#include "ClangHelpers.h"
#include "ClangUtils.h"
#include "Utils.h"
#include "UnsavedFile.h"
#include "Location.h"
#include "Range.h"

#include <boost/unordered_map.hpp>

using boost::unordered_map;

namespace YouCompleteMe {
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


std::vector< Range > GetRanges( const DiagnosticWrap &diagnostic_wrap ) {
  std::vector< Range > ranges;
  uint num_ranges = clang_getDiagnosticNumRanges( diagnostic_wrap.get() );
  ranges.reserve( num_ranges );

  for ( uint i = 0; i < num_ranges; ++i ) {
    ranges.push_back(
        Range( clang_getDiagnosticRange( diagnostic_wrap.get(), i ) ) );
  }

  return ranges;
}


Range GetLocationExtent( CXSourceLocation source_location,
                         CXTranslationUnit translation_unit ) {
  // If you think the below code is an idiotic way of getting the source range
  // for an identifier at a specific source location, you are not the only one.
  // I cannot believe that this is the only way to achieve this with the
  // libclang API in a robust way.
  // I've tried many simpler ways of doing this and they all fail in various
  // situations.

  CXSourceRange range = clang_getCursorExtent(
      clang_getCursor( translation_unit, source_location ) );
  CXToken *tokens;
  uint num_tokens;
  clang_tokenize( translation_unit, range, &tokens, &num_tokens );

  Location location( source_location );
  Range final_range;
  for ( uint i = 0; i < num_tokens; ++i ) {
    Location token_location( clang_getTokenLocation( translation_unit,
                                                     tokens[ i ] ) );
    if ( token_location == location ) {
      std::string name = CXStringToString(
          clang_getTokenSpelling( translation_unit, tokens[ i ] ) );
      Location end_location = location;
      end_location.column_number_ += name.length();
      final_range = Range( location, end_location );
      break;
    }
  }

  clang_disposeTokens( translation_unit, tokens, num_tokens );
  return final_range;
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


Diagnostic BuildDiagnostic( DiagnosticWrap diagnostic_wrap,
                            CXTranslationUnit translation_unit ) {
  Diagnostic diagnostic;

  if ( !diagnostic_wrap )
    return diagnostic;

  diagnostic.kind_ = DiagnosticSeverityToType(
                       clang_getDiagnosticSeverity( diagnostic_wrap.get() ) );

  // If this is an "ignored" diagnostic, there's no point in continuing since we
  // won't display those to the user
  if ( diagnostic.kind_ == 'I' )
    return diagnostic;

  CXSourceLocation source_location =
      clang_getDiagnosticLocation( diagnostic_wrap.get() );
  diagnostic.location_ = Location( source_location );
  diagnostic.location_extent_ = GetLocationExtent( source_location,
                                                   translation_unit );
  diagnostic.ranges_ = GetRanges( diagnostic_wrap );
  diagnostic.text_ = CXStringToString(
                       clang_getDiagnosticSpelling( diagnostic_wrap.get() ) );
  diagnostic.long_formatted_text_ = FullDiagnosticText( diagnostic_wrap.get() );

  return diagnostic;
}

} // namespace YouCompleteMe
