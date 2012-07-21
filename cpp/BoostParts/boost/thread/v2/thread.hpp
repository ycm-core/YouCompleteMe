// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)
// (C) Copyright 2011 Vicente J. Botet Escriba

#ifndef BOOST_THREAD_V2_THREAD_HPP
#define BOOST_THREAD_V2_THREAD_HPP

#include <boost/thread/detail/config.hpp>
#ifdef BOOST_THREAD_USES_CHRONO
#include <boost/chrono/system_clocks.hpp>
#endif
#include <boost/thread/condition_variable.hpp>
#include <boost/thread/locks.hpp>

namespace boost
{
  namespace this_thread
  {

#ifdef BOOST_THREAD_USES_CHRONO

    template <class Rep, class Period>
    void sleep_for(const chrono::duration<Rep, Period>& d)
    {
      using namespace chrono;
      nanoseconds ns = duration_cast<nanoseconds> (d);
      if (ns < d) ++ns;
      sleep_for(ns);
    }

    template <class Clock, class Duration>
    void sleep_until(const chrono::time_point<Clock, Duration>& t)
    {
      using namespace chrono;
      mutex mut;
      condition_variable cv;
      unique_lock<mutex> lk(mut);
      while (Clock::now() < t)
        cv.wait_until(lk, t);
    }

    template <class Duration>
    inline BOOST_SYMBOL_VISIBLE
    void sleep_until(const chrono::time_point<chrono::steady_clock, Duration>& t)
    {
      using namespace chrono;
      sleep_for(t - steady_clock::now());
    }

#endif
  }
}


#endif
