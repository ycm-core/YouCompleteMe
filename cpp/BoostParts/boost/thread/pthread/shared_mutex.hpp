#ifndef BOOST_THREAD_PTHREAD_SHARED_MUTEX_HPP
#define BOOST_THREAD_PTHREAD_SHARED_MUTEX_HPP

//  (C) Copyright 2006-8 Anthony Williams
//  (C) Copyright 2012 Vicente J. Botet Escriba
//
//  Distributed under the Boost Software License, Version 1.0. (See
//  accompanying file LICENSE_1_0.txt or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

#include <boost/assert.hpp>
#include <boost/static_assert.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/condition_variable.hpp>
#include <boost/thread/detail/thread_interruption.hpp>
#ifdef BOOST_THREAD_USES_CHRONO
#include <boost/chrono/system_clocks.hpp>
#include <boost/chrono/ceil.hpp>
#endif
#include <boost/thread/detail/delete.hpp>

#include <boost/config/abi_prefix.hpp>

namespace boost
{
    class shared_mutex
    {
    private:
        struct state_data
        {
            unsigned shared_count;
            bool exclusive;
            bool upgrade;
            bool exclusive_waiting_blocked;
        };



        state_data state;
        boost::mutex state_change;
        boost::condition_variable shared_cond;
        boost::condition_variable exclusive_cond;
        boost::condition_variable upgrade_cond;

        void release_waiters()
        {
            exclusive_cond.notify_one();
            shared_cond.notify_all();
        }

    public:
        BOOST_THREAD_NO_COPYABLE(shared_mutex)

        shared_mutex()
        {
            state_data state_={0,0,0,0};
            state=state_;
        }

        ~shared_mutex()
        {
        }

        void lock_shared()
        {
            boost::this_thread::disable_interruption do_not_disturb;
            boost::mutex::scoped_lock lk(state_change);

            while(state.exclusive || state.exclusive_waiting_blocked)
            {
                shared_cond.wait(lk);
            }
            ++state.shared_count;
        }

        bool try_lock_shared()
        {
            boost::mutex::scoped_lock lk(state_change);

            if(state.exclusive || state.exclusive_waiting_blocked)
            {
                return false;
            }
            else
            {
                ++state.shared_count;
                return true;
            }
        }

        bool timed_lock_shared(system_time const& timeout)
        {
            boost::this_thread::disable_interruption do_not_disturb;
            boost::mutex::scoped_lock lk(state_change);

            while(state.exclusive || state.exclusive_waiting_blocked)
            {
                if(!shared_cond.timed_wait(lk,timeout))
                {
                    return false;
                }
            }
            ++state.shared_count;
            return true;
        }

        template<typename TimeDuration>
        bool timed_lock_shared(TimeDuration const & relative_time)
        {
            return timed_lock_shared(get_system_time()+relative_time);
        }
#ifdef BOOST_THREAD_USES_CHRONO
        template <class Rep, class Period>
        bool try_lock_shared_for(const chrono::duration<Rep, Period>& rel_time)
        {
          return try_lock_shared_until(chrono::steady_clock::now() + rel_time);
        }
        template <class Clock, class Duration>
        bool try_lock_shared_until(const chrono::time_point<Clock, Duration>& abs_time)
        {
          boost::this_thread::disable_interruption do_not_disturb;
          boost::mutex::scoped_lock lk(state_change);

          while(state.exclusive || state.exclusive_waiting_blocked)
          {
              if(cv_status::timeout==shared_cond.wait_until(lk,abs_time))
              {
                  return false;
              }
          }
          ++state.shared_count;
          return true;
        }
#endif
        void unlock_shared()
        {
            boost::mutex::scoped_lock lk(state_change);
            bool const last_reader=!--state.shared_count;

            if(last_reader)
            {
                if(state.upgrade)
                {
                    state.upgrade=false;
                    state.exclusive=true;
                    upgrade_cond.notify_one();
                }
                else
                {
                    state.exclusive_waiting_blocked=false;
                }
                release_waiters();
            }
        }

        void lock()
        {
            boost::this_thread::disable_interruption do_not_disturb;
            boost::mutex::scoped_lock lk(state_change);

            while(state.shared_count || state.exclusive)
            {
                state.exclusive_waiting_blocked=true;
                exclusive_cond.wait(lk);
            }
            state.exclusive=true;
        }

        bool timed_lock(system_time const& timeout)
        {
            boost::this_thread::disable_interruption do_not_disturb;
            boost::mutex::scoped_lock lk(state_change);

            while(state.shared_count || state.exclusive)
            {
                state.exclusive_waiting_blocked=true;
                if(!exclusive_cond.timed_wait(lk,timeout))
                {
                    if(state.shared_count || state.exclusive)
                    {
                        state.exclusive_waiting_blocked=false;
                        release_waiters();
                        return false;
                    }
                    break;
                }
            }
            state.exclusive=true;
            return true;
        }

        template<typename TimeDuration>
        bool timed_lock(TimeDuration const & relative_time)
        {
            return timed_lock(get_system_time()+relative_time);
        }

#ifdef BOOST_THREAD_USES_CHRONO
        template <class Rep, class Period>
        bool try_lock_for(const chrono::duration<Rep, Period>& rel_time)
        {
          return try_lock_until(chrono::steady_clock::now() + rel_time);
        }
        template <class Clock, class Duration>
        bool try_lock_until(const chrono::time_point<Clock, Duration>& abs_time)
        {
          boost::this_thread::disable_interruption do_not_disturb;
          boost::mutex::scoped_lock lk(state_change);

          while(state.shared_count || state.exclusive)
          {
              state.exclusive_waiting_blocked=true;
              if(cv_status::timeout == exclusive_cond.wait_until(lk,abs_time))
              {
                  if(state.shared_count || state.exclusive)
                  {
                      state.exclusive_waiting_blocked=false;
                      release_waiters();
                      return false;
                  }
                  break;
              }
          }
          state.exclusive=true;
          return true;
        }
#endif

        bool try_lock()
        {
            boost::mutex::scoped_lock lk(state_change);

            if(state.shared_count || state.exclusive)
            {
                return false;
            }
            else
            {
                state.exclusive=true;
                return true;
            }

        }

        void unlock()
        {
            boost::mutex::scoped_lock lk(state_change);
            state.exclusive=false;
            state.exclusive_waiting_blocked=false;
            release_waiters();
        }

        void lock_upgrade()
        {
            boost::this_thread::disable_interruption do_not_disturb;
            boost::mutex::scoped_lock lk(state_change);
            while(state.exclusive || state.exclusive_waiting_blocked || state.upgrade)
            {
                shared_cond.wait(lk);
            }
            ++state.shared_count;
            state.upgrade=true;
        }

        bool timed_lock_upgrade(system_time const& timeout)
        {
            boost::this_thread::disable_interruption do_not_disturb;
            boost::mutex::scoped_lock lk(state_change);
            while(state.exclusive || state.exclusive_waiting_blocked || state.upgrade)
            {
                if(!shared_cond.timed_wait(lk,timeout))
                {
                    if(state.exclusive || state.exclusive_waiting_blocked || state.upgrade)
                    {
                        return false;
                    }
                    break;
                }
            }
            ++state.shared_count;
            state.upgrade=true;
            return true;
        }

        template<typename TimeDuration>
        bool timed_lock_upgrade(TimeDuration const & relative_time)
        {
            return timed_lock_upgrade(get_system_time()+relative_time);
        }

#ifdef BOOST_THREAD_USES_CHRONO
        template <class Rep, class Period>
        bool try_lock_upgrade_for(const chrono::duration<Rep, Period>& rel_time)
        {
          return try_lock_upgrade_until(chrono::steady_clock::now() + rel_time);
        }
        template <class Clock, class Duration>
        bool try_lock_upgrade_until(const chrono::time_point<Clock, Duration>& abs_time)
        {
          boost::this_thread::disable_interruption do_not_disturb;
          boost::mutex::scoped_lock lk(state_change);
          while(state.exclusive || state.exclusive_waiting_blocked || state.upgrade)
          {
              if(cv_status::timeout == shared_cond.wait_until(lk,abs_time))
              {
                  if(state.exclusive || state.exclusive_waiting_blocked || state.upgrade)
                  {
                      return false;
                  }
                  break;
              }
          }
          ++state.shared_count;
          state.upgrade=true;
          return true;
        }
#endif
        bool try_lock_upgrade()
        {
            boost::mutex::scoped_lock lk(state_change);
            if(state.exclusive || state.exclusive_waiting_blocked || state.upgrade)
            {
                return false;
            }
            else
            {
                ++state.shared_count;
                state.upgrade=true;
                return true;
            }
        }

        void unlock_upgrade()
        {
            boost::mutex::scoped_lock lk(state_change);
            state.upgrade=false;
            bool const last_reader=!--state.shared_count;

            if(last_reader)
            {
                state.exclusive_waiting_blocked=false;
                release_waiters();
            } else {
              shared_cond.notify_all();
            }
        }

        // Upgrade <-> Exclusive
        void unlock_upgrade_and_lock()
        {
            boost::this_thread::disable_interruption do_not_disturb;
            boost::mutex::scoped_lock lk(state_change);
            --state.shared_count;
            while(state.shared_count)
            {
                upgrade_cond.wait(lk);
            }
            state.upgrade=false;
            state.exclusive=true;
        }

        void unlock_and_lock_upgrade()
        {
            boost::mutex::scoped_lock lk(state_change);
            state.exclusive=false;
            state.upgrade=true;
            ++state.shared_count;
            state.exclusive_waiting_blocked=false;
            release_waiters();
        }

        bool try_unlock_upgrade_and_lock()
        {
          boost::mutex::scoped_lock lk(state_change);
          if(    !state.exclusive
              && !state.exclusive_waiting_blocked
              && state.upgrade
              && state.shared_count==1)
          {
            state.shared_count=0;
            state.exclusive=true;
            state.upgrade=false;
            return true;
          }
          return false;
        }
#ifdef BOOST_THREAD_USES_CHRONO
        template <class Rep, class Period>
        bool
        try_unlock_upgrade_and_lock_for(
                                const chrono::duration<Rep, Period>& rel_time)
        {
          return try_unlock_upgrade_and_lock_until(
                                 chrono::steady_clock::now() + rel_time);
        }
        template <class Clock, class Duration>
        bool
        try_unlock_upgrade_and_lock_until(
                          const chrono::time_point<Clock, Duration>& abs_time)
        {
          boost::this_thread::disable_interruption do_not_disturb;
          boost::mutex::scoped_lock lk(state_change);
          if (state.shared_count != 1)
          {
              for (;;)
              {
                cv_status status = shared_cond.wait_until(lk,abs_time);
                if (state.shared_count == 1)
                  break;
                if(status == cv_status::timeout)
                  return false;
              }
          }
          state.upgrade=false;
          state.exclusive=true;
          state.exclusive_waiting_blocked=false;
          state.shared_count=0;
          return true;
        }
#endif

        // Shared <-> Exclusive
        void unlock_and_lock_shared()
        {
            boost::mutex::scoped_lock lk(state_change);
            state.exclusive=false;
            ++state.shared_count;
            state.exclusive_waiting_blocked=false;
            release_waiters();
        }

#ifdef BOOST_THREAD_PROVIDES_SHARED_MUTEX_UPWARDS_CONVERSIONS
        bool try_unlock_shared_and_lock()
        {
          boost::mutex::scoped_lock lk(state_change);
          if(    !state.exclusive
              && !state.exclusive_waiting_blocked
              && !state.upgrade
              && state.shared_count==1)
          {
            state.shared_count=0;
            state.exclusive=true;
            return true;
          }
          return false;
        }
#ifdef BOOST_THREAD_USES_CHRONO
        template <class Rep, class Period>
            bool
            try_unlock_shared_and_lock_for(
                                const chrono::duration<Rep, Period>& rel_time)
        {
          return try_unlock_shared_and_lock_until(
                                 chrono::steady_clock::now() + rel_time);
        }
        template <class Clock, class Duration>
            bool
            try_unlock_shared_and_lock_until(
                          const chrono::time_point<Clock, Duration>& abs_time)
        {
          boost::this_thread::disable_interruption do_not_disturb;
          boost::mutex::scoped_lock lk(state_change);
          if (state.shared_count != 1)
          {
              for (;;)
              {
                cv_status status = shared_cond.wait_until(lk,abs_time);
                if (state.shared_count == 1)
                  break;
                if(status == cv_status::timeout)
                  return false;
              }
          }
          state.upgrade=false;
          state.exclusive=true;
          state.exclusive_waiting_blocked=false;
          state.shared_count=0;
          return true;
        }
#endif
#endif

        // Shared <-> Upgrade
        void unlock_upgrade_and_lock_shared()
        {
            boost::mutex::scoped_lock lk(state_change);
            state.upgrade=false;
            state.exclusive_waiting_blocked=false;
            release_waiters();
        }

#ifdef BOOST_THREAD_PROVIDES_SHARED_MUTEX_UPWARDS_CONVERSIONS
        bool try_unlock_shared_and_lock_upgrade()
        {
          boost::mutex::scoped_lock lk(state_change);
          if(    !state.exclusive
              && !state.exclusive_waiting_blocked
              && !state.upgrade
              )
          {
            state.upgrade=true;
            return true;
          }
          return false;
        }
#ifdef BOOST_THREAD_USES_CHRONO
        template <class Rep, class Period>
            bool
            try_unlock_shared_and_lock_upgrade_for(
                                const chrono::duration<Rep, Period>& rel_time)
        {
          return try_unlock_shared_and_lock_upgrade_until(
                                 chrono::steady_clock::now() + rel_time);
        }
        template <class Clock, class Duration>
            bool
            try_unlock_shared_and_lock_upgrade_until(
                          const chrono::time_point<Clock, Duration>& abs_time)
        {
          boost::this_thread::disable_interruption do_not_disturb;
          boost::mutex::scoped_lock lk(state_change);
          if(    state.exclusive
              || state.exclusive_waiting_blocked
              || state.upgrade
              )
          {
              for (;;)
              {
                cv_status status = exclusive_cond.wait_until(lk,abs_time);
                if(    ! state.exclusive
                    && ! state.exclusive_waiting_blocked
                    && ! state.upgrade
                    )
                  break;
                if(status == cv_status::timeout)
                  return false;
              }
          }
          state.upgrade=true;
          return true;
        }
#endif
#endif
    };

    typedef shared_mutex upgrade_mutex;
}

#include <boost/config/abi_suffix.hpp>

#endif
