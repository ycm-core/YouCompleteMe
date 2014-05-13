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

#ifndef UTILS_H_KEPMRPBH
#define UTILS_H_KEPMRPBH

#include <string>
#include <vector>
#include <boost/filesystem.hpp>
namespace fs = boost::filesystem;

namespace YouCompleteMe {

bool AlmostEqual( double a, double b );

// Reads the entire contents of the specified file. If the file does not exist,
// an exception is thrown.
std::string ReadUtf8File( const fs::path &filepath );

// Writes the entire contents of the specified file. If the file does not exist,
// an exception is thrown.
void WriteUtf8File( const fs::path &filepath, const std::string &contents );

template <class Container, class Key>
typename Container::mapped_type &
GetValueElseInsert( Container &container,
                    const Key &key,
                    const typename Container::mapped_type &value ) {
  return container.insert( typename Container::value_type( key, value ) )
         .first->second;
}


template <class Container, class Key>
bool ContainsKey( Container &container, const Key &key ) {
  return container.find( key ) != container.end();
}


template <class Container, class Key>
typename Container::mapped_type
FindWithDefault( Container &container,
                 const Key &key,
                 const typename Container::mapped_type &value ) {
  typename Container::const_iterator it = container.find( key );
  return it != container.end() ? it->second : value;
}


template <class Container, class Key>
bool Erase( Container &container, const Key &key ) {
  typename Container::iterator it = container.find( key );

  if ( it != container.end() ) {
    container.erase( it );
    return true;
  }

  return false;
}

} // namespace YouCompleteMe

#endif /* end of include guard: UTILS_H_KEPMRPBH */
