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

#include "TranslationUnit.h"
#include "exceptions.h"
#include "Utils.h"
#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include <boost/filesystem.hpp>
namespace fs = boost::filesystem;

using ::testing::ElementsAre;
using ::testing::WhenSorted;

namespace YouCompleteMe {

TEST( TranslationUnitTest, ExceptionThrownOnParseFailure ) {
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


} // namespace YouCompleteMe
