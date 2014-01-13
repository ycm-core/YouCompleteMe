// Copyright (C) 2011, 2012, 2013  Google Inc.
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

#ifndef PYTHONSUPPORT_H_KWGFEX0V
#define PYTHONSUPPORT_H_KWGFEX0V

#include <boost/python.hpp>

namespace YouCompleteMe {

// Given a list of python objects (that represent completion candidates) in a
// python list |candidates|, a |candidate_property| on which to filter and sort
// the candidates and a user query, returns a new sorted python list with the
// original objects that survived the filtering.
boost::python::list FilterAndSortCandidates(
  const boost::python::list &candidates,
  const std::string &candidate_property,
  const std::string &query );

} // namespace YouCompleteMe

#endif /* end of include guard: PYTHONSUPPORT_H_KWGFEX0V */

