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
#include "TestUtils.h"
#include <gtest/gtest.h>
#include <gmock/gmock.h>

using ::testing::ElementsAre;

namespace YouCompleteMe
{

extern const char *CLANG_OPTIONS_FILENAME;

TEST( ClangUtilsTest, SanitizeClangFlagsWorks )
{
	EXPECT_THAT( SanitizeClangFlags( StringVector(
	             "foo",
	             "-arch",
	             "die",
	             "-arch",
	             "die2",
	             "bar" ) ),
	             ElementsAre( "foo",
	                          "bar" ) );

	EXPECT_THAT( SanitizeClangFlags( StringVector(
	             "foo",
	             "-arch",
	             "die" ) ),
	             ElementsAre( "foo" ) );

	EXPECT_THAT( SanitizeClangFlags( StringVector(
	             "-arch",
	             "die" ) ),
	             ElementsAre() );

	EXPECT_THAT( SanitizeClangFlags( StringVector(
	             "-arch" ) ),
	             ElementsAre() );
}


TEST( ClangUtilsTest, SplitFlagsWorks )
{
	EXPECT_THAT( SplitFlags( "-f     --bar=qux" ),
	             ElementsAre( "-f",
	                          "--bar=qux" ) );

	EXPECT_THAT( SplitFlags( "foo" ),
	             ElementsAre( "foo" ) );

	EXPECT_THAT( SplitFlags( "foo \n\n\t\v bar" ),
	             ElementsAre( "foo",
	                          "bar" ) );

	EXPECT_THAT( SplitFlags( "  a '  a b c ' q  " ),
	             ElementsAre( "a",
	                          "'  a b c '",
	                          "q" ) );

	EXPECT_THAT( SplitFlags( "-I../a/b/c -I\"foo/b/c\" -I\"a c\" -I'a/b/c'" ),
	             ElementsAre( "-I../a/b/c",
	                          "-I\"foo/b/c\"",
	                          "-I\"a c\"",
	                          "-I'a/b/c'" ) );
}


TEST( ClangUtilsTest, GetNearestClangOptionsWorks )
{
  fs::path temp_root = fs::temp_directory_path() / fs::unique_path();
  fs::create_directories( temp_root );

  std::string contents = "foo bar";
  WriteUtf8File( temp_root / fs::path( CLANG_OPTIONS_FILENAME ), contents );

  fs::path parent = temp_root / fs::unique_path();
  fs::create_directories( parent );

  EXPECT_STREQ( contents.c_str(),
                GetNearestClangOptions(
                    ( parent / fs::unique_path() ).string() ).c_str() );
}

} // namespace YouCompleteMe

