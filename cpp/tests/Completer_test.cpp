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

Pylist Candidates( const std::string &a,
                   const std::string &b = std::string(),
                   const std::string &c = std::string(),
                   const std::string &d = std::string(),
                   const std::string &e = std::string(),
                   const std::string &f = std::string(),
                   const std::string &g = std::string(),
                   const std::string &h = std::string(),
                   const std::string &i = std::string() )
{
  Pylist candidates;
	candidates.append( a );
	if ( !b.empty() )
    candidates.append( b );
	if ( !c.empty() )
    candidates.append( c );
	if ( !d.empty() )
    candidates.append( d );
	if ( !e.empty() )
    candidates.append( e );
	if ( !f.empty() )
    candidates.append( f );
	if ( !g.empty() )
    candidates.append( g );
	if ( !h.empty() )
    candidates.append( h );
	if ( !i.empty() )
    candidates.append( i );

  return candidates;
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
	Pylist results;
	Completer( Candidates( "foobar" ) ).GetCandidatesForQuery( "fbr", results );

	EXPECT_THAT( ToStringVector( results ), ElementsAre( "foobar" ) );
}

TEST_F( CompleterTest, ManyCandidateSimple )
{
	Pylist results;
	Completer( Candidates(
	        "foobar",
	        "foobartest",
	        "Foobartest" ) ).GetCandidatesForQuery( "fbr", results );

	EXPECT_THAT( ToStringVector( results ),
	             WhenSorted( ElementsAre( "Foobartest",
	                                      "foobar",
	                                      "foobartest" ) ) );
}

TEST_F( CompleterTest, FirstCharSameAsQueryWins )
{
	Pylist results;
	Completer( Candidates(
	        "foobar",
	        "afoobar" ) ).GetCandidatesForQuery( "fbr", results );

	EXPECT_THAT( ToStringVector( results ),
	             ElementsAre( "foobar",
	                          "afoobar" ) );
}

TEST_F( CompleterTest, CompleteMatchForWordBoundaryCharsWins )
{
	Pylist results;
	Completer( Candidates(
	        "FooBarQux",
	        "FBaqux" ) ).GetCandidatesForQuery( "fbq", results );

	EXPECT_THAT( ToStringVector( results ),
	             ElementsAre( "FooBarQux",
	                          "FBaqux" ) );

	Pylist results2;
	Completer( Candidates(
	        "CompleterTest",
	        "CompleteMatchForWordBoundaryCharsWins"
	        ) ).GetCandidatesForQuery( "ct", results2 );

	EXPECT_THAT( ToStringVector( results2 ),
	             ElementsAre( "CompleterTest",
	                          "CompleteMatchForWordBoundaryCharsWins" ) );

	Pylist results3;
	Completer( Candidates(
	        "FooBar",
	        "FooBarRux"
	        ) ).GetCandidatesForQuery( "fbr", results3 );

	EXPECT_THAT( ToStringVector( results3 ),
	             ElementsAre( "FooBarRux",
	                          "FooBar" ) );
}

TEST_F( CompleterTest, RatioUtilizationTieBreak )
{
	Pylist results;
	Completer( Candidates(
	        "FooBarQux",
	        "FooBarQuxZaa" ) ).GetCandidatesForQuery( "fbq", results );

	EXPECT_THAT( ToStringVector( results ),
	             ElementsAre( "FooBarQux",
	                          "FooBarQuxZaa" ) );
}

TEST_F( CompleterTest, ShorterCandidateWins )
{
	Pylist results;
	Completer( Candidates(
	        "FooBarQux",
	        "FaBarQux" ) ).GetCandidatesForQuery( "fbq", results );

	EXPECT_THAT( ToStringVector( results ),
	             ElementsAre( "FaBarQux",
	                          "FooBarQux" ) );

	Pylist results2;
	Completer( Candidates(
	        "CompleterT",
	        "CompleterTest" ) ).GetCandidatesForQuery( "co", results2 );

	EXPECT_THAT( ToStringVector( results2 ),
	             ElementsAre( "CompleterT",
	                          "CompleterTest" ) );
}

} // namespace YouCompleteMe

