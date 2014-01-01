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
#include <fstream>
#include <set>

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

/**
 * @brief function generating the textual description of a diagnostic. This
 * description is similar to the one generated by clang. It reads the source files
 * referenced by the diagnostic's location and ranges, write the specific lines
 * and underline the parts which are relevant.
 *
 * @param cxdiagnostic diagnostic from which the description will be generated.
 *
 * @return the string describing the given diagnostic.
 */
std::string CXDiagnosticToLocationAndRangesText( CXDiagnostic cxdiagnostic ) {
    // resulting map of <file name, map<line number, description>>
    std::map<std::string, std::map<unsigned, std::string>> result;

    // retrieve the context of the diagnostic's location
    const CXSourceLocation cxlocation = clang_getDiagnosticLocation( cxdiagnostic );
    CXFile loc_file;
    unsigned loc_line;
    unsigned loc_col;
    clang_getSpellingLocation( cxlocation, &loc_file, &loc_line, &loc_col, 0 );
    const std::string loc_path = CXStringToString( clang_getFileName( loc_file ) );

    // map all the ranges in a map of <file name, map<line number, set<ranges' column indexes>>>
    const unsigned num_ranges = clang_getDiagnosticNumRanges( cxdiagnostic );
    std::map<std::string, std::map<unsigned, std::set<unsigned>>> range_idxs{};
    for ( unsigned range = 0; range < num_ranges; ++range ) {
        CXSourceLocation range_start = clang_getRangeStart(
                clang_getDiagnosticRange( cxdiagnostic, range ) );
        CXSourceLocation range_end = clang_getRangeEnd(
                clang_getDiagnosticRange( cxdiagnostic, range ) );

        CXFile start_file, end_file;
        unsigned start_col, end_col, start_line, end_line;
        clang_getSpellingLocation( range_start, &start_file, &start_line, &start_col, 0 );
        clang_getSpellingLocation( range_end, &end_file, &end_line, &end_col, 0 );

        const std::string start_path = CXStringToString( clang_getFileName( start_file ) );
        const std::string end_path = CXStringToString( clang_getFileName( end_file ) );
        if ( start_path == end_path ) {
            // retrieve the file's lines ranges. Create it if none exists.
            std::map<unsigned, std::set<unsigned>>& range_lines = range_idxs[start_path];
            for ( unsigned l = start_line; l <= end_line; ++l ) {
                // retrieve the ranged columns for the current line. Create it if none exists.
                std::set<unsigned>& range_line = range_lines[l];
                for ( unsigned c = start_col; c < end_col; ++c ) {
                    range_line.insert( c );
                }
            }
        } else {
            // The range spans on multiple files... only take the first character of the first
            // line
            std::map<unsigned, std::set<unsigned>>& range_lines = range_idxs[start_path];
            std::set<unsigned>& range_line = range_lines[start_line];
            range_line.insert(start_col);
        }
    }

    // for each range generate the underlines. If the line is also referenced by the
    // diagnostic's location then add the caret under the location.
    bool loc_processed = false; // true if the location has been processed
    for ( auto current_file : range_idxs ) {
        const std::string current_path = current_file.first;
        std::map<unsigned, std::string>& result_file = result[current_path];
        for ( auto current_line : current_file.second ) {
            // retrieve the current line result
            std::string& result_line = result_file[current_line.first];
            const std::set<unsigned>& line_idxs = current_line.second;
            unsigned max_col = *line_idxs.rbegin();
            bool processing_location = false;
            if ( current_path == loc_path and current_line.first == loc_line ) {
                loc_processed = true;
                unsigned max_col = max_col > loc_col ? max_col : loc_col;
                processing_location = true;
            }
            for ( unsigned current_col = 1; current_col <= max_col; ++current_col ) {
                if ( processing_location and current_col == loc_col ) {
                    result_line.append("^");
                } else if ( line_idxs.find( current_col ) != line_idxs.end() ) {
                    result_line.append("~");
                } else {
                    result_line.append(" ");
                }
            }
        }
    }
    // if the ranges are not on the same line as the location, add the location
    if ( not loc_processed ) {
        std::map<unsigned, std::string>& result_file = result[loc_path];
        std::string result_line(loc_col > 0 ? loc_col - 1 : 0 , ' ');
        result_line.append("^");
        result_file[loc_line] = result_line;
    }

    // for each underline, read the corresponding line in the source file and generate the
    // resulting description (~= source line \n underline)
    std::string str_result;
    for ( auto current_file : result ) {
        if (current_file.first != loc_path) {
            str_result.append(current_file.first + ": context:\n");
        }
        std::ifstream infile( current_file.first );
        std::string line;
        unsigned current_line_idx = 0;
        for ( auto current_line : current_file.second ) {
            line = "YCM ERROR WHILE READING FILE \"" + current_file.first + "\"";
            while ( infile.good() and std::getline( infile, line ) ) {
                if ( ++current_line_idx == current_line.first ) {
                    break;
                }
                line = "YCM ERROR WHILE READING FILE \"" + current_file.first + "\"";
            }
            // prepend the source code line
            std::string index = std::to_string(current_line_idx) + ": ";
            str_result.append(index + line + "\n"
                    + std::string(index.size(), ' ') + current_line.second + "\n");
        }
    }

    return str_result;
}


// NOTE: The passed in pointer should never be NULL!
std::string FullDiagnosticText( CXDiagnostic cxdiagnostic ) {
  std::string full_text = CXStringToString(
                            clang_formatDiagnostic(
                              cxdiagnostic,
                              clang_defaultDiagnosticDisplayOptions() ) );
  full_text.append( "\n" );
  full_text.append( CXDiagnosticToLocationAndRangesText( cxdiagnostic ) );
  full_text.append( "\n" );

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
