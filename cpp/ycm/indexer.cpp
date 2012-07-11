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

#include "IdentifierCompleter.h"
#include "ClangCompleter.h"
#include "Future.h"

#include <boost/python.hpp>
#include <boost/utility.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

BOOST_PYTHON_MODULE(indexer)
{
  using namespace boost::python;
  using namespace YouCompleteMe;

	class_< std::vector< std::string > >( "StringVec" )
		.def( vector_indexing_suite< std::vector< std::string > >() );

  class_< Future >( "Future" )
    .def( "ResultsReady", &Future::ResultsReady )
    .def( "GetResults", &Future::GetResults );

  class_< IdentifierCompleter, boost::noncopyable >( "IdentifierCompleter" )
    .def( "EnableThreading", &IdentifierCompleter::EnableThreading )
    .def( "AddCandidatesToDatabase",
          &IdentifierCompleter::AddCandidatesToDatabase )
    .def( "CandidatesForQueryAndTypeAsync",
          &IdentifierCompleter::CandidatesForQueryAndTypeAsync );

  // CAREFUL HERE! For filename and contents we are referring directly to
  // Python-allocated and -managed memory since we are accepting pointers to
  // data members of python objects. We need to ensure that those objects
  // outlive our UnsavedFile objects.
	class_< UnsavedFile >( "UnsavedFile" )
    .add_property( "filename_",
      make_getter( &UnsavedFile::filename_ ),
      make_setter( &UnsavedFile::filename_,
                   return_value_policy< reference_existing_object >() ) )
    .add_property( "contents_",
      make_getter( &UnsavedFile::contents_ ),
      make_setter( &UnsavedFile::contents_,
                   return_value_policy< reference_existing_object >() ) )
    .def_readwrite( "length_", &UnsavedFile::length_ );

	class_< std::vector< UnsavedFile > >( "UnsavedFileVec" )
		.def( vector_indexing_suite< std::vector< UnsavedFile > >() );

  class_< ClangCompleter, boost::noncopyable >( "ClangCompleter" )
    .def( "SetGlobalCompileFlags", &ClangCompleter::SetGlobalCompileFlags )
    .def( "SetFileCompileFlags", &ClangCompleter::SetFileCompileFlags )
    .def( "UpdateTranslationUnit", &ClangCompleter::UpdateTranslationUnit )
    .def( "CandidatesForLocationInFile",
          &ClangCompleter::CandidatesForLocationInFile );
}
