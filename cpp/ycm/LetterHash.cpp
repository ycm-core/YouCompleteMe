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

#include "LetterHash.h"
#include "standard.h"

namespace YouCompleteMe
{

const int kNumLetters = NUM_LETTERS;
static const int kLettersIndexStart = 0;
static const int kNumbersIndexStart = 26;


bool IsUppercase( char letter )
{
  return 'A' <= letter && letter <= 'Z';
}


int IndexForChar( char letter )
{
  if ( IsUppercase( letter ) )
    return letter + ( 'a' - 'A' );

  return letter;
}


LetterHash::LetterHash()
{
  letters_.resize( kNumLetters );

  for ( uint i = 0; i < letters_.size(); ++i )
  {
    letters_[ i ] = NULL;
  }
}


LetterHash::~LetterHash()
{
  for ( uint i = 0; i < letters_.size(); ++i )
  {
    delete letters_[ i ];
  }
}


bool LetterHash::HasLetter( char letter )
{
  int letter_index = IndexForChar( letter );
  std::list< LetterNode* > *list = letters_[ letter_index ];
  return list;
}


std::list< LetterNode* >& LetterHash::operator[] ( char letter )
{
  int letter_index = IndexForChar( letter );
  std::list< LetterNode* > *list = letters_[ letter_index ];
  if ( list )

    return *list;

  letters_[ letter_index ] = new std::list< LetterNode* >();
  return *letters_[ letter_index ];
}


std::list< LetterNode* >* LetterHash::ListPointerAt( char letter )
{
  return letters_[ IndexForChar( letter ) ];
}


bool LetterHash::HasLetter( char letter ) const
{
  return letters_[ IndexForChar( letter ) ] != NULL;
}

} // namespace YouCompleteMe
