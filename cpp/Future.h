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

#ifndef FUTURE_H_NR1U6MZS
#define FUTURE_H_NR1U6MZS

#include <boost/thread.hpp>
#include <boost/python.hpp>
#include <boost/shared_ptr.hpp>

namespace YouCompleteMe
{

class Result;

typedef boost::python::list Pylist;
typedef boost::shared_ptr< std::vector< Result > > AsyncResults;

class Future
{
public:
  Future() {}
  Future( boost::shared_future< AsyncResults > future );
  bool ResultsReady();
  void GetResults( Pylist &candidates );

private:
  boost::shared_future< AsyncResults > future_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: FUTURE_H_NR1U6MZS */
