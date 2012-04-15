// Copyright (C) 2011  Strahinja Markovic  <strahinja.markovic@gmail.com>
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
#include <gmock/gmock.h>
#include "Completer.h"
#include "Utils.h"
#include <boost/python.hpp>

using ::testing::ElementsAre;
using ::testing::WhenSorted;

namespace YouCompleteMe
{

namespace
{

std::vector<std::string> ToStringVector( const boost::python::list &pylist )
{
	std::vector<std::string> values;
  for (int i = 0; i < boost::python::len( pylist ); ++i)
  {
    values.push_back(
      boost::python::extract< std::string >( pylist[ i ] ) );
  }

  return values;
}

} // unnamed namespace

class CompleterTest : public ::testing::Test
{
 protected:
  virtual void SetUp()
  {
    Py_Initialize();
  }
};


TEST_F( CompleterTest, OneCandidate )
{
	Pylist candidates;
	candidates.append( "foobar" );

	Completer completer;
	completer.AddCandidatesToDatabase( candidates );

	Pylist results;
	completer.GetCandidatesForQuery( "fbr", results );

	EXPECT_THAT( ToStringVector( results ), ElementsAre( "foobar" ) );
}

TEST_F( CompleterTest, ManyCandidateSimple )
{
	Pylist candidates;
	candidates.append( "foobar" );
	candidates.append( "foobartest" );
	candidates.append( "Foobartest" );

	Completer completer;
	completer.AddCandidatesToDatabase( candidates );

	Pylist results;
	completer.GetCandidatesForQuery( "fbr", results );

	EXPECT_THAT( ToStringVector( results ),
	             WhenSorted( ElementsAre( "Foobartest",
	                                      "foobar",
	                                      "foobartest" ) ) );
}

TEST_F( CompleterTest, FirstCharSameAsQueryWins )
{
	Pylist candidates;
	candidates.append( "foobar" );
	candidates.append( "afoobar" );

	Completer completer;
	completer.AddCandidatesToDatabase( candidates );

	Pylist results;
	completer.GetCandidatesForQuery( "fbr", results );

	EXPECT_THAT( ToStringVector( results ),
	             ElementsAre( "foobar",
	                          "afoobar" ) );
}

TEST_F( CompleterTest, CompleteMatchForWordBoundaryCharsWins )
{
	Pylist candidates;
	candidates.append( "FooBarQux" );
	candidates.append( "FBaqux" );

	Completer completer;
	completer.AddCandidatesToDatabase( candidates );

	Pylist results;
	completer.GetCandidatesForQuery( "fbq", results );

	EXPECT_THAT( ToStringVector( results ),
	             ElementsAre( "FooBarQux",
	                          "FBaqux" ) );
}

} // namespace YouCompleteMe

