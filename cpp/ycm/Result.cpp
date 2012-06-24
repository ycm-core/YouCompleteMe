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

#include "Result.h"
#include "standard.h"
#include "Utils.h"
#include <boost/algorithm/string.hpp>

using boost::algorithm::istarts_with;

namespace YouCompleteMe
{

namespace
{

int NumWordBoundaryCharMatches( const std::string &query,
                                const std::string &word_boundary_chars )
{
  uint i = 0;
  uint j = 0;
  while ( j < query.size() && i < word_boundary_chars.size() )
  {
    if ( toupper( query[ j ] ) == toupper( word_boundary_chars[ i ] ) )
      ++j;
    ++i;
  }

  return j;
}

} // unnamed namespace


Result::Result( bool is_subsequence )
  :
  is_subsequence_( is_subsequence ),
  first_char_same_in_query_and_text_( false ),
  ratio_of_word_boundary_chars_in_query_( 0 ),
  word_boundary_char_utilization_( 0 ),
  query_is_candidate_prefix_( false ),
  text_is_lowercase_( false ),
  text_( NULL )
{
}

Result::Result( bool is_subsequence,
                const std::string *text,
                bool text_is_lowercase,
                const std::string &word_boundary_chars,
                const std::string &query )
  :
  is_subsequence_( is_subsequence ),
  first_char_same_in_query_and_text_( false ),
  ratio_of_word_boundary_chars_in_query_( 0 ),
  word_boundary_char_utilization_( 0 ),
  query_is_candidate_prefix_( false ),
  text_is_lowercase_( text_is_lowercase ),
  text_( text )
{
  if ( is_subsequence )
    SetResultFeaturesFromQuery( word_boundary_chars, query );
}


Result::Result( const Result& other )
  :
  is_subsequence_( other.is_subsequence_ ),
  first_char_same_in_query_and_text_(
      other.first_char_same_in_query_and_text_ ),
  ratio_of_word_boundary_chars_in_query_(
      other.ratio_of_word_boundary_chars_in_query_ ),
  word_boundary_char_utilization_( other.word_boundary_char_utilization_ ),
  query_is_candidate_prefix_( other.query_is_candidate_prefix_ ),
  text_is_lowercase_( other.text_is_lowercase_ ),
  text_( other.text_ )
{
}


bool Result::operator< ( const Result &other ) const {
  // Yes, this is ugly but it also needs to be fast.  Since this is called a
  // bazillion times, we have to make sure only the required comparisons are
  // made, and no more.

  if ( first_char_same_in_query_and_text_ !=
       other.first_char_same_in_query_and_text_ )
  {
    return first_char_same_in_query_and_text_;
  }

  bool equal_wb_ratios = AlmostEqual(
      ratio_of_word_boundary_chars_in_query_,
      other.ratio_of_word_boundary_chars_in_query_ );

  bool equal_wb_utilization = AlmostEqual(
      word_boundary_char_utilization_,
      other.word_boundary_char_utilization_ );

  if ( AlmostEqual( ratio_of_word_boundary_chars_in_query_, 1.0 ) ||
       AlmostEqual( other.ratio_of_word_boundary_chars_in_query_, 1.0 ) )
  {
    if ( !equal_wb_ratios )
    {
      return ratio_of_word_boundary_chars_in_query_ >
        other.ratio_of_word_boundary_chars_in_query_;
    }

    else
    {
      if ( !equal_wb_utilization )
        return word_boundary_char_utilization_ >
          other.word_boundary_char_utilization_;
    }
  }

  if ( query_is_candidate_prefix_ != other.query_is_candidate_prefix_ )
    return query_is_candidate_prefix_;

  if ( !equal_wb_ratios )
  {
    return ratio_of_word_boundary_chars_in_query_ >
      other.ratio_of_word_boundary_chars_in_query_;
  }

  else
  {
    if ( !equal_wb_utilization )
      return word_boundary_char_utilization_ >
        other.word_boundary_char_utilization_;
  }

  if ( text_->length() != other.text_->length() )
    return text_->length() < other.text_->length();

  if ( text_is_lowercase_ != other.text_is_lowercase_ )
    return text_is_lowercase_;

  return *text_ < *other.text_;
}


void Result::SetResultFeaturesFromQuery(
    const std::string &word_boundary_chars,
    const std::string &query)
{
  if ( query.empty() || text_->empty() )
    return;

  first_char_same_in_query_and_text_ =
    toupper( query[ 0 ] ) == toupper( (*text_)[ 0 ] );
  int num_wb_matches = NumWordBoundaryCharMatches( query,
                                                   word_boundary_chars );
  ratio_of_word_boundary_chars_in_query_ =
    num_wb_matches / static_cast< double >( query.length() );
  word_boundary_char_utilization_ =
    num_wb_matches / static_cast< double >( word_boundary_chars.length() );
  query_is_candidate_prefix_ = istarts_with( *text_, query );

}

} // namespace YouCompleteMe
