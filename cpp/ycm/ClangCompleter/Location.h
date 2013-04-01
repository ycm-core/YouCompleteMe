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

#ifndef LOCATION_H_6TLFQH4I
#define LOCATION_H_6TLFQH4I

#include "standard.h"
#include <string>
#include <clang-c/Index.h>

namespace YouCompleteMe {

struct Location {
  // Creates an invalid location
  Location()
    : line_number_( 0 ),
      column_number_( 0 ),
      filename_( "" ) {}

  Location( const std::string &filename, uint line, uint column )
    : line_number_( line ),
      column_number_( column ),
      filename_( filename ) {}

  bool operator== ( const Location &other ) const {
    return
      line_number_ == other.line_number_ &&
      column_number_ == other.column_number_ &&
      filename_ == other.filename_;
  }

  bool IsValid() {
    return !filename_.empty();
  }

  uint line_number_;
  uint column_number_;

  // The full, absolute path
  std::string filename_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: LOCATION_H_6TLFQH4I */
