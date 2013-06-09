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

#include "IdentifierUtils.h"
#include "Utils.h"
#include "standard.h"

#include <boost/unordered_map.hpp>
#include <boost/assign/list_of.hpp>
#include <boost/regex.hpp>
#include <boost/algorithm/string/regex.hpp>

namespace YouCompleteMe {

namespace fs = boost::filesystem;

namespace {

const char *COMMENT_AND_STRING_REGEX =
  "//.*?$" // Anything following '//'
  "|"
  "#.*?$"  // Anything following '#'
  "|"
  "/\\*.*?\\*/"  // C-style comments, '/* ... */'
  "|"
  // Anything inside single quotes, '...', but mind the escaped quote and the
  // escaped slash (\\)
  "'(?:\\\\\\\\|\\\\'|.)*?'"
  "|"
  // Anything inside double quotes, "...", but mind the escaped double quote and
  // the escaped slash (\\)
  "\"(?:\\\\\\\\|\\\\\"|.)*?\"";

const char *IDENTIFIER_REGEX = "[_a-zA-Z]\\w*";

// For details on the tag format supported, see here for details:
// http://ctags.sourceforge.net/FORMAT
// TL;DR: The only supported format is the one Exuberant Ctags emits.
const char *TAG_REGEX =
  "^([^\\t\\n\\r]+)"  // The first field is the identifier
  "\\t"  // A TAB char is the field separator
  // The second field is the path to the file that has the identifier; either
  // absolute or relative to the tags file.
  "([^\\t\\n\\r]+)"
  "\\t.*?"  // Non-greedy everything
  "language:([^\\t\\n\\r]+)"  // We want to capture the language of the file
  ".*?$";


// List of languages Exuberant Ctags supports:
//   ctags --list-languages
// To map a language name to a filetype, see this file:
//   :e $VIMRUNTIME/filetype.vim
const boost::unordered_map< std::string, std::string > LANG_TO_FILETYPE =
  boost::assign::map_list_of
  ( std::string( "Ant"        ), std::string( "ant"        ) )
  ( std::string( "Asm"        ), std::string( "asm"        ) )
  ( std::string( "Awk"        ), std::string( "awk"        ) )
  ( std::string( "Basic"      ), std::string( "basic"      ) )
  ( std::string( "C++"        ), std::string( "cpp"        ) )
  ( std::string( "C#"         ), std::string( "cs"         ) )
  ( std::string( "C"          ), std::string( "c"          ) )
  ( std::string( "COBOL"      ), std::string( "cobol"      ) )
  ( std::string( "DosBatch"   ), std::string( "dosbatch"   ) )
  ( std::string( "Eiffel"     ), std::string( "eiffel"     ) )
  ( std::string( "Erlang"     ), std::string( "erlang"     ) )
  ( std::string( "Fortran"    ), std::string( "fortran"    ) )
  ( std::string( "HTML"       ), std::string( "html"       ) )
  ( std::string( "Java"       ), std::string( "java"       ) )
  ( std::string( "JavaScript" ), std::string( "javascript" ) )
  ( std::string( "Lisp"       ), std::string( "lisp"       ) )
  ( std::string( "Lua"        ), std::string( "lua"        ) )
  ( std::string( "Make"       ), std::string( "make"       ) )
  ( std::string( "MatLab"     ), std::string( "matlab"     ) )
  ( std::string( "OCaml"      ), std::string( "ocaml"      ) )
  ( std::string( "Pascal"     ), std::string( "pascal"     ) )
  ( std::string( "Perl"       ), std::string( "perl"       ) )
  ( std::string( "PHP"        ), std::string( "php"        ) )
  ( std::string( "Python"     ), std::string( "python"     ) )
  ( std::string( "REXX"       ), std::string( "rexx"       ) )
  ( std::string( "Ruby"       ), std::string( "ruby"       ) )
  ( std::string( "Scheme"     ), std::string( "scheme"     ) )
  ( std::string( "Sh"         ), std::string( "sh"         ) )
  ( std::string( "SLang"      ), std::string( "slang"      ) )
  ( std::string( "SML"        ), std::string( "sml"        ) )
  ( std::string( "SQL"        ), std::string( "sql"        ) )
  ( std::string( "Tcl"        ), std::string( "tcl"        ) )
  ( std::string( "Tex"        ), std::string( "tex"        ) )
  ( std::string( "Vera"       ), std::string( "vera"       ) )
  ( std::string( "Verilog"    ), std::string( "verilog"    ) )
  ( std::string( "VHDL"       ), std::string( "vhdl"       ) )
  ( std::string( "Vim"        ), std::string( "vim"        ) )
  ( std::string( "YACC"       ), std::string( "yacc"       ) );

const std::string NOT_FOUND = "YCMFOOBAR_NOT_FOUND";

}  // unnamed namespace


std::string RemoveIdentifierFreeText( std::string text ) {
  boost::erase_all_regex( text, boost::regex( COMMENT_AND_STRING_REGEX ) );
  return text;
}


std::vector< std::string > ExtractIdentifiersFromText(
  const std::string &text ) {
  std::string::const_iterator start = text.begin();
  std::string::const_iterator end   = text.end();

  boost::smatch matches;
  const boost::regex expression( IDENTIFIER_REGEX );

  std::vector< std::string > identifiers;

  while ( boost::regex_search( start, end, matches, expression ) ) {
    identifiers.push_back( matches[ 0 ] );
    start = matches[ 0 ].second;
  }

  return identifiers;
}


FiletypeIdentifierMap ExtractIdentifiersFromTagsFile(
  const fs::path &path_to_tag_file,
  const std::string &common_filetype) {
  FiletypeIdentifierMap filetype_identifier_map;
  std::string tags_file_contents;

  try {
    tags_file_contents = ReadUtf8File( path_to_tag_file );
  } catch ( ... ) {
    return filetype_identifier_map;
  }

  std::string::const_iterator start = tags_file_contents.begin();
  std::string::const_iterator end   = tags_file_contents.end();

  boost::smatch matches;
  const boost::regex expression( TAG_REGEX );
  const boost::match_flag_type options = boost::match_not_dot_newline;

  while ( boost::regex_search( start, end, matches, expression, options ) ) {
    start = matches[ 0 ].second;

    std::string language( matches[ 3 ] );
    std::string filetype = common_filetype.size() != 0
        ? common_filetype : FindWithDefault( LANG_TO_FILETYPE,
                                             language,
                                             NOT_FOUND );

    if ( filetype == NOT_FOUND )
      continue;

    std::string identifier( matches[ 1 ] );
    fs::path path( matches[ 2 ] );

    if ( path.is_relative() )
      path = path_to_tag_file.parent_path() / path;

    filetype_identifier_map[ filetype ][ path.string() ].push_back( identifier );
  }

  return filetype_identifier_map;
}

} // namespace YouCompleteMe
