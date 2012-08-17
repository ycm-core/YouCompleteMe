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
#include "Future.h"

#ifndef NO_CLANG_COMPLETER
#  include "ClangCompleter.h"
#  include "CompletionData.h"
#  include "Diagnostic.h"
#  include "UnsavedFile.h"
#endif // NO_CLANG_COMPLETER

#include <boost/python.hpp>
#include <boost/utility.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

BOOST_PYTHON_MODULE(ycm_core)
{
  using namespace boost::python;
  using namespace YouCompleteMe;

  class_< IdentifierCompleter, boost::noncopyable >( "IdentifierCompleter" )
    .def( "EnableThreading", &IdentifierCompleter::EnableThreading )
    .def( "AddCandidatesToDatabase",
          &IdentifierCompleter::AddCandidatesToDatabase )
    .def( "AddCandidatesToDatabaseFromBufferAsync",
          &IdentifierCompleter::AddCandidatesToDatabaseFromBufferAsync )
    .def( "CandidatesForQueryAndTypeAsync",
          &IdentifierCompleter::CandidatesForQueryAndTypeAsync );

  // TODO: rename these *Vec classes to *Vector; don't forget the python file
  class_< std::vector< std::string >,
      boost::shared_ptr< std::vector< std::string > > >( "StringVec" )
    .def( vector_indexing_suite< std::vector< std::string > >() );

  class_< Future< AsyncResults > >( "FutureResults" )
    .def( "ResultsReady", &Future< AsyncResults >::ResultsReady )
    .def( "GetResults", &Future< AsyncResults >::GetResults );

  class_< Future< void > >( "FutureVoid" )
    .def( "ResultsReady", &Future< void >::ResultsReady )
    .def( "GetResults", &Future< void >::GetResults );

#ifndef NO_CLANG_COMPLETER
  class_< Future< AsyncCompletions > >( "FutureCompletions" )
    .def( "ResultsReady", &Future< AsyncCompletions >::ResultsReady )
    .def( "GetResults", &Future< AsyncCompletions >::GetResults );

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
    .def( "EnableThreading", &ClangCompleter::EnableThreading )
    .def( "DiagnosticsForFile", &ClangCompleter::DiagnosticsForFile )
    .def( "UpdatingTranslationUnit", &ClangCompleter::UpdatingTranslationUnit )
    .def( "UpdateTranslationUnitAsync",
          &ClangCompleter::UpdateTranslationUnitAsync )
    .def( "CandidatesForQueryAndLocationInFileAsync",
          &ClangCompleter::CandidatesForQueryAndLocationInFileAsync );

  class_< CompletionData >( "CompletionData" )
    .def( "TextToInsertInBuffer", &CompletionData::TextToInsertInBuffer )
    .def( "MainCompletionText", &CompletionData::MainCompletionText )
    .def( "ExtraMenuInfo", &CompletionData::ExtraMenuInfo )
    .def( "DetailedInfoForPreviewWindow",
          &CompletionData::DetailedInfoForPreviewWindow )
    .def_readonly( "kind_", &CompletionData::kind_ );

  class_< std::vector< CompletionData >,
      boost::shared_ptr< std::vector< CompletionData > > >(
          "CompletionVec" )
    .def( vector_indexing_suite< std::vector< CompletionData > >() );

  class_< Diagnostic >( "Diagnostic" )
    .def_readonly( "line_number_", &Diagnostic::line_number_ )
    .def_readonly( "column_number_", &Diagnostic::column_number_ )
    .def_readonly( "kind_", &Diagnostic::kind_ )
    .def_readonly( "filename_", &Diagnostic::filename_ )
    .def_readonly( "text_", &Diagnostic::text_ )
    .def_readonly( "long_formatted_text_", &Diagnostic::long_formatted_text_ );

  class_< std::vector< Diagnostic > >( "DiagnosticVec" )
    .def( vector_indexing_suite< std::vector< Diagnostic > >() );

#endif // NO_CLANG_COMPLETER
}
