// Copyright (C) 2013  Google Inc.
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

#include "IdentifierCompleter.h"
#include "PythonSupport.h"
#include "versioning.h"

#include <boost/python.hpp>
#include <boost/utility.hpp>


BOOST_PYTHON_MODULE(ycm_client_support)
{
  using namespace boost::python;
  using namespace YouCompleteMe;

  // Necessary because of usage of the ReleaseGil class
  PyEval_InitThreads();

  def( "FilterAndSortCandidates", FilterAndSortCandidates );
  def( "YcmCoreVersion", YcmCoreVersion );
}

// Boost.Thread forces us to implement this.
// We don't use any thread-specific (local) storage so it's fine to implement
// this as an empty function.
namespace boost {
void tss_cleanup_implemented() {}
};

