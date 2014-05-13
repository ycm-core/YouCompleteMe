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

#include "CompletionData.h"
#include "ClangUtils.h"

#include <boost/algorithm/string/erase.hpp>
#include <boost/move/move.hpp>

namespace {

char CursorKindToVimKind( CXCursorKind kind ) {
  switch ( kind ) {
    case CXCursor_StructDecl:
      return 's';

    case CXCursor_ClassDecl:
    case CXCursor_ClassTemplate:
      return 'c';

    case CXCursor_EnumDecl:
      return 'e';

    case CXCursor_UnexposedDecl:
    case CXCursor_UnionDecl:
    case CXCursor_TypedefDecl:
      return 't';

    case CXCursor_FieldDecl:
      return 'm';

    case CXCursor_FunctionDecl:
    case CXCursor_CXXMethod:
    case CXCursor_FunctionTemplate:
    case CXCursor_ConversionFunction:
    case CXCursor_Constructor:
    case CXCursor_Destructor:
      return 'f';

    case CXCursor_VarDecl:
      return 'v';

    case CXCursor_MacroDefinition:
      return 'd';

    case CXCursor_ParmDecl:
      return 'p';

    case CXCursor_Namespace:
    case CXCursor_NamespaceAlias:
      return 'n';

    default:
      return 'u'; // for 'unknown', 'unsupported'... whatever you like
  }
}


bool IsMainCompletionTextInfo( CXCompletionChunkKind kind ) {
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


std::string ChunkToString( CXCompletionString completion_string,
                           uint chunk_num ) {
  if ( !completion_string )
    return std::string();

  return YouCompleteMe::CXStringToString(
           clang_getCompletionChunkText( completion_string, chunk_num ) );
}


std::string OptionalChunkToString( CXCompletionString completion_string,
                                   uint chunk_num ) {
  std::string final_string;

  if ( !completion_string )
    return final_string;

  CXCompletionString optional_completion_string =
    clang_getCompletionChunkCompletionString( completion_string, chunk_num );

  if ( !optional_completion_string )
    return final_string;

  uint optional_num_chunks = clang_getNumCompletionChunks(
                               optional_completion_string );

  for ( uint j = 0; j < optional_num_chunks; ++j ) {
    CXCompletionChunkKind kind = clang_getCompletionChunkKind(
                                   optional_completion_string, j );

    if ( kind == CXCompletionChunk_Optional ) {
      final_string.append( OptionalChunkToString( optional_completion_string,
                                                  j ) );
    }

    else {
      final_string.append( ChunkToString( optional_completion_string, j ) );
    }
  }

  return final_string;
}


// NOTE: this function accepts the text param by value on purpose; it internally
// needs a copy before processing the text so the copy might as well be made on
// the parameter BUT if this code is compiled in C++11 mode a move constructor
// can be called on the passed-in value. This is not possible if we accept the
// param by const ref.
std::string RemoveTwoConsecutiveUnderscores( std::string text ) {
  boost::erase_all( text, "__" );
  return text;
}

} // unnamed namespace


namespace YouCompleteMe {

CompletionData::CompletionData( const CXCompletionResult &completion_result ) {
  CXCompletionString completion_string = completion_result.CompletionString;

  if ( !completion_string )
    return;

  uint num_chunks = clang_getNumCompletionChunks( completion_string );
  bool saw_left_paren = false;
  bool saw_function_params = false;

  for ( uint j = 0; j < num_chunks; ++j ) {
    ExtractDataFromChunk( completion_string,
                          j,
                          saw_left_paren,
                          saw_function_params );
  }

  kind_ = CursorKindToVimKind( completion_result.CursorKind );

  // We remove any two consecutive underscores from the function definition
  // since identifiers with them are ugly, compiler-reserved names. Functions
  // from the standard library use parameter names like "__pos" and we want to
  // show them as just "pos". This will never interfere with client code since
  // ANY C++ identifier with two consecutive underscores in it is
  // compiler-reserved.
  everything_except_return_type_ =
    RemoveTwoConsecutiveUnderscores(
      boost::move( everything_except_return_type_ ) );

  detailed_info_.append( return_type_ )
  .append( " " )
  .append( everything_except_return_type_ )
  .append( "\n" );
}


void CompletionData::ExtractDataFromChunk( CXCompletionString completion_string,
                                           uint chunk_num,
                                           bool &saw_left_paren,
                                           bool &saw_function_params ) {
  CXCompletionChunkKind kind = clang_getCompletionChunkKind(
                                 completion_string, chunk_num );

  if ( IsMainCompletionTextInfo( kind ) ) {
    if ( kind == CXCompletionChunk_LeftParen ) {
      saw_left_paren = true;
    }

    else if ( saw_left_paren &&
              !saw_function_params &&
              kind != CXCompletionChunk_RightParen &&
              kind != CXCompletionChunk_Informative ) {
      saw_function_params = true;
      everything_except_return_type_.append( " " );
    }

    else if ( saw_function_params && kind == CXCompletionChunk_RightParen ) {
      everything_except_return_type_.append( " " );
    }

    if ( kind == CXCompletionChunk_Optional ) {
      everything_except_return_type_.append(
        OptionalChunkToString( completion_string, chunk_num ) );
    }

    else {
      everything_except_return_type_.append(
        ChunkToString( completion_string, chunk_num ) );
    }
  }

  if ( kind == CXCompletionChunk_ResultType )
    return_type_ = ChunkToString( completion_string, chunk_num );

  if ( kind == CXCompletionChunk_TypedText )
    original_string_ = ChunkToString( completion_string, chunk_num );
}

} // namespace YouCompleteMe
