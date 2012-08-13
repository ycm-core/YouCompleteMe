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

#include "ClangResultsCache.h"
#include "standard.h"

using boost::shared_mutex;
using boost::shared_lock;
using boost::unique_lock;

namespace YouCompleteMe
{

bool ClangResultsCache::NewPositionDifferentFromStoredPosition( int new_line,
                                                                int new_colum )
  const
{
  shared_lock< shared_mutex > reader_lock( access_mutex_ );
  return line_ != new_line || column_ != new_colum;
}

void ClangResultsCache::ResetWithNewLineAndColumn( int new_line, int new_colum )
{
  unique_lock< shared_mutex > reader_lock( access_mutex_ );

  line_ = new_line;
  column_ = new_colum;
  completion_datas_.clear();
}

} // namespace YouCompleteMe
