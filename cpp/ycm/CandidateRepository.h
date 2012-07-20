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

#ifndef CANDIDATEREPOSITORY_H_K9OVCMHG
#define CANDIDATEREPOSITORY_H_K9OVCMHG

#include <boost/utility.hpp>
#include <boost/unordered_map.hpp>
#include <boost/thread/mutex.hpp>

#include <vector>
#include <string>

namespace YouCompleteMe
{

class Candidate;
struct CompletionData;

typedef boost::unordered_map< std::string, const Candidate* >
          CandidateHolder;

class CandidateRepository : boost::noncopyable
{
public:
  static CandidateRepository& Instance();

  std::vector< const Candidate* > GetCandidatesForStrings(
      const std::vector< std::string > &strings );

  std::vector< const Candidate* > GetCandidatesForStrings(
      const std::vector< CompletionData > &datas );

private:
  CandidateRepository() {};
  ~CandidateRepository();

  boost::mutex holder_mutex_;

  static boost::mutex singleton_mutex_;
  static CandidateRepository *instance_;

  // This data structure owns all the Candidate pointers
  CandidateHolder candidate_holder_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: CANDIDATEREPOSITORY_H_K9OVCMHG */

