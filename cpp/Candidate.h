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

#ifndef CANDIDATE_H_R5LZH6AC
#define CANDIDATE_H_R5LZH6AC

// TODO can be moved to cpp?
#include "LetterNode.h"
#include "Result.h"

#include <boost/scoped_ptr.hpp>
#include <boost/utility.hpp>

#include <string>
#include <bitset>

namespace YouCompleteMe
{

typedef std::bitset< NUM_LETTERS > Bitset;

Bitset LetterBitsetFromString( const std::string &text );

class Candidate : boost::noncopyable
{
public:

  explicit Candidate( const std::string &text );

  inline const std::string& Text() const
  {
    return text_;
  }

  // Returns true if the candidate contains the bits from the query (it may also
  // contain other bits)
  inline bool MatchesQueryBitset( const Bitset &query_bitset ) const
  {
    return ( letters_present_ & query_bitset ) == query_bitset;
  }

  Result QueryMatchResult( const std::string &query ) const;

private:

  std::string text_;
  std::string word_boundary_chars_;
  Bitset letters_present_;
  boost::scoped_ptr< LetterNode > root_node_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: CANDIDATE_H_R5LZH6AC */

