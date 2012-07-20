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

#ifndef COMPLETIONDATA_H_2JCTF1NU
#define COMPLETIONDATA_H_2JCTF1NU

namespace YouCompleteMe
{

struct CompletionData
{
  // What should actually be inserted into the buffer. For functions, this
  // should be the original string plus "("
  std::string TextToInsertInBuffer()
  {
    if ( kind_ == 'f' )
      return original_string_ + "(";
    return original_string_;
  }


  bool operator== ( const CompletionData &other ) const
  {
    return
      kind_ == other.kind_ &&
      original_string_ == other.original_string_ &&
      extra_menu_info_ == other.extra_menu_info_;
    // detailed_info_ doesn't matter
  }

  // This is used to show extra information in vim's preview window
  std::string detailed_info_;

  // This is extra info shown in the pop-up completion menu, after the
  // completion text and the kind
  std::string extra_menu_info_;

  // Vim's completion string "kind"
  //  'v' -> variable
  //  'f' -> function or method
  //  'm' -> member of struct/class (data member)
  //  't' -> typedef (but we're going to use it for types in general)
  //  'd' -> #define or macro
  char kind_;

  // The original, raw completion string. For a function like "int foo(int x)",
  // the original string is "foo". This corresponds to clang's TypedText chunk
  // of the completion string.
  std::string original_string_;
};

} // namespace YouCompleteMe


#endif /* end of include guard: COMPLETIONDATA_H_2JCTF1NU */
