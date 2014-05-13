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
#include "TestUtils.h"
#include "IdentifierDatabase.h"

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <boost/filesystem.hpp>

namespace YouCompleteMe {

namespace fs = boost::filesystem;
using ::testing::ElementsAre;
using ::testing::ContainerEq;
using ::testing::WhenSorted;

TEST( IdentifierUtilsTest, RemoveIdentifierFreeTextComments ) {
  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar //foo \n"
                  "qux"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux" );

  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar #foo \n"
                  "qux"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux" );

  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar /* foo \n"
                  " foo2 */\n"
                  "qux"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux" );
}


TEST( IdentifierUtilsTest, RemoveIdentifierFreeTextSimpleStrings ) {
  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar 'foo'\n"
                  "qux"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux" );

  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar \"foo\"\n"
                  "qux"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux" );
}


TEST( IdentifierUtilsTest, RemoveIdentifierFreeTextEscapedQuotesInStrings ) {
  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar 'fo\\'oz\\nfoo'\n"
                  "qux"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux" );


  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar \"fo\\\"oz\\nfoo\"\n"
                  "qux"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux" );
}


TEST( IdentifierUtilsTest, RemoveIdentifierFreeTextEscapedSlashesInStrings ) {
  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar \"fo\\\\\"baz\n"
                  "qux \"qwe\""
                ).c_str(),
                "foo \n"
                "bar baz\n"
                "qux " );

  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo '\\\\'\n"
                  "bar '\\\\'\n"
                  "qux '\\\\'"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux " );
}


TEST( IdentifierUtilsTest, RemoveIdentifierFreeTextEscapedQuotesStartStrings ) {
  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "\\\"foo\\\""
                  "'\"'"
                  "'bar' zoo'test'"
                ).c_str(),
                "\\\"foo\\\" zoo" );

  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "\\'foo\\'"
                  "\"'\""
                  "\"bar\" zoo\"test\""
                ).c_str(),
                "\\'foo\\' zoo" );
}


TEST( IdentifierUtilsTest, ExtractIdentifiersFromTextWorks ) {
  EXPECT_THAT( ExtractIdentifiersFromText(
                 "foo $_bar \n&BazGoo\n FOO= !!! '-' - _ (x) one-two !moo [qqq]"
               ),
               ElementsAre( "foo",
                            "_bar",
                            "BazGoo",
                            "FOO",
                            "_",
                            "x",
                            "one",
                            "two",
                            "moo",
                            "qqq" ) );

}


TEST( IdentifierUtilsTest, ExtractIdentifiersFromTagsFileWorks ) {
  fs::path testfile = PathToTestFile( "basic.tags" );
  fs::path testfile_parent = testfile.parent_path();

  FiletypeIdentifierMap expected;
  expected[ "cpp" ][ ( testfile_parent / "foo" ).string() ]
  .push_back( "i1" );
  expected[ "cpp" ][ ( testfile_parent / "bar" ).string() ]
  .push_back( "i1" );
  expected[ "cpp" ][ ( testfile_parent / "foo" ).string() ]
  .push_back( "foosy" );
  expected[ "cpp" ][ ( testfile_parent / "bar" ).string() ]
  .push_back( "fooaaa" );

  expected[ "c" ][ "/foo/zoo" ].push_back( "Floo::goo" );
  expected[ "c" ][ "/foo/goo maa" ].push_back( "!goo" );

  expected[ "cs" ][ "/m_oo" ].push_back( "#bleh" );

  EXPECT_THAT( ExtractIdentifiersFromTagsFile( testfile ),
               ContainerEq( expected ) );
}

} // namespace YouCompleteMe

