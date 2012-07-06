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

#ifndef CONCURRENTLATESTVALUE_H_SYF1JPPG
#define CONCURRENTLATESTVALUE_H_SYF1JPPG

#include <boost/thread.hpp>
#include <boost/utility.hpp>

namespace YouCompleteMe
{

// This is is basically a multi-consumer single-producer queue, only with the
// twist that we only care about the latest value set. So the GUI thread is the
// setter, and the worker threads are the workers. The workers wait in line on
// the condition variable and when the setter sets a value, a worker is chosen
// to consume it.
//
// The point is that we always want to have one "fresh" worker thread ready to
// work on our latest value. If a newer value is set, then we don't care what
// happens to the old values.
//
// This implementation is mutex-based and is not lock-free. Normally using a
// lock-free data structure makes more sense, but since the GUI thread goes
// through VimL and Python on every keystroke, there's really no point. Those 5
// nanoseconds it takes to lock a mutex are laughably negligible compared to the
// VimL/Python overhead.
template <typename T>
class ConcurrentLatestValue : boost::noncopyable
{
public:

  ConcurrentLatestValue() : empty_( true ) {}

  void Set( const T& data )
  {
    {
      boost::unique_lock< boost::mutex > lock( mutex_ );
      latest_ = data;
      empty_ = false;
    }

    condition_variable_.notify_one();
  }

  T Get()
  {
    boost::unique_lock< boost::mutex > lock( mutex_ );

    while ( empty_ )
    {
      condition_variable_.wait( lock );
    }

    empty_ = true;
    return latest_;
  }


private:
  T latest_;
  bool empty_;
  boost::mutex mutex_;
  boost::condition_variable condition_variable_;

};

} // namespace YouCompleteMe

#endif /* end of include guard: CONCURRENTLATESTVALUE_H_SYF1JPPG */
