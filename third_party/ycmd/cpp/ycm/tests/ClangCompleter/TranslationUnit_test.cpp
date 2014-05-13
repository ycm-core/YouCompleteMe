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

#include "TranslationUnit.h"
#include "exceptions.h"
#include "Utils.h"
#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include <clang-c/Index.h>

#include <boost/filesystem.hpp>
namespace fs = boost::filesystem;

using ::testing::ElementsAre;
using ::testing::WhenSorted;

namespace YouCompleteMe {

class TranslationUnitTest : public ::testing::Test {
protected:
  virtual void SetUp() {
    clang_index_ = clang_createIndex( 0, 0 );
  }

  virtual void TearDown() {
    clang_disposeIndex( clang_index_ );
  }

  CXIndex clang_index_;
};


TEST_F( TranslationUnitTest, ExceptionThrownOnParseFailure ) {
  fs::path test_file = fs::temp_directory_path() / fs::unique_path();
  std::string junk = "#&9112(^(^#>@(^@!@(&#@a}}}}{nthoeu\n&&^^&^&!#%%@@!aeu";
  WriteUtf8File( test_file, junk );

  std::vector< std::string > flags;
  flags.push_back( junk );

  EXPECT_THROW( TranslationUnit( test_file.string(),
                                 std::vector< UnsavedFile >(),
                                 flags,
                                 NULL ),
                ClangParseError );
}

TEST_F( TranslationUnitTest, GoToDefinitionWorks ) {
  fs::path path_to_testdata = fs::current_path() / fs::path( "testdata" );
  fs::path test_file = path_to_testdata / fs::path( "goto.cpp" );

  TranslationUnit unit( test_file.string(),
                        std::vector< UnsavedFile >(),
                        std::vector< std::string >(),
                        clang_index_ );

  Location location = unit.GetDefinitionLocation(
                        15,
                        3,
                        std::vector< UnsavedFile >() );

  EXPECT_EQ( 1, location.line_number_ );
  EXPECT_EQ( 8, location.column_number_ );
  EXPECT_TRUE( !location.filename_.empty() );
}

TEST_F( TranslationUnitTest, GoToDefinitionFails ) {
  fs::path path_to_testdata = fs::current_path() / fs::path( "testdata" );
  fs::path test_file = path_to_testdata / fs::path( "goto.cpp" );

  TranslationUnit unit( test_file.string(),
                        std::vector< UnsavedFile >(),
                        std::vector< std::string >(),
                        clang_index_ );

  Location location = unit.GetDefinitionLocation(
                        17,
                        3,
                        std::vector< UnsavedFile >() );

  EXPECT_FALSE( location.IsValid() );
}

TEST_F( TranslationUnitTest, GoToDeclarationWorks ) {
  fs::path path_to_testdata = fs::current_path() / fs::path( "testdata" );
  fs::path test_file = path_to_testdata / fs::path( "goto.cpp" );

  TranslationUnit unit( test_file.string(),
                        std::vector< UnsavedFile >(),
                        std::vector< std::string >(),
                        clang_index_ );

  Location location = unit.GetDeclarationLocation(
                        17,
                        3,
                        std::vector< UnsavedFile >() );

  EXPECT_EQ( 12, location.line_number_ );
  EXPECT_EQ( 8, location.column_number_ );
  EXPECT_TRUE( !location.filename_.empty() );
}

} // namespace YouCompleteMe
