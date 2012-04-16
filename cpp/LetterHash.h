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

#ifndef LETTERHASH_H_BRK2UMC1
#define LETTERHASH_H_BRK2UMC1

#include <vector>
#include <list>
#include <boost/utility.hpp>

#define NUM_LETTERS 128

namespace YouCompleteMe
{

class LetterNode;

extern const int kNumLetters;

int IndexForChar( char letter );
bool IsUppercase( char letter );

class LetterHash : boost::noncopyable
{
public:
  LetterHash();
  ~LetterHash();

  // const std::list< LetterNode* > operator[] ( char letter ) const;

  bool HasLetter( char letter );

  std::list< LetterNode* >& operator[] ( char letter );

  std::list< LetterNode* >* ListPointerAt( char letter );

  bool HasLetter( char letter ) const;

private:

  std::vector< std::list< LetterNode* >* > letters_;
  // TODO: remove this list, we can just create lists on the heap when we need
  // them
  // std::vector< std::list< LetterNode* > > letter_node_lists_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: LETTERHASH_H_BRK2UMC1 */

