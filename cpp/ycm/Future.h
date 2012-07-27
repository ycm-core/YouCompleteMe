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
#include <boost/make_shared.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/function.hpp>

namespace YouCompleteMe
{

class Result;
typedef boost::shared_ptr< boost::packaged_task< void > > VoidTask;

template< typename T >
boost::shared_ptr< T > ReturnValueAsShared(
    boost::function< T() > func )
{
  return boost::make_shared< T >( func() );
}


template< typename T >
class Future
{
public:
  Future() {};
  Future( boost::shared_future< T > future )
    : future_( boost::move( future ) ) {}

  bool ResultsReady()
  {
    // It's OK to return true since GetResults will just return a
    // default-constructed value if the future_ is uninitialized. If we don't
    // return true for this case, any loop waiting on ResultsReady will wait
    // forever.
    if ( future_.get_state() == boost::future_state::uninitialized )
      return true;

    return future_.is_ready();
  }


  T GetResults()
  {
    try
    {
      return future_.get();
    }

    catch ( boost::future_uninitialized & )
    {
      // Do nothing and return a T()
    }

    return T();
  }

private:
  boost::shared_future< T > future_;
};

} // namespace YouCompleteMe

#endif /* end of include guard: FUTURE_H_NR1U6MZS */
