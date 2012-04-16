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

#include "standard.h"
#include "Candidate.h"
#include <cctype>

namespace YouCompleteMe
{

namespace
{

std::string GetWordBoundaryChars( const std::string &text )
{
  std::string result;

  for ( int i = 0; i < text.size(); ++i )
  {
    if ( i == 0 ||
         IsUppercase( text[ i ] ) ||
         ( i > 0 && text[ i - 1 ] == '_' && isalpha( text[ i ] ) )
       )
    {
      result.push_back( tolower( text[ i ] ) );
    }
  }

  return result;
}

} // unnamed namespace


Bitset LetterBitsetFromString( const std::string &text )
{
  Bitset letter_bitset;
  foreach ( char letter, text )
  {
    letter_bitset.set( IndexForChar( letter ) );
  }

  return letter_bitset;
}

Candidate::Candidate( const std::string &text )
  :
  text_( text ),
  word_boundary_chars_( GetWordBoundaryChars( text ) ),
  letters_present_( LetterBitsetFromString( text ) ),
  root_node_( new LetterNode( text ) )
{
}

Result Candidate::QueryMatchResult( const std::string &query ) const
{
  LetterNode *node = root_node_.get();

  foreach ( char letter, query )
  {
    const std::list< LetterNode *> *list = node->NodeListForLetter( letter );
    if ( !list )

      return Result( false );

    node = list->front();
  }

  return Result( true, &text_, word_boundary_chars_, query );
}

} // namespace YouCompleteMe
