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
#include "Candidate.h"

namespace YouCompleteMe
{

TEST( CandidateTest, TextValid )
{
  std::string text = "foo";
  Candidate candidate( text );

  EXPECT_EQ( text, candidate.Text() );
}

TEST( CandidateTest, MatchesQueryBitsetWhenMatch )
{
  Candidate candidate( "foobaaar" );

  EXPECT_TRUE( candidate.MatchesQueryBitset(
                LetterBitsetFromString( "foobaaar" ) ) );
  EXPECT_TRUE( candidate.MatchesQueryBitset(
                LetterBitsetFromString( "fobar" ) ) );
  EXPECT_TRUE( candidate.MatchesQueryBitset(
                LetterBitsetFromString( "rabof" ) ) );
  EXPECT_TRUE( candidate.MatchesQueryBitset(
                LetterBitsetFromString( "bfroa" ) ) );
  EXPECT_TRUE( candidate.MatchesQueryBitset(
                LetterBitsetFromString( "fbr" ) ) );
  EXPECT_TRUE( candidate.MatchesQueryBitset(
                LetterBitsetFromString( "r" ) ) );
  EXPECT_TRUE( candidate.MatchesQueryBitset(
                LetterBitsetFromString( "bbb" ) ) );
  EXPECT_TRUE( candidate.MatchesQueryBitset(
                LetterBitsetFromString( "" ) ) );
}

TEST( CandidateTest, DoesntMatchQueryBitset )
{
  Candidate candidate( "foobar" );

  EXPECT_FALSE( candidate.MatchesQueryBitset(
                  LetterBitsetFromString( "foobare" ) ) );
  EXPECT_FALSE( candidate.MatchesQueryBitset(
                  LetterBitsetFromString( "gggg" ) ) );
  EXPECT_FALSE( candidate.MatchesQueryBitset(
                  LetterBitsetFromString( "x" ) ) );
  EXPECT_FALSE( candidate.MatchesQueryBitset(
                  LetterBitsetFromString( "nfoobar" ) ) );
  EXPECT_FALSE( candidate.MatchesQueryBitset(
                  LetterBitsetFromString( "fbrmmm" ) ) );
}

TEST( CandidateTest, QueryMatchResultIsSubsequence )
{
  Candidate candidate( "foobaaar" );

  EXPECT_TRUE( candidate.QueryMatchResult( "foobaaar" ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "fobar"    ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "fbr"      ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "f"        ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "o"        ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "a"        ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "r"        ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "b"        ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "bar"      ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "oa"       ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "obr"      ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "oo"       ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "aaa"      ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( ""         ).IsSubsequence() );
}

TEST( CandidateTest, QueryMatchResultIsntSubsequence )
{
  Candidate candidate( "foobaaar" );

  EXPECT_FALSE( candidate.QueryMatchResult( "foobra"    ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "frb"       ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "brf"       ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "x"         ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "9"         ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "-"         ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "~"         ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( " "         ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "rabof"     ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "oabfr"     ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "ooo"       ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "baaara"    ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "ffoobaaar" ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "xfoobaaar" ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( " foobaaar" ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "foobaaar " ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "ff"        ).IsSubsequence() );
}

} // namespace YouCompleteMe
