// Copyright (C) 2011  Strahinja Markovic  <strahinja.markovic@gmail.com>
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

namespace YouCompleteMe
{

bool AlmostEqual( double a, double b )
{
  return std::abs( a - b ) <=
    ( std::numeric_limits< double >::epsilon() *
      std::max( std::abs( a ), std::abs( b ) ) );
}

} // namespace YouCompleteMe
