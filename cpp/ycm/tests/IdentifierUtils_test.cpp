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

#include "IdentifierUtils.h"
#include <gtest/gtest.h>
#include <gmock/gmock.h>

using ::testing::ElementsAre;
using ::testing::WhenSorted;

namespace YouCompleteMe {


TEST( IdentifierUtilsTest, RemoveIdentifierFreeTextWorks ) {
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
                  "bar 'fo\\'oz\\nfoo'\n"
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

  EXPECT_STREQ( RemoveIdentifierFreeText(
                  "foo \n"
                  "bar \"fo\\\"oz\\nfoo\"\n"
                  "qux"
                ).c_str(),
                "foo \n"
                "bar \n"
                "qux" );
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

} // namespace YouCompleteMe

