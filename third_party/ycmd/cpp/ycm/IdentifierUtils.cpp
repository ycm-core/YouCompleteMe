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

const char *const COMMENT_AND_STRING_REGEX =
  "//.*?$" // Anything following '//'
  "|"
  "#.*?$"  // Anything following '#'
  "|"
  "/\\*.*?\\*/"  // C-style comments, '/* ... */'
  "|"
  // Anything inside single quotes, '...', but mind:
  //  1. that the starting single quote is not escaped
  //  2. the escaped slash (\\)
  //  3. the escaped single quote inside the string
  // "(?<!\\\\)'(?:\\\\\\\\|\\\\'|.)*?'"
  "(?<!\\\\)'(?:\\\\\\\\|\\\\'|.)*?'"
  "|"
  // Anything inside double quotes, "...", but mind:
  //  1. that the starting double quote is not escaped
  //  2. the escaped slash (\\)
  //  3. the escaped double quote inside the string
  "(?<!\\\\)\"(?:\\\\\\\\|\\\\\"|.)*?\"";

const char *const IDENTIFIER_REGEX = "[_a-zA-Z]\\w*";

// For details on the tag format supported, see here for details:
// http://ctags.sourceforge.net/FORMAT
// TL;DR: The only supported format is the one Exuberant Ctags emits.
const char *const TAG_REGEX =
  "^([^\\t\\n\\r]+)"  // The first field is the identifier
  "\\t"  // A TAB char is the field separator
  // The second field is the path to the file that has the identifier; either
  // absolute or relative to the tags file.
  "([^\\t\\n\\r]+)"
  "\\t.*?"  // Non-greedy everything
  "language:([^\\t\\n\\r]+)"  // We want to capture the language of the file
  ".*?$";

// Only used as the equality comparer for the below unordered_map which stores
// const char* pointers and not std::string but needs to hash based on string
// values and not pointer values.
// When passed a const char* this will create a temporary std::string for
// comparison, but it's fast enough for our use case.
struct StringEqualityComparer :
    std::binary_function< std::string, std::string, bool > {
  bool operator()( const std::string &a, const std::string &b ) const {
    return a == b;
  }
};

// List of languages Exuberant Ctags supports:
//   ctags --list-languages
// To map a language name to a filetype, see this file:
//   :e $VIMRUNTIME/filetype.vim
// This is a map of const char* and not std::string to prevent issues with
// static initialization.
const boost::unordered_map < const char *,
      const char *,
      boost::hash< std::string >,
      StringEqualityComparer > LANG_TO_FILETYPE =
        boost::assign::map_list_of
        ( "Ant"        , "ant"        )
        ( "Asm"        , "asm"        )
        ( "Awk"        , "awk"        )
        ( "Basic"      , "basic"      )
        ( "C++"        , "cpp"        )
        ( "C#"         , "cs"         )
        ( "C"          , "c"          )
        ( "COBOL"      , "cobol"      )
        ( "DosBatch"   , "dosbatch"   )
        ( "Eiffel"     , "eiffel"     )
        ( "Erlang"     , "erlang"     )
        ( "Fortran"    , "fortran"    )
        ( "HTML"       , "html"       )
        ( "Java"       , "java"       )
        ( "JavaScript" , "javascript" )
        ( "Lisp"       , "lisp"       )
        ( "Lua"        , "lua"        )
        ( "Make"       , "make"       )
        ( "MatLab"     , "matlab"     )
        ( "OCaml"      , "ocaml"      )
        ( "Pascal"     , "pascal"     )
        ( "Perl"       , "perl"       )
        ( "PHP"        , "php"        )
        ( "Python"     , "python"     )
        ( "REXX"       , "rexx"       )
        ( "Ruby"       , "ruby"       )
        ( "Scheme"     , "scheme"     )
        ( "Sh"         , "sh"         )
        ( "SLang"      , "slang"      )
        ( "SML"        , "sml"        )
        ( "SQL"        , "sql"        )
        ( "Tcl"        , "tcl"        )
        ( "Tex"        , "tex"        )
        ( "Vera"       , "vera"       )
        ( "Verilog"    , "verilog"    )
        ( "VHDL"       , "vhdl"       )
        ( "Vim"        , "vim"        )
        ( "YACC"       , "yacc"       );

const char *const NOT_FOUND = "YCMFOOBAR_NOT_FOUND";

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
  const fs::path &path_to_tag_file ) {
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
    std::string filetype = FindWithDefault( LANG_TO_FILETYPE,
                                            language.c_str(),
                                            NOT_FOUND );

    if ( filetype == NOT_FOUND )
      continue;

    std::string identifier( matches[ 1 ] );
    fs::path path( matches[ 2 ].str() );

    if ( path.is_relative() )
      path = path_to_tag_file.parent_path() / path;

    filetype_identifier_map[ filetype ][ path.string() ].push_back( identifier );
  }

  return filetype_identifier_map;
}

} // namespace YouCompleteMe
