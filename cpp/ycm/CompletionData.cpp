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

#include "CompletionData.h"
#include "standard.h"

namespace
{

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
    kind == CXCompletionChunk_Informative  ||
    kind == CXCompletionChunk_HorizontalSpace;

}


std::string ChunkToString( CXCompletionString completion_string, int chunk_num )
{
  if ( !completion_string )
    return std::string();
  return YouCompleteMe::CXStringToString(
      clang_getCompletionChunkText( completion_string, chunk_num ) );
}


std::string OptionalChunkToString( CXCompletionString completion_string,
                                   int chunk_num )
{
  std::string final_string;
  if ( !completion_string )
    return final_string;

  CXCompletionString optional_completion_string =
    clang_getCompletionChunkCompletionString( completion_string, chunk_num );

  if ( !optional_completion_string )
    return final_string;

  uint optional_num_chunks = clang_getNumCompletionChunks(
      optional_completion_string );

  for ( uint j = 0; j < optional_num_chunks; ++j )
  {
    CXCompletionChunkKind kind = clang_getCompletionChunkKind(
        optional_completion_string, j );

    if ( kind == CXCompletionChunk_Optional )
    {
      final_string.append( OptionalChunkToString( optional_completion_string,
                                                  j ) );
    }

    else
    {
      final_string.append( ChunkToString( optional_completion_string, j ) );
    }
  }

  return final_string;
}

} // unnamed namespace


namespace YouCompleteMe
{

std::string CXStringToString( CXString text )
{
  std::string final_string;
  if ( !text.data )
    return final_string;

  final_string = std::string( clang_getCString( text ) );
  clang_disposeString( text );
  return final_string;
}


CompletionData::CompletionData( const CXCompletionResult &completion_result )
{
  CXCompletionString completion_string = completion_result.CompletionString;

  if ( !completion_string )
    return;

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
                kind != CXCompletionChunk_RightParen &&
                kind != CXCompletionChunk_Informative )
      {
        saw_function_params = true;
        everything_except_return_type_.append( " " );
      }

      else if ( saw_function_params && kind == CXCompletionChunk_RightParen )
      {
        everything_except_return_type_.append( " " );
      }

      if ( kind == CXCompletionChunk_Optional )
      {
        everything_except_return_type_.append(
            OptionalChunkToString( completion_string, j ) );
      }

      else
      {
        everything_except_return_type_.append(
            ChunkToString( completion_string, j ) );
      }
    }

    if ( kind == CXCompletionChunk_ResultType )
      return_type_ = ChunkToString( completion_string, j );

    if ( kind == CXCompletionChunk_TypedText )
      original_string_ = ChunkToString( completion_string, j );
  }

  kind_ = CursorKindToVimKind( completion_result.CursorKind );
}

} // namespace YouCompleteMe
