// Copyright (C) 2011, 2012, 2013  Strahinja Val Markovic  <val@markovic.io>
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

#include "PythonSupport.h"
#include "standard.h"
#include "Result.h"
#include "Candidate.h"
#include "CandidateRepository.h"
#include "MatchingUtils.h"
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/cxx11/any_of.hpp>
#include <vector>

using boost::algorithm::any_of;
using boost::algorithm::is_upper;
using boost::python::len;
using boost::python::extract;
using boost::python::object;
typedef boost::python::list pylist;

namespace YouCompleteMe {

namespace {

std::vector< const Candidate * > CandidatesFromObjectList(
  const pylist &candidates,
  const std::string &candidate_property ) {
  int num_candidates = len( candidates );
  std::vector< std::string > candidate_strings;
  candidate_strings.reserve( num_candidates );

  for ( int i = 0; i < num_candidates; ++i ) {
    if ( candidate_property.empty() ) {
      candidate_strings.push_back( extract< std::string >( candidates[ i ] ) );
    } else {
      object holder = extract< object >( candidates[ i ] );
      candidate_strings.push_back( extract< std::string >(
                                     holder[ candidate_property.c_str() ] ) );
    }
  }

  return CandidateRepository::Instance().GetCandidatesForStrings(
           candidate_strings );
}

} // unnamed namespace

boost::python::list FilterAndSortCandidates(
  const boost::python::list &candidates,
  const std::string &candidate_property,
  const std::string &query ) {
  pylist filtered_candidates;

  if ( query.empty() )
    return filtered_candidates;

  std::vector< const Candidate * > repository_candidates =
    CandidatesFromObjectList( candidates, candidate_property );

  Bitset query_bitset = LetterBitsetFromString( query );
  bool query_has_uppercase_letters = any_of( query, is_upper() );

  int num_candidates = len( candidates );
  std::vector< ResultAnd< int > > object_and_results;

  for ( int i = 0; i < num_candidates; ++i ) {
    const Candidate *candidate = repository_candidates[ i ];

    if ( !candidate->MatchesQueryBitset( query_bitset ) )
      continue;

    Result result = candidate->QueryMatchResult( query,
                                                 query_has_uppercase_letters );

    if ( result.IsSubsequence() ) {
      ResultAnd< int > object_and_result( i, result );
      object_and_results.push_back( boost::move( object_and_result ) );
    }
  }

  std::sort( object_and_results.begin(), object_and_results.end() );

  foreach ( const ResultAnd< int > &object_and_result,
            object_and_results ) {
    filtered_candidates.append( candidates[ object_and_result.extra_object_ ] );
  }

  return filtered_candidates;
}

boost::python::list FilterAndSortMultiEncodedCandidates(
  const boost::python::list &candidates,
  const std::string &query ) {

  boost::python::list filtered_candidates;
  int num_candidates = len( candidates );
  std::vector< Match > matches;

  if ( query.empty() )
    return candidates;

  for ( int i = 0; i < num_candidates; i++ )
  {
    Match match;
    match.str = extract< std::string > ( candidates[ i ] );

    MatchObject m;
    m.str                = match.str;
    m.str_len            = match.str.length();
    m.query              = query;
    m.query_len          = query.length();
    m.max_score_per_char = ( 1.0 / m.str_len + 1.0 / m.query_len ) / 2;
    m.is_dot_file        = 0;

    match.score = CalculateMatchScore( &m, 0, 0, 0, 0.0 );

    if ( match.score > 0 )
      matches.push_back( match );
  }

  typedef bool ( *comparer_t )( Match, Match );
  comparer_t cmp = &CompareMatchScore;
  std::sort( matches.begin(), matches.end(), cmp );

  foreach ( const Match &match, matches ) {
    filtered_candidates.append( match.str );
  }

  return filtered_candidates;
}

} // namespace YouCompleteMe
