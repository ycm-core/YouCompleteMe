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

#ifndef LETTERNODE_H_EIZ6JVWC
#define LETTERNODE_H_EIZ6JVWC

#include "LetterHash.h"

#include <boost/utility.hpp>
#include <boost/shared_ptr.hpp>

#include <vector>
#include <list>
#include <string>


namespace YouCompleteMe
{

class LetterNode : boost::noncopyable
{
public:
	explicit LetterNode( char letter );

  // this is for root nodes
	explicit LetterNode( const std::string &text );

  inline bool LetterIsUppercase() const
  {
    return is_uppercase;
  }


	inline const std::list< LetterNode* >* NodeListForLetter( char letter )
  {
    return letters_.ListPointerAt( letter );
  }


	inline void PrependNodeForLetter( char letter, LetterNode* node )
  {
    letters_[ letter ].push_front( node );
  }

private:

  // TODO: rename LetterHash to LetterNodeListHash or LetterNodeListDict/Map?
  LetterHash letters_;
  std::vector< boost::shared_ptr< LetterNode > > letternode_per_text_index_;
	bool is_uppercase;
	bool is_root_node;
};

} // namespace YouCompleteMe

#endif /* end of include guard: LETTERNODE_H_EIZ6JVWC */

