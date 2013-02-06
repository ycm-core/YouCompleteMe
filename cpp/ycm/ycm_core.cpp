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

#ifdef USE_CLANG_COMPLETER
#  include "ClangCompleter.h"
#  include "ClangUtils.h"
#  include "CompletionData.h"
#  include "Diagnostic.h"
#  include "UnsavedFile.h"
#  include "CompilationDatabase.h"
#endif // USE_CLANG_COMPLETER

#include <boost/python.hpp>
#include <boost/utility.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

bool HasClangSupport()
{
#ifdef USE_CLANG_COMPLETER
  return true;
#else
  return false;
#endif // USE_CLANG_COMPLETER
}


BOOST_PYTHON_MODULE(ycm_core)
{
  using namespace boost::python;
  using namespace YouCompleteMe;

  def( "HasClangSupport", HasClangSupport );

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

#ifdef USE_CLANG_COMPLETER
  def( "ClangVersion", ClangVersion );

  class_< Future< AsyncCompletions > >( "FutureCompletions" )
    .def( "ResultsReady", &Future< AsyncCompletions >::ResultsReady )
    .def( "GetResults", &Future< AsyncCompletions >::GetResults );

  class_< Future< AsyncCompilationInfoForFile > >(
      "FutureCompilationInfoForFile" )
    .def( "ResultsReady",
          &Future< AsyncCompilationInfoForFile >::ResultsReady )
    .def( "GetResults",
          &Future< AsyncCompilationInfoForFile >::GetResults );

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

  class_< CompilationDatabase, boost::noncopyable >(
      "CompilationDatabase", init< std::string >() )
    .def( "EnableThreading", &CompilationDatabase::EnableThreading )
    .def( "DatabaseSuccessfullyLoaded",
          &CompilationDatabase::DatabaseSuccessfullyLoaded )
    .def( "GetCompilationInfoForFile",
          &CompilationDatabase::GetCompilationInfoForFile )
    .def( "GetCompilationInfoForFileAsync",
          &CompilationDatabase::GetCompilationInfoForFileAsync );

  class_< CompilationInfoForFile,
      boost::shared_ptr< CompilationInfoForFile > >(
          "CompilationInfoForFile", no_init )
    .def_readonly( "compiler_working_dir_",
                   &CompilationInfoForFile::compiler_working_dir_ )
    .def_readonly( "compiler_flags_",
                   &CompilationInfoForFile::compiler_flags_ );

#endif // USE_CLANG_COMPLETER
}

// Boost.Thread forces us to implement this.
// We don't use any thread-specific (local) storage so it's fine to implement
// this as an empty function.
namespace boost {
void tss_cleanup_implemented() {}
};
