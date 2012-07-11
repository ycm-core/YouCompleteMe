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

#ifndef CLANGCOMPLETE_H_WLKDU0ZV
#define CLANGCOMPLETE_H_WLKDU0ZV

#include <boost/utility.hpp>
#include <boost/unordered_map.hpp>

#include <string>

typedef void *CXIndex;
typedef struct CXTranslationUnitImpl *CXTranslationUnit;

namespace YouCompleteMe
{

struct UnsavedFile
{
  UnsavedFile() : filename_( NULL ), contents_( NULL ), length_( 0 ) {}

  const char *filename_;
  const char *contents_;
  unsigned long length_;

  // We need this to be able to export this struct to Python via Boost.Python's
  // methods. I have no clue why, but it won't compile without it.
  // TODO: report this problem on the Boost bug tracker, the default equality
  // operator should be more than adequate here
  bool operator==( const UnsavedFile &other) const
  {
    return filename_ == other.filename_ && contents_ == other.contents_;
  }
};


typedef boost::unordered_map< std::string, std::vector< std::string > >
  FlagsForFile;
typedef boost::unordered_map< std::string, CXTranslationUnit >
  TranslationUnitForFilename;


class ClangComplete : boost::noncopyable
{
public:
  ClangComplete();
  ~ClangComplete();

  void SetGlobalCompileFlags( const std::vector< std::string > &flags );

  void SetFileCompileFlags( const std::string &filename,
                            const std::vector< std::string > &flags );

  void UpdateTranslationUnit( const std::string &filename,
                              const std::vector< UnsavedFile > &unsaved_files );

  std::vector< std::string > CandidatesForLocationInFile(
      const std::string &filename,
      int line,
      int column,
      const std::vector< UnsavedFile > &unsaved_files );

private:

  // caller takes ownership of translation unit
  CXTranslationUnit CreateTranslationUnit(
      const std::string &filename,
      const std::vector< UnsavedFile > &unsaved_files );

  std::vector< const char* > ClangFlagsForFilename(
      const std::string &filename );

  CXTranslationUnit GetTranslationUnitForFile(
      const std::string &filename,
      const std::vector< UnsavedFile > &unsaved_files );

  CXIndex clang_index_;
  FlagsForFile flags_for_file_;
  TranslationUnitForFilename filename_to_translation_unit_;
  std::vector< std::string > global_flags_;

};

} // namespace YouCompleteMe

#endif /* end of include guard: CLANGCOMPLETE_H_WLKDU0ZV */
