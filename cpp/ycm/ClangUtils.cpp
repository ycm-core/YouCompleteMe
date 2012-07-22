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
#include "Utils.h"

#include <cctype>
#include <boost/algorithm/string.hpp>


namespace YouCompleteMe
{

const char *CLANG_OPTIONS_FILENAME = ".ycm_clang_options";

std::vector< std::string > SanitizeClangFlags(
    const std::vector< std::string > &flags )
{
  std::vector< std::string > sanitized_flags = flags;
  std::vector< std::string >::iterator it = sanitized_flags.begin();

  while ( it != sanitized_flags.end() )
  {
    if ( *it == "-arch" )
    {
      if ( it + 1 != sanitized_flags.end() )
        sanitized_flags.erase( it, it + 2 );
      else
        sanitized_flags.erase( it, it + 1 );
    }

    else
    {
      ++it;
    }
  }

  return sanitized_flags;
}


std::vector< std::string > SplitFlags( const std::string &flags_string )
{
  std::vector< std::string > flags;

  bool in_quotes = false;
  uint flag_start = 0;
  uint flag_length = 0;
  for ( uint i = 0; i < flags_string.size(); ++i )
  {
    char current_char = flags_string[ i ];
    if ( isspace( current_char ) and !in_quotes )
    {
      if ( flag_length != 0 )
      {
        flags.push_back( flags_string.substr( flag_start, flag_length ) );
        flag_length = 0;
      }

      flag_start = i + 1;
      continue;
    }

    if ( current_char == '\'' || current_char == '\"' )
    {
      in_quotes = !in_quotes;
    }

    ++flag_length;
  }

  if ( flag_length != 0 )
    flags.push_back( flags_string.substr( flag_start, flag_length ) );

  return flags;
}


std::string GetNearestClangOptions( const std::string &filename )
{
  fs::path parent_folder = fs::path( filename ).parent_path();
  fs::path clang_options_filename( CLANG_OPTIONS_FILENAME );

  std::string options_file_contents;
  fs::path old_parent_folder = parent_folder;

  do
  {
    fs::path current_file = parent_folder / clang_options_filename;
    if ( fs::exists( current_file ) )
    {
      options_file_contents = ReadUtf8File( current_file );
      break;
    }

    old_parent_folder = parent_folder;
    parent_folder = parent_folder.parent_path();
  }
  while ( old_parent_folder != parent_folder );

  return options_file_contents;
}

} // namespace YouCompleteMe
