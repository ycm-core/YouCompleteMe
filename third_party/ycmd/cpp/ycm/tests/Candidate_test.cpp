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

#include <gtest/gtest.h>
#include "Candidate.h"
#include "Result.h"

namespace YouCompleteMe {

TEST( GetWordBoundaryCharsTest, SimpleOneWord ) {
  EXPECT_EQ( "s", GetWordBoundaryChars( "simple" ) );
}

TEST( GetWordBoundaryCharsTest, UnderscoreInMiddle ) {
  EXPECT_EQ( "sf", GetWordBoundaryChars( "simple_foo" ) );
}

TEST( GetWordBoundaryCharsTest, UnderscoreStart ) {
  EXPECT_EQ( "s", GetWordBoundaryChars( "_simple" ) );
}

TEST( GetWordBoundaryCharsTest, ManyUnderscoreStart ) {
  EXPECT_EQ( "s", GetWordBoundaryChars( "___simple" ) );
}

TEST( GetWordBoundaryCharsTest, UnderscoreStartAndInMiddle ) {
  EXPECT_EQ( "sf", GetWordBoundaryChars( "_simple_foo" ) );
}

TEST( GetWordBoundaryCharsTest, ManyUnderscoreStartAndInMiddle ) {
  EXPECT_EQ( "sf", GetWordBoundaryChars( "___simple__foo" ) );
}

TEST( GetWordBoundaryCharsTest, SimpleCapitalStart ) {
  EXPECT_EQ( "s", GetWordBoundaryChars( "Simple" ) );
}

TEST( GetWordBoundaryCharsTest, SimpleCapitalTwoWord ) {
  EXPECT_EQ( "ss", GetWordBoundaryChars( "SimpleStuff" ) );
}

TEST( GetWordBoundaryCharsTest, SimpleCapitalTwoWordUnderscoreMiddle ) {
  EXPECT_EQ( "ss", GetWordBoundaryChars( "Simple_Stuff" ) );
}

TEST( GetWordBoundaryCharsTest, JavaCase ) {
  EXPECT_EQ( "ssf", GetWordBoundaryChars( "simpleStuffFoo" ) );
}

TEST( GetWordBoundaryCharsTest, UppercaseSequence ) {
  EXPECT_EQ( "ss", GetWordBoundaryChars( "simpleSTUFF" ) );
}

TEST( GetWordBoundaryCharsTest, UppercaseSequenceInMiddle ) {
  EXPECT_EQ( "ss", GetWordBoundaryChars( "simpleSTUFFfoo" ) );
}

TEST( GetWordBoundaryCharsTest, UppercaseSequenceInMiddleUnderscore ) {
  EXPECT_EQ( "ssf", GetWordBoundaryChars( "simpleSTUFF_Foo" ) );
}

TEST( GetWordBoundaryCharsTest, UppercaseSequenceInMiddleUnderscoreLowercase ) {
  EXPECT_EQ( "ssf", GetWordBoundaryChars( "simpleSTUFF_foo" ) );
}

TEST( GetWordBoundaryCharsTest, AllCapsSimple ) {
  EXPECT_EQ( "s", GetWordBoundaryChars( "SIMPLE" ) );
}

TEST( GetWordBoundaryCharsTest, AllCapsUnderscoreStart ) {
  EXPECT_EQ( "s", GetWordBoundaryChars( "_SIMPLE" ) );
}

TEST( GetWordBoundaryCharsTest, AllCapsUnderscoreMiddle ) {
  EXPECT_EQ( "ss", GetWordBoundaryChars( "SIMPLE_STUFF" ) );
}

TEST( GetWordBoundaryCharsTest, AllCapsUnderscoreMiddleAndStart ) {
  EXPECT_EQ( "ss", GetWordBoundaryChars( "_SIMPLE_STUFF" ) );
}

TEST( CandidateTest, TextValid ) {
  std::string text = "foo";
  Candidate candidate( text );

  EXPECT_EQ( text, candidate.Text() );
}

TEST( CandidateTest, MatchesQueryBitsetWhenMatch ) {
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

TEST( CandidateTest, DoesntMatchQueryBitset ) {
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

TEST( CandidateTest, QueryMatchResultCaseInsensitiveIsSubsequence ) {
  Candidate candidate( "foobaaar" );

  EXPECT_TRUE( candidate.QueryMatchResult( "foobaaar", false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "foOBAaar", false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "FOOBAAAR", false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "fobar"   , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "fbr"     , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "f"       , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "F"       , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "o"       , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "O"       , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "a"       , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "r"       , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "b"       , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "bar"     , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "oa"      , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "obr"     , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "oar"     , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "oo"      , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "aaa"     , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "AAA"     , false ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( ""        , false ).IsSubsequence() );
}

TEST( CandidateTest, QueryMatchResultCaseInsensitiveIsntSubsequence ) {
  Candidate candidate( "foobaaar" );

  EXPECT_FALSE( candidate.QueryMatchResult( "foobra"   , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "frb"      , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "brf"      , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "x"        , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "9"        , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "-"        , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "~"        , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( " "        , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "rabof"    , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "oabfr"    , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "ooo"      , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "baaara"   , false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "ffoobaaar", false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "xfoobaaar", false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( " foobaaar", false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "foobaaar ", false ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "ff"       , false ).IsSubsequence() );
}

TEST( CandidateTest, QueryMatchResultCaseSensitiveIsSubsequence ) {
  Candidate candidate( "FooBaAAr" );

  EXPECT_TRUE( candidate.QueryMatchResult( "FooBaAAr", true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "FBAA"    , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "F"       , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "AA"      , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "A"       , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "B"       , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "foobaaar", true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "foobaAAr", true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "fbAA"    , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "fbaa"    , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "b"       , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "f"       , true ).IsSubsequence() );
  EXPECT_TRUE( candidate.QueryMatchResult( "fbar"    , true ).IsSubsequence() );
}

TEST( CandidateTest, QueryMatchResultCaseSensitiveIsntSubsequence ) {
  Candidate candidate( "FooBaAAr" );

  EXPECT_FALSE( candidate.QueryMatchResult( "goo"     , true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "R"       , true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "O"       , true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "OO"      , true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "OBA"     , true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "FBAR"    , true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "FBAAR"   , true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "Oar"     , true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "FooBAAAr", true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "FOoBaAAr", true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "FOobaaar", true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "fOobaaar", true ).IsSubsequence() );
  EXPECT_FALSE( candidate.QueryMatchResult( "foobaaaR", true ).IsSubsequence() );
}

} // namespace YouCompleteMe
