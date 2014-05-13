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

#include <gtest/gtest.h>
#include "LetterNodeListMap.h"

namespace YouCompleteMe {

TEST( IndexForCharTest, Basic ) {
  EXPECT_EQ( static_cast<int>( 'a' ), IndexForChar( 'a' ) );
  EXPECT_EQ( static_cast<int>( 'a' ), IndexForChar( 'A' ) );
  EXPECT_EQ( static_cast<int>( 'z' ), IndexForChar( 'z' ) );
  EXPECT_EQ( static_cast<int>( 'z' ), IndexForChar( 'Z' ) );

  EXPECT_EQ( static_cast<int>( '[' ), IndexForChar( '[' ) );
  EXPECT_EQ( static_cast<int>( ' ' ), IndexForChar( ' ' ) );
  EXPECT_EQ( static_cast<int>( '~' ), IndexForChar( '~' ) );
}

} // namespace YouCompleteMe

