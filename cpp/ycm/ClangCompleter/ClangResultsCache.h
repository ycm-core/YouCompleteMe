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

#ifndef CLANGRESULTSCACHE_H_REUWM3RU
#define CLANGRESULTSCACHE_H_REUWM3RU

#include "CompletionData.h"

#include <vector>
#include <boost/thread/locks.hpp>
#include <boost/thread/shared_mutex.hpp>
#include <boost/function.hpp>
#include <boost/config.hpp>
#include <boost/utility.hpp>

namespace YouCompleteMe {

struct CompletionData;

class ClangResultsCache : boost::noncopyable {
public:

  ClangResultsCache() : line_( -1 ), column_( -1 ) {}

  bool NewPositionDifferentFromStoredPosition( int new_line, int new_colum )
  const;

  void ResetWithNewLineAndColumn( int new_line, int new_colum );

  void SetCompletionDatas(
    const std::vector< CompletionData > new_completions ) {
    completion_datas_ = new_completions;
  }

#ifndef BOOST_NO_RVALUE_REFERENCES
#  ifdef __clang__
#    pragma clang diagnostic push
#    pragma clang diagnostic ignored "-Wc++98-compat"
#  endif   //#ifdef __clang__

  void SetCompletionDatas( std::vector< CompletionData > && new_completions ) {
    completion_datas_ = new_completions;
  }

#  ifdef __clang__
#    pragma clang diagnostic pop
#  endif   //#ifdef __clang__
#endif   //#ifndef BOOST_NO_RVALUE_REFERENCES

  template< typename T >
  T OperateOnCompletionDatas(
    boost::function< T( const std::vector< CompletionData >& ) > operation )
  const {
    boost::shared_lock< boost::shared_mutex > reader_lock( access_mutex_ );
    return operation( completion_datas_ );
  }

private:

  int line_;
  int column_;
  std::vector< CompletionData > completion_datas_;

  mutable boost::shared_mutex access_mutex_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: CLANGRESULTSCACHE_H_REUWM3RU */

