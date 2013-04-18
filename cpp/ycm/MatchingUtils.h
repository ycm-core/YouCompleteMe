// Copyright (C) 2011, 2012, 2013  Strahinja Val Markovic  <val@markovic.io>
//                                 Stanislav Golovanov <stgolovanov@gmail.com>
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
#include <string>

namespace YouCompleteMe {

typedef struct
{
  std::string str;           // Python object with file path
  double score;              // score of string
} Match;

typedef struct
{
  std::string str;           // string to be searched
  long str_len;              // length of same
  std::string query;         // query string
  long query_len;            // length of same
  double max_score_per_char;
  int is_dot_file;           // boolean: true if str is a dot-file
} MatchObject;

double CalculateMatchScore(
  MatchObject *m,            // sharable meta-data
  long str_index,            // where in the path string to start
  long query_index,          // where in the search string to start
  long last_matched_index,   // location of last matched character
  double score);             // cumulative score so far

bool CompareMatchScore(Match a_val, Match b_val);

} // namespace YouCompleteMe
