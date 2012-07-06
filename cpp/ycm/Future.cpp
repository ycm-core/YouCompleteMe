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

#include "Future.h"
#include "standard.h"
#include "Result.h"

namespace YouCompleteMe
{

Future::Future( boost::shared_future< AsyncResults > future )
  : future_( boost::move( future ) )
{
}

bool Future::ResultsReady()
{
  return future_.is_ready();
}

void Future::GetResults( Pylist &candidates )
{
  AsyncResults results;

  try
  {
    results = future_.get();
  }

  catch ( boost::future_uninitialized & )
  {
    return;
  }

  foreach ( const Result& result, *results )
  {
    candidates.append( *result.Text() );
  }
}

} // namespace YouCompleteMe
