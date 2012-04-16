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
#include "LetterNode.h"


namespace YouCompleteMe
{

LetterNode::LetterNode( char letter )
{
  is_uppercase = IsUppercase( letter );
  is_root_node = false;
}

LetterNode::LetterNode( const std::string &text )
{
  is_uppercase = false;
  is_root_node = true;

  letternode_per_text_index_.resize( text.size() );

  for (int i = 0; i < text.size(); ++i)
  {
    char letter = text[ i ];
    LetterNode *node = new LetterNode( letter );
    letters_[ letter ].push_back( node );
    letternode_per_text_index_[ i ] = boost::shared_ptr< LetterNode >( node );
  }

  for ( int i = letternode_per_text_index_.size() - 1; i >= 0; --i )
  {
    LetterNode *node_to_add = letternode_per_text_index_[ i ].get();

    for ( int j = i - 1; j >= 0; --j )
    {
      letternode_per_text_index_[ j ]->PrependNodeForLetter( text[ i ],
                                                             node_to_add );
    }
  }
}

} // namespace YouCompleteMe
