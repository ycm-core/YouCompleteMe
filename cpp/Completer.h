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

#ifndef COMPLETER_H_7AR4UGXE
#define COMPLETER_H_7AR4UGXE

#include "Candidate.h"

#include <boost/utility.hpp>
#include <boost/python.hpp>
#include <boost/unordered_map.hpp>

#include <set>
#include <vector>
#include <string>

namespace YouCompleteMe
{

typedef boost::python::list Pylist;
typedef boost::unordered_map< std::string, Candidate* > CandidateRepository;

// class Completer : boost::noncopyable
class Completer
{
public:
  Completer() {}
  Completer( const Pylist &candidates );
  Completer( const Pylist &candidates, const std::string &filepath );
  ~Completer();

  void AddCandidatesToDatabase( const Pylist &candidates,
                                const std::string &filepath );

	void GetCandidatesForQuery(
			const std::string &query, Pylist &candidates ) const;

private:
  struct CandidatePointerLess
  {
    bool operator() ( const Candidate *first, const Candidate *second )
    {
      return first->Text() < second->Text();
    }
  };

  CandidateRepository candidate_repository_;
	std::set< Candidate*, CandidatePointerLess > candidates_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: COMPLETER_H_7AR4UGXE */

