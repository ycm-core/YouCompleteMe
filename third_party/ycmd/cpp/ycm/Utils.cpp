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

#include "Utils.h"
#include <cmath>
#include <limits>
#include <boost/filesystem.hpp>
#include <boost/filesystem/fstream.hpp>

namespace fs = boost::filesystem;

namespace YouCompleteMe {

bool AlmostEqual( double a, double b ) {
  return std::abs( a - b ) <=
         ( std::numeric_limits< double >::epsilon() *
           std::max( std::abs( a ), std::abs( b ) ) );
}


std::string ReadUtf8File( const fs::path &filepath ) {
  fs::ifstream file( filepath, std::ios::in | std::ios::binary );
  std::vector< char > contents( ( std::istreambuf_iterator< char >( file ) ),
                                std::istreambuf_iterator< char >() );

  if ( contents.size() == 0 )
    return std::string();

  return std::string( contents.begin(), contents.end() );
}


void WriteUtf8File( const fs::path &filepath, const std::string &contents ) {
  fs::ofstream file;
  file.open( filepath );
  file << contents;
  file.close();
}

} // namespace YouCompleteMe
