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

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "Completer.h"
#include "Utils.h"

using ::testing::ElementsAre;
using ::testing::WhenSorted;

namespace YouCompleteMe
{

namespace
{

std::vector< std::string > Candidates( const std::string &a,
                                       const std::string &b = std::string(),
                                       const std::string &c = std::string(),
                                       const std::string &d = std::string(),
                                       const std::string &e = std::string(),
                                       const std::string &f = std::string(),
                                       const std::string &g = std::string(),
                                       const std::string &h = std::string(),
                                       const std::string &i = std::string() )
{
  std::vector< std::string > candidates;
	candidates.push_back( a );
	if ( !b.empty() )
    candidates.push_back( b );
	if ( !c.empty() )
    candidates.push_back( c );
	if ( !d.empty() )
    candidates.push_back( d );
	if ( !e.empty() )
    candidates.push_back( e );
	if ( !f.empty() )
    candidates.push_back( f );
	if ( !g.empty() )
    candidates.push_back( g );
	if ( !h.empty() )
    candidates.push_back( h );
	if ( !i.empty() )
    candidates.push_back( i );

  return candidates;
}

} // unnamed namespace


TEST( CompleterTest, OneCandidate )
{
	EXPECT_THAT( Completer( Candidates(
               "foobar" ) ).CandidatesForQuery( "fbr" ),
	             ElementsAre( "foobar" ) );
}

TEST( CompleterTest, ManyCandidateSimple )
{
	EXPECT_THAT( Completer( Candidates(
               "foobar",
               "foobartest",
               "Foobartest" ) ).CandidatesForQuery( "fbr" ),
	             WhenSorted( ElementsAre( "Foobartest",
	                                      "foobar",
	                                      "foobartest" ) ) );
}

TEST( CompleterTest, FirstCharSameAsQueryWins )
{
	EXPECT_THAT( Completer( Candidates(
               "foobar",
               "afoobar" ) ).CandidatesForQuery( "fbr" ),
	             ElementsAre( "foobar",
	                          "afoobar" ) );
}

TEST( CompleterTest, CompleteMatchForWordBoundaryCharsWins )
{
	EXPECT_THAT( Completer( Candidates(
               "FooBarQux",
               "FBaqux" ) ).CandidatesForQuery( "fbq" ),
	             ElementsAre( "FooBarQux",
	                          "FBaqux" ) );

	EXPECT_THAT( Completer( Candidates(
               "CompleterTest",
               "CompleteMatchForWordBoundaryCharsWins" ) )
                  .CandidatesForQuery( "ct" ),
	             ElementsAre( "CompleterTest",
	                          "CompleteMatchForWordBoundaryCharsWins" ) );

	EXPECT_THAT( Completer( Candidates(
               "FooBar",
               "FooBarRux" ) ).CandidatesForQuery( "fbr" ),
	             ElementsAre( "FooBarRux",
	                          "FooBar" ) );
}

TEST( CompleterTest, RatioUtilizationTieBreak )
{
	EXPECT_THAT( Completer( Candidates(
               "aGaaFooBarQux",
               "aBaafbq" ) ).CandidatesForQuery( "fbq" ),
	             ElementsAre( "aGaaFooBarQux",
	                          "aBaafbq" ) );

	EXPECT_THAT( Completer( Candidates(
               "aFooBarQux",
               "afbq" ) ).CandidatesForQuery( "fbq" ),
	             ElementsAre( "aFooBarQux",
	                          "afbq" ) );

	EXPECT_THAT( Completer( Candidates(
               "acaaCaaFooGxx",
               "aCaafoog" ) ).CandidatesForQuery( "caafoo" ),
	             ElementsAre( "acaaCaaFooGxx",
	                          "aCaafoog" ) );

	EXPECT_THAT( Completer( Candidates(
               "acaaCaaFooGxx",
               "aCaafoog" ) ).CandidatesForQuery( "caaFoo" ),
	             ElementsAre( "acaaCaaFooGxx",
	                          "aCaafoog" ) );

	EXPECT_THAT( Completer( Candidates(
               "FooBarQux",
               "FooBarQuxZaa" ) ).CandidatesForQuery( "fbq" ),
	             ElementsAre( "FooBarQux",
	                          "FooBarQuxZaa" ) );

	EXPECT_THAT( Completer( Candidates(
               "FooBar",
               "FooBarRux" ) ).CandidatesForQuery( "fba" ),
	             ElementsAre( "FooBar",
	                          "FooBarRux" ) );
}

TEST( CompleterTest, QueryPrefixOfCandidateWins )
{
	EXPECT_THAT( Completer( Candidates(
               "foobar",
               "fbaroo" ) ).CandidatesForQuery( "foo" ),
	             ElementsAre( "foobar",
	                          "fbaroo" ) );
}

TEST( CompleterTest, LowerMatchCharIndexSumWins )
{
	EXPECT_THAT( Completer( Candidates(
              "ratio_of_word_boundary_chars_in_query_",
              "first_char_same_in_query_and_text_") )
                 .CandidatesForQuery( "charinq" ),
              ElementsAre( "first_char_same_in_query_and_text_",
                           "ratio_of_word_boundary_chars_in_query_") );

	EXPECT_THAT( Completer( Candidates(
               "barfooq",
               "barquxfoo" ) ).CandidatesForQuery( "foo" ),
	             ElementsAre( "barfooq",
                            "barquxfoo") );

	EXPECT_THAT( Completer( Candidates(
               "xxxxxxabc",
               "xxabcxxxx" ) ).CandidatesForQuery( "abc" ),
	             ElementsAre( "xxabcxxxx",
                            "xxxxxxabc") );

	EXPECT_THAT( Completer( Candidates(
               "FooBarQux",
               "FaBarQux" ) ).CandidatesForQuery( "fbq" ),
	             ElementsAre( "FaBarQux",
	                          "FooBarQux" ) );
}

TEST( CompleterTest, ShorterCandidateWins )
{
	EXPECT_THAT( Completer( Candidates(
               "CompleterT",
               "CompleterTest" ) ).CandidatesForQuery( "co" ),
	             ElementsAre( "CompleterT",
	                          "CompleterTest" ) );

	EXPECT_THAT( Completer( Candidates(
               "CompleterT",
               "CompleterTest" ) ).CandidatesForQuery( "plet" ),
	             ElementsAre( "CompleterT",
	                          "CompleterTest" ) );
}

TEST( CompleterTest, SameLowercaseCandidateWins )
{
	EXPECT_THAT( Completer( Candidates(
               "foobar",
               "Foobar" ) ).CandidatesForQuery( "foo" ),
	             ElementsAre( "foobar",
	                          "Foobar" ) );
}

// TODO: tests for filepath and filetype candidate storing

} // namespace YouCompleteMe

