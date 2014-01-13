// Copyright (C) 2013  Google Inc.
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

#ifndef RANGE_H_4MFTIGQK
#define RANGE_H_4MFTIGQK

#include "standard.h"
#include "Location.h"

namespace YouCompleteMe {

// Half-open, [start, end>
struct Range {
  Range() {}

  Range( const Location &start_location, const Location &end_location )
    : start_( start_location ), end_( end_location ) {}

  Range( const CXSourceRange &range );

  bool operator== ( const Range &other ) const {
    return
      start_ == other.start_ &&
      end_ == other.end_;
  }

  Location start_;
  Location end_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: RANGE_H_4MFTIGQK */
