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

#ifndef UTILS_H_KEPMRPBH
#define UTILS_H_KEPMRPBH


#include <string>
#include <vector>

namespace YouCompleteMe
{

bool AlmostEqual( double a, double b );


template <class Container, class Key>
typename Container::mapped_type &
GetValueElseInsert( Container &container,
                    Key const& key,
                    typename Container::mapped_type const& value )
{
  return container.insert( typename Container::value_type( key, value ) )
    .first->second;
}


template <class Container, class Key>
bool ContainsKey( Container &container, Key const& key)
{
  return container.find( key ) != container.end();
}

} // namespace YouCompleteMe

#endif /* end of include guard: UTILS_H_KEPMRPBH */

