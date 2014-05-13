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

#ifndef COMPLETIONDATA_H_2JCTF1NU
#define COMPLETIONDATA_H_2JCTF1NU

#include "standard.h"
#include <string>
#include <clang-c/Index.h>

namespace YouCompleteMe {

// This class holds pieces of information about a single completion coming from
// clang. These pieces are shown in Vim's UI in different ways.
//
// Normally, the completion menu looks like this (without square brackets):
//
//   [main completion text]  [kind]  [extra menu info]
//   [main completion text]  [kind]  [extra menu info]
//   [main completion text]  [kind]  [extra menu info]
//    ... (etc.) ...
//
// The user can also enable a "preview" window that will show extra information
// about a completion at the top of the buffer.
struct CompletionData {
  CompletionData() {}
  CompletionData( const CXCompletionResult &completion_result );

  // What should actually be inserted into the buffer. For a function like
  // "int foo(int x)", this is just "foo". Same for a data member like "foo_":
  // we insert just "foo_".
  std::string TextToInsertInBuffer() {
    return original_string_;
  }

  // Currently, here we show the full function signature (without the return
  // type) if the current completion is a function or just the raw TypedText if
  // the completion is, say, a data member. So for a function like "int foo(int
  // x)", this would be "foo(int x)". For a data member like "count_", it would
  // be just "count_".
  std::string MainCompletionText() {
    return everything_except_return_type_;
  }

  // This is extra info shown in the pop-up completion menu, after the
  // completion text and the kind. Currently we put the return type of the
  // function here, if any.
  std::string ExtraMenuInfo() {
    return return_type_;
  }

  // This is used to show extra information in vim's preview window. This is the
  // window that vim usually shows at the top of the buffer. This should be used
  // for extra information about the completion.
  std::string DetailedInfoForPreviewWindow() {
    return detailed_info_;
  }

  bool operator== ( const CompletionData &other ) const {
    return
      kind_ == other.kind_ &&
      everything_except_return_type_ == other.everything_except_return_type_ &&
      return_type_ == other.return_type_ &&
      original_string_ == other.original_string_;
    // detailed_info_ doesn't matter
  }

  std::string detailed_info_;

  std::string return_type_;

  // Vim's completion string "kind"
  //  'v' -> variable
  //  'f' -> function or method
  //  'm' -> member of struct/class (data member)
  //  't' -> typedef (but we're going to use it for types in general)
  //  'd' -> #define or macro
  char kind_;

  // The original, raw completion string. For a function like "int foo(int x)",
  // the original string is "foo". For a member data variable like "foo_", this
  // is just "foo_". This corresponds to clang's TypedText chunk of the
  // completion string.
  std::string original_string_;

  std::string everything_except_return_type_;

private:

  void ExtractDataFromChunk( CXCompletionString completion_string,
                             uint chunk_num,
                             bool &saw_left_paren,
                             bool &saw_function_params );
};

} // namespace YouCompleteMe


#endif /* end of include guard: COMPLETIONDATA_H_2JCTF1NU */
