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

#ifndef UNSAVEDFILE_H_0GIYZQL4
#define UNSAVEDFILE_H_0GIYZQL4

#include <string>

struct UnsavedFile {
  UnsavedFile() : filename_( "" ), contents_( "" ), length_( 0 ) {}

  std::string filename_;
  std::string contents_;
  unsigned long length_;

  // We need this to be able to export this struct to Python via Boost.Python's
  // methods. I have no clue why, but it won't compile without it.
  // TODO: report this problem on the Boost bug tracker, the default equality
  // operator should be more than adequate here
  bool operator== ( const UnsavedFile &other ) const {
    return
      filename_ == other.filename_ &&
      contents_ == other.contents_ &&
      length_   == other.length_;
  }
};


#endif /* end of include guard: UNSAVEDFILE_H_0GIYZQL4 */

