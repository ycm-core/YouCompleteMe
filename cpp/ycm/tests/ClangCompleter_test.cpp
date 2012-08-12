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

#include "ClangCompleter.h"
#include "CompletionData.h"
#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include <boost/filesystem.hpp>
namespace fs = boost::filesystem;

using ::testing::ElementsAre;
using ::testing::WhenSorted;

namespace YouCompleteMe
{

TEST( ClangCompleterTest, CandidatesForLocationInFile )
{
  fs::path path_to_testdata = fs::current_path() / fs::path( "testdata" );
  fs::path test_file = path_to_testdata / fs::path( "basic.cpp" );

  ClangCompleter completer;
  std::vector< CompletionData > completions =
    completer.CandidatesForLocationInFile(
        test_file.string(),
        11,
        7,
        std::vector< UnsavedFile >(),
        std::vector< std::string >() );

  EXPECT_TRUE( !completions.empty() );
}


TEST( ClangCompleterTest, CandidatesForQueryAndLocationInFileAsync )
{
  fs::path path_to_testdata = fs::current_path() / fs::path( "testdata" );
  fs::path test_file = path_to_testdata / fs::path( "basic.cpp" );

  ClangCompleter completer;
  completer.EnableThreading();

  Future< AsyncCompletions > completions_future =
    completer.CandidatesForQueryAndLocationInFileAsync(
        "",
        test_file.string(),
        11,
        7,
        std::vector< UnsavedFile >(),
        std::vector< std::string >() );

  completions_future.Wait();

  EXPECT_TRUE( !completions_future.GetResults()->empty() );
}

} // namespace YouCompleteMe


