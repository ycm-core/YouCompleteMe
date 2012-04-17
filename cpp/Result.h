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

#ifndef RESULT_H_CZYD2SGN
#define RESULT_H_CZYD2SGN

#include <string>

namespace YouCompleteMe
{

class Result
{
public:
  explicit Result( bool is_subsequence );

  Result( bool is_subsequence,
          const std::string *text,
          bool text_is_lowercase,
          const std::string &word_boundary_chars,
          const std::string &query );

  Result( const Result& other );

  bool operator< ( const Result &other ) const;

  inline bool IsSubsequence() const
  {
    return is_subsequence_;
  }

  inline const std::string* Text() const
  {
    return text_;
  }

private:
  void SetResultFeaturesFromQuery(
      const std::string &query,
      const std::string &word_boundary_chars );


  bool is_subsequence_;
  bool first_char_same_in_query_and_text_;

  // number of word boundary matches / number of chars in query
  double ratio_of_word_boundary_chars_in_query_;

  // number of word boundary matches / number of all word boundary chars
  double word_boundary_char_utilization_;
  bool query_is_candidate_prefix_;
  bool text_is_lowercase_;
  const std::string *text_;

};

} // namespace YouCompleteMe

#endif /* end of include guard: RESULT_H_CZYD2SGN */

