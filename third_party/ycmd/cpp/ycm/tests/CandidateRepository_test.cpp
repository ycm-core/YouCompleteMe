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
#include "CandidateRepository.h"
#include "Candidate.h"
#include "Result.h"

namespace YouCompleteMe {

TEST( CandidateRepositoryTest, EmptyCandidatesForUnicode ) {
  std::vector< std::string > inputs;
  inputs.push_back( "fooδιακριτικός" );
  inputs.push_back( "fooδιακός" );

  CandidateRepository &repo = CandidateRepository::Instance();
  std::vector< const Candidate * > candidates =
    repo.GetCandidatesForStrings( inputs );

  EXPECT_EQ( "", candidates[ 0 ]->Text() );
  EXPECT_EQ( "", candidates[ 1 ]->Text() );
}


TEST( CandidateRepositoryTest, EmptyCandidatesForNonPrintable ) {
  std::vector< std::string > inputs;
  inputs.push_back( "\x01\x05\x0a\x15" );

  CandidateRepository &repo = CandidateRepository::Instance();
  std::vector< const Candidate * > candidates =
    repo.GetCandidatesForStrings( inputs );

  EXPECT_EQ( "", candidates[ 0 ]->Text() );
}


} // namespace YouCompleteMe

