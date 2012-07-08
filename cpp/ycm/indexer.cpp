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

#include "Completer.h"
#include "Future.h"

#include <boost/python.hpp>
#include <boost/utility.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

BOOST_PYTHON_MODULE(indexer)
{
  using namespace boost::python;
  using namespace YouCompleteMe;

  class_< Future >( "Future" )
    .def( "ResultsReady", &Future::ResultsReady )
    .def( "GetResults", &Future::GetResults );

  class_< Completer, boost::noncopyable >( "Completer" )
    .def( "EnableThreading", &Completer::EnableThreading )
    // .def( "AddCandidatesToDatabase", actd )
    .def( "AddCandidatesToDatabase", &Completer::AddCandidatesToDatabase )
    .def( "CandidatesForQueryAndTypeAsync",
          &Completer::CandidatesForQueryAndTypeAsync );

	class_< std::vector< std::string > >( "StringVec" )
		.def( vector_indexing_suite< std::vector< std::string > >() );
}
