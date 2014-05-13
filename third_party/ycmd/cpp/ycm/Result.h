// Copyright (C) 2011, 2012  Google Inc.
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

namespace YouCompleteMe {

class Result {
public:
  Result();
  explicit Result( bool is_subsequence );

  Result( bool is_subsequence,
          const std::string *text,
          bool text_is_lowercase,
          int char_match_index_sum,
          const std::string &word_boundary_chars,
          const std::string &query );

  bool operator< ( const Result &other ) const;

  inline bool IsSubsequence() const {
    return is_subsequence_;
  }

  inline const std::string *Text() const {
    return text_;
  }

private:
  void SetResultFeaturesFromQuery(
    const std::string &query,
    const std::string &word_boundary_chars );

  // true when the query for which the result was created was an empty string;
  // in these cases we just use a lexicographic comparison
  bool query_is_empty_;

  // true when the characters of the query are a subsequence of the characters
  // in the candidate text, e.g. the characters "abc" are a subsequence for
  // "xxaygbefc" but not for "axxcb" since they occur in the correct order ('a'
  // then 'b' then 'c') in the first string but not in the second.
  bool is_subsequence_;

  // true when the first character of the query and the candidate match
  bool first_char_same_in_query_and_text_;

  // number of word boundary matches / number of chars in query
  double ratio_of_word_boundary_chars_in_query_;

  // number of word boundary matches / number of all word boundary chars
  double word_boundary_char_utilization_;

  // true when the query is a prefix of the candidate string, e.g. "foo" query
  // for "foobar" candidate.
  bool query_is_candidate_prefix_;

  // true when the candidate text is all lowercase, e.g. "foo" candidate.
  bool text_is_lowercase_;

  // The sum of the indexes of all the letters the query "hit" in the candidate
  // text. For instance, the result for the query "abc" in the candidate
  // "012a45bc8" has char_match_index_sum of 3 + 6 + 7 = 16 because those are
  // the char indexes of those letters in the candidate string.
  int char_match_index_sum_;

  // points to the full candidate text
  const std::string *text_;

};

template< class T >
struct ResultAnd {
  // TODO: Swap the order of these parameters
  ResultAnd( T extra_object, const Result &result )
    : extra_object_( extra_object ), result_( result ) {}

  bool operator< ( const ResultAnd &other ) const {
    return result_ < other.result_;
  }

  T extra_object_;
  Result result_;
};

template< class T >
struct ResultAnd<T * > {
  ResultAnd( const T *extra_object, const Result &result )
    : extra_object_( extra_object ), result_( result ) {}

  bool operator< ( const ResultAnd &other ) const {
    return result_ < other.result_;
  }

  const T *extra_object_;
  Result result_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: RESULT_H_CZYD2SGN */

