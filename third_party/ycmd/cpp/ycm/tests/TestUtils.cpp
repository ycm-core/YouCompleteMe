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

#include "TestUtils.h"

namespace YouCompleteMe {

namespace fs = boost::filesystem;

std::vector< std::string > StringVector( const std::string &a,
                                         const std::string &b,
                                         const std::string &c,
                                         const std::string &d,
                                         const std::string &e,
                                         const std::string &f,
                                         const std::string &g,
                                         const std::string &h,
                                         const std::string &i ) {
  std::vector< std::string > string_vector;
  string_vector.push_back( a );

  if ( !b.empty() )
    string_vector.push_back( b );

  if ( !c.empty() )
    string_vector.push_back( c );

  if ( !d.empty() )
    string_vector.push_back( d );

  if ( !e.empty() )
    string_vector.push_back( e );

  if ( !f.empty() )
    string_vector.push_back( f );

  if ( !g.empty() )
    string_vector.push_back( g );

  if ( !h.empty() )
    string_vector.push_back( h );

  if ( !i.empty() )
    string_vector.push_back( i );

  return string_vector;
}

boost::filesystem::path PathToTestFile( const std::string &filepath ) {
  fs::path path_to_testdata = fs::current_path() / fs::path( "testdata" );
  return path_to_testdata / fs::path( filepath );
}

} // namespace YouCompleteMe

