#ifndef BOOST_THREAD_PTHREAD_CONDITION_VARIABLE_FWD_HPP
#define BOOST_THREAD_PTHREAD_CONDITION_VARIABLE_FWD_HPP
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)
// (C) Copyright 2007-8 Anthony Williams
// (C) Copyright 2011 Vicente J. Botet Escriba

#include <boost/assert.hpp>
#include <boost/throw_exception.hpp>
#include <pthread.h>
#include <boost/thread/cv_status.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/locks.hpp>
#include <boost/thread/thread_time.hpp>
#include <boost/thread/xtime.hpp>
#ifdef BOOST_THREAD_USES_CHRONO
#include <boost/chrono/system_clocks.hpp>
#include <boost/chrono/ceil.hpp>
#endif
#include <boost/thread/detail/delete.hpp>
#include <boost/date_time/posix_time/posix_time_duration.hpp>
#include <boost/config/abi_prefix.hpp>

namespace boost
{

    class condition_variable
    {
    private:
        pthread_mutex_t internal_mutex;
        pthread_cond_t cond;

    public:
      BOOST_THREAD_NO_COPYABLE(condition_variable)
        condition_variable()
        {
            int const res=pthread_mutex_init(&internal_mutex,NULL);
            if(res)
            {
                boost::throw_exception(thread_resource_error(res, "boost:: condition_variable constructor failed in pthread_mutex_init"));
            }
            int const res2=pthread_cond_init(&cond,NULL);
            if(res2)
            {
                BOOST_VERIFY(!pthread_mutex_destroy(&internal_mutex));
                boost::throw_exception(thread_resource_error(res2, "boost:: condition_variable constructor failed in pthread_cond_init"));
            }
        }
        ~condition_variable()
        {
            BOOST_VERIFY(!pthread_mutex_destroy(&internal_mutex));
            int ret;
            do {
              ret = pthread_cond_destroy(&cond);
            } while (ret == EINTR);
            BOOST_VERIFY(!ret);
        }

        void wait(unique_lock<mutex>& m);

        template<typename predicate_type>
        void wait(unique_lock<mutex>& m,predicate_type pred)
        {
            while(!pred()) wait(m);
        }


        inline bool timed_wait(
            unique_lock<mutex>& m,
            boost::system_time const& wait_until)
        {
#if defined BOOST_THREAD_WAIT_BUG
            struct timespec const timeout=detail::get_timespec(wait_until + BOOST_THREAD_WAIT_BUG);
            return do_timed_wait(m, timeout);
#else
            struct timespec const timeout=detail::get_timespec(wait_until);
            return do_timed_wait(m, timeout);
#endif
        }
        bool timed_wait(
            unique_lock<mutex>& m,
            xtime const& wait_until)
        {
            return timed_wait(m,system_time(wait_until));
        }

        template<typename duration_type>
        bool timed_wait(
            unique_lock<mutex>& m,
            duration_type const& wait_duration)
        {
            return timed_wait(m,get_system_time()+wait_duration);
        }

        template<typename predicate_type>
        bool timed_wait(
            unique_lock<mutex>& m,
            boost::system_time const& wait_until,predicate_type pred)
        {
            while (!pred())
            {
                if(!timed_wait(m, wait_until))
                    return pred();
            }
            return true;
        }

        template<typename predicate_type>
        bool timed_wait(
            unique_lock<mutex>& m,
            xtime const& wait_until,predicate_type pred)
        {
            return timed_wait(m,system_time(wait_until),pred);
        }

        template<typename duration_type,typename predicate_type>
        bool timed_wait(
            unique_lock<mutex>& m,
            duration_type const& wait_duration,predicate_type pred)
        {
            return timed_wait(m,get_system_time()+wait_duration,pred);
        }

#ifdef BOOST_THREAD_USES_CHRONO

        template <class Duration>
        cv_status
        wait_until(
                unique_lock<mutex>& lock,
                const chrono::time_point<chrono::system_clock, Duration>& t)
        {
          using namespace chrono;
          typedef time_point<system_clock, nanoseconds> nano_sys_tmpt;
          wait_until(lock,
                        nano_sys_tmpt(ceil<nanoseconds>(t.time_since_epoch())));
          return system_clock::now() < t ? cv_status::no_timeout :
                                             cv_status::timeout;
        }

        template <class Clock, class Duration>
        cv_status
        wait_until(
                unique_lock<mutex>& lock,
                const chrono::time_point<Clock, Duration>& t)
        {
          using namespace chrono;
          system_clock::time_point     s_now = system_clock::now();
          typename Clock::time_point  c_now = Clock::now();
          wait_until(lock, s_now + ceil<nanoseconds>(t - c_now));
          return Clock::now() < t ? cv_status::no_timeout : cv_status::timeout;
        }

        template <class Clock, class Duration, class Predicate>
        bool
        wait_until(
                unique_lock<mutex>& lock,
                const chrono::time_point<Clock, Duration>& t,
                Predicate pred)
        {
            while (!pred())
            {
                if (wait_until(lock, t) == cv_status::timeout)
                    return pred();
            }
            return true;
        }


        template <class Rep, class Period>
        cv_status
        wait_for(
                unique_lock<mutex>& lock,
                const chrono::duration<Rep, Period>& d)
        {
          using namespace chrono;
          system_clock::time_point s_now = system_clock::now();
          steady_clock::time_point c_now = steady_clock::now();
          wait_until(lock, s_now + ceil<nanoseconds>(d));
          return steady_clock::now() - c_now < d ? cv_status::no_timeout :
                                                   cv_status::timeout;

        }


        template <class Rep, class Period, class Predicate>
        bool
        wait_for(
                unique_lock<mutex>& lock,
                const chrono::duration<Rep, Period>& d,
                Predicate pred)
        {
          while (!pred())
          {
              if (wait_for(lock, d) == cv_status::timeout)
                  return pred();
          }
          return true;
        }
#endif

#define BOOST_THREAD_DEFINES_CONDITION_VARIABLE_NATIVE_HANDLE
        typedef pthread_cond_t* native_handle_type;
        native_handle_type native_handle()
        {
            return &cond;
        }

        void notify_one() BOOST_NOEXCEPT;
        void notify_all() BOOST_NOEXCEPT;

#ifdef BOOST_THREAD_USES_CHRONO
        inline void wait_until(
            unique_lock<mutex>& lk,
            chrono::time_point<chrono::system_clock, chrono::nanoseconds> tp)
        {
            using namespace chrono;
            nanoseconds d = tp.time_since_epoch();
            timespec ts;
            seconds s = duration_cast<seconds>(d);
            ts.tv_sec = static_cast<long>(s.count());
            ts.tv_nsec = static_cast<long>((d - s).count());
            do_timed_wait(lk, ts);
        }
#endif
        //private: // used by boost::thread::try_join_until

        inline bool do_timed_wait(
            unique_lock<mutex>& lock,
            struct timespec const &timeout);
    };
}

#include <boost/config/abi_suffix.hpp>

#endif
