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

namespace YouCompleteMe
{

std::vector< CXUnsavedFile > ToCXUnsavedFiles(
    const std::vector< UnsavedFile > &unsaved_files )
{
  std::vector< CXUnsavedFile > clang_unsaved_files( unsaved_files.size() );
  for ( uint i = 0; i < unsaved_files.size(); ++i )
  {
    // TODO: assert non-null
    clang_unsaved_files[ i ].Filename = unsaved_files[ i ].filename_;
    clang_unsaved_files[ i ].Contents = unsaved_files[ i ].contents_;
    clang_unsaved_files[ i ].Length   = unsaved_files[ i ].length_;
  }

  return clang_unsaved_files;
}


std::string CXStringToString( CXString text )
{
  std::string final_string;
  if ( !text.data )
    return final_string;

  final_string = std::string( clang_getCString( text ) );
  clang_disposeString( text );
  return final_string;
}


std::string ChunkToString( CXCompletionString completion_string, int chunk_num )
{
  if ( !completion_string )
    return std::string();
  return CXStringToString(
      clang_getCompletionChunkText( completion_string, chunk_num ) );
}


// Returns true when the provided completion string is available to the user;
// unavailable completion strings refer to entities that are private/protected,
// deprecated etc.
bool CompletionStringAvailable( CXCompletionString completion_string )
{
  if ( !completion_string )
    return false;
  return clang_getCompletionAvailability( completion_string ) ==
    CXAvailability_Available;
}


bool IsMainCompletionTextInfo( CXCompletionChunkKind kind )
{
  return
    kind == CXCompletionChunk_Optional     ||
    kind == CXCompletionChunk_TypedText    ||
    kind == CXCompletionChunk_Placeholder  ||
    kind == CXCompletionChunk_LeftParen    ||
    kind == CXCompletionChunk_RightParen   ||
    kind == CXCompletionChunk_RightBracket ||
    kind == CXCompletionChunk_LeftBracket  ||
    kind == CXCompletionChunk_LeftBrace    ||
    kind == CXCompletionChunk_RightBrace   ||
    kind == CXCompletionChunk_RightAngle   ||
    kind == CXCompletionChunk_LeftAngle    ||
    kind == CXCompletionChunk_Comma        ||
    kind == CXCompletionChunk_Colon        ||
    kind == CXCompletionChunk_SemiColon    ||
    kind == CXCompletionChunk_Equal        ||
    kind == CXCompletionChunk_HorizontalSpace;

}


char CursorKindToVimKind( CXCursorKind kind )
{
  // TODO: actually it appears that Vim will show returned kinds even when they
  // do not match the "approved" list, so let's use that
  switch ( kind )
  {
    case CXCursor_UnexposedDecl:
    case CXCursor_StructDecl:
    case CXCursor_UnionDecl:
    case CXCursor_ClassDecl:
    case CXCursor_EnumDecl:
    case CXCursor_TypedefDecl:
      return 't';

    case CXCursor_FieldDecl:
      return 'm';

    case CXCursor_FunctionDecl:
    case CXCursor_CXXMethod:
    case CXCursor_FunctionTemplate:
      return 'f';

    case CXCursor_VarDecl:
      return 'v';

    case CXCursor_MacroDefinition:
      return 'd';

    default:
      return 'u'; // for 'unknown', 'unsupported'... whatever you like
  }
}


char DiagnosticSeverityToType( CXDiagnosticSeverity severity )
{
  switch ( severity )
  {
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


// TODO: this should be a constructor
CompletionData CompletionResultToCompletionData(
    const CXCompletionResult &completion_result )
{
  CompletionData data;
  CXCompletionString completion_string = completion_result.CompletionString;

  if ( !completion_string )
    return data;

  uint num_chunks = clang_getNumCompletionChunks( completion_string );
  bool saw_left_paren = false;
  bool saw_function_params = false;

  for ( uint j = 0; j < num_chunks; ++j )
  {
    CXCompletionChunkKind kind = clang_getCompletionChunkKind(
        completion_string, j );

    if ( IsMainCompletionTextInfo( kind ) )
    {
      if ( kind == CXCompletionChunk_LeftParen )
      {
        saw_left_paren = true;
      }

      else if ( saw_left_paren &&
                !saw_function_params &&
                kind != CXCompletionChunk_RightParen )
      {
        saw_function_params = true;
        data.everything_except_return_type_.append( " " );
      }

      else if ( saw_function_params && kind == CXCompletionChunk_RightParen )
      {
        data.everything_except_return_type_.append( " " );
      }

      data.everything_except_return_type_.append(
          ChunkToString( completion_string, j ) );
    }

    if ( kind == CXCompletionChunk_ResultType )
      data.return_type_ = ChunkToString( completion_string, j );

    if ( kind == CXCompletionChunk_TypedText )
      data.original_string_ = ChunkToString( completion_string, j );

    if ( kind == CXCompletionChunk_Informative )
      data.detailed_info_ = ChunkToString( completion_string, j );
  }

  data.kind_ = CursorKindToVimKind( completion_result.CursorKind );
  return data;
}


std::vector< CompletionData > ToCompletionDataVector(
    CXCodeCompleteResults *results )
{
  std::vector< CompletionData > completions;
  if ( !results || !results->Results )
    return completions;

  completions.reserve( results->NumResults );
  unordered_map< std::string, uint > seen_data;

  for ( uint i = 0; i < results->NumResults; ++i )
  {
    CXCompletionResult completion_result = results->Results[ i ];

    if ( !CompletionStringAvailable( completion_result.CompletionString ) )
      continue;

    CompletionData data = CompletionResultToCompletionData( completion_result );
    uint index = GetValueElseInsert( seen_data,
                                     data.original_string_,
                                     completions.size() );

    if ( index == completions.size() )
    {
      completions.push_back( data );
    }

    else
    {
      // If we have already seen this completion, then this is an overload of a
      // function we have seen. We add the signature of the overload to the
      // detailed information.
      completions[ index ].detailed_info_
        .append( "\n" )
        .append( data.return_type_ )
        .append( " " )
        .append( data.everything_except_return_type_ );
    }
  }

  return completions;
}


Diagnostic CXDiagnosticToDiagnostic( CXDiagnostic cxdiagnostic )
{
  Diagnostic diagnostic;
  if ( !cxdiagnostic )
    return diagnostic;

  diagnostic.kind_ = DiagnosticSeverityToType(
      clang_getDiagnosticSeverity( cxdiagnostic ) );

  // If this is an "ignored" diagnostic, there's no point in continuing since we
  // won't display those to the user
  if ( diagnostic.kind_ == 'I' )
    return diagnostic;

  CXSourceLocation location = clang_getDiagnosticLocation( cxdiagnostic );
  CXFile file;
  uint unused_offset;
  clang_getSpellingLocation( location,
                             &file,
                             &diagnostic.line_number_,
                             &diagnostic.column_number_,
                             &unused_offset );
  diagnostic.filename_ = CXStringToString( clang_getFileName( file ) );
  diagnostic.text_ = CXStringToString(
      clang_getDiagnosticSpelling( cxdiagnostic ) );

  clang_disposeDiagnostic( cxdiagnostic );
  return diagnostic;
}

} // namespace YouCompleteMe
