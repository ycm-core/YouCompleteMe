#ifndef BOOST_THREAD_CONDITION_VARIABLE_PTHREAD_HPP
#define BOOST_THREAD_CONDITION_VARIABLE_PTHREAD_HPP
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)
// (C) Copyright 2007-10 Anthony Williams
// (C) Copyright 2011 Vicente J. Botet Escriba

#include <boost/thread/pthread/timespec.hpp>
#include <boost/thread/pthread/pthread_mutex_scoped_lock.hpp>
#include <boost/thread/pthread/thread_data.hpp>
#include <boost/thread/pthread/condition_variable_fwd.hpp>
#ifdef BOOST_THREAD_USES_CHRONO
#include <boost/chrono/system_clocks.hpp>
#include <boost/chrono/ceil.hpp>
#endif
#include <boost/thread/detail/delete.hpp>

#include <boost/config/abi_prefix.hpp>

namespace boost
{
    namespace this_thread
    {
        void BOOST_THREAD_DECL interruption_point();
    }

    namespace thread_cv_detail
    {
        template<typename MutexType>
        struct lock_on_exit
        {
            MutexType* m;

            lock_on_exit():
                m(0)
            {}

            void activate(MutexType& m_)
            {
                m_.unlock();
                m=&m_;
            }
            ~lock_on_exit()
            {
                if(m)
                {
                    m->lock();
                }
           }
        };
    }

    inline void condition_variable::wait(unique_lock<mutex>& m)
    {
        int res=0;
        {
            thread_cv_detail::lock_on_exit<unique_lock<mutex> > guard;
            detail::interruption_checker check_for_interruption(&internal_mutex,&cond);
            guard.activate(m);
            do {
              res = pthread_cond_wait(&cond,&internal_mutex);
            } while (res == EINTR);
        }
        this_thread::interruption_point();
        if(res)
        {
            boost::throw_exception(condition_error(res, "boost:: condition_variable constructor failed in pthread_cond_wait"));
        }
    }

    inline bool condition_variable::do_timed_wait(
                unique_lock<mutex>& m,
                struct timespec const &timeout)
    {
        if (!m.owns_lock())
            boost::throw_exception(condition_error(EPERM, "condition_variable do_timed_wait: mutex not locked"));

        thread_cv_detail::lock_on_exit<unique_lock<mutex> > guard;
        int cond_res;
        {
            detail::interruption_checker check_for_interruption(&internal_mutex,&cond);
            guard.activate(m);
            cond_res=pthread_cond_timedwait(&cond,&internal_mutex,&timeout);
        }
        this_thread::interruption_point();
        if(cond_res==ETIMEDOUT)
        {
            return false;
        }
        if(cond_res)
        {
            boost::throw_exception(condition_error(cond_res, "condition_variable failed in pthread_cond_timedwait"));
        }
        return true;
    }

    inline void condition_variable::notify_one() BOOST_NOEXCEPT
    {
        boost::pthread::pthread_mutex_scoped_lock internal_lock(&internal_mutex);
        BOOST_VERIFY(!pthread_cond_signal(&cond));
    }

    inline void condition_variable::notify_all() BOOST_NOEXCEPT
    {
        boost::pthread::pthread_mutex_scoped_lock internal_lock(&internal_mutex);
        BOOST_VERIFY(!pthread_cond_broadcast(&cond));
    }

    class condition_variable_any
    {
        pthread_mutex_t internal_mutex;
        pthread_cond_t cond;

    public:
        BOOST_THREAD_NO_COPYABLE(condition_variable_any)
        condition_variable_any()
        {
            int const res=pthread_mutex_init(&internal_mutex,NULL);
            if(res)
            {
                boost::throw_exception(thread_resource_error(res, "condition_variable_any failed in pthread_mutex_init"));
            }
            int const res2=pthread_cond_init(&cond,NULL);
            if(res2)
            {
                BOOST_VERIFY(!pthread_mutex_destroy(&internal_mutex));
                boost::throw_exception(thread_resource_error(res, "condition_variable_any failed in pthread_cond_init"));
            }
        }
        ~condition_variable_any()
        {
            BOOST_VERIFY(!pthread_mutex_destroy(&internal_mutex));
            BOOST_VERIFY(!pthread_cond_destroy(&cond));
        }

        template<typename lock_type>
        void wait(lock_type& m)
        {
            int res=0;
            {
                thread_cv_detail::lock_on_exit<lock_type> guard;
                detail::interruption_checker check_for_interruption(&internal_mutex,&cond);
                guard.activate(m);
                res=pthread_cond_wait(&cond,&internal_mutex);
            }
            this_thread::interruption_point();
            if(res)
            {
                boost::throw_exception(condition_error(res, "condition_variable_any failed in pthread_cond_wait"));
            }
        }

        template<typename lock_type,typename predicate_type>
        void wait(lock_type& m,predicate_type pred)
        {
            while(!pred()) wait(m);
        }

        template<typename lock_type>
        bool timed_wait(lock_type& m,boost::system_time const& wait_until)
        {
            struct timespec const timeout=detail::get_timespec(wait_until);
            return do_timed_wait(m, timeout);
        }
        template<typename lock_type>
        bool timed_wait(lock_type& m,xtime const& wait_until)
        {
            return timed_wait(m,system_time(wait_until));
        }

        template<typename lock_type,typename duration_type>
        bool timed_wait(lock_type& m,duration_type const& wait_duration)
        {
            return timed_wait(m,get_system_time()+wait_duration);
        }

        template<typename lock_type,typename predicate_type>
        bool timed_wait(lock_type& m,boost::system_time const& wait_until,predicate_type pred)
        {
            while (!pred())
            {
                if(!timed_wait(m, wait_until))
                    return pred();
            }
            return true;
        }

        template<typename lock_type,typename predicate_type>
        bool timed_wait(lock_type& m,xtime const& wait_until,predicate_type pred)
        {
            return timed_wait(m,system_time(wait_until),pred);
        }

        template<typename lock_type,typename duration_type,typename predicate_type>
        bool timed_wait(lock_type& m,duration_type const& wait_duration,predicate_type pred)
        {
            return timed_wait(m,get_system_time()+wait_duration,pred);
        }

#ifdef BOOST_THREAD_USES_CHRONO
        template <class lock_type,class Duration>
        cv_status
        wait_until(
                lock_type& lock,
                const chrono::time_point<chrono::system_clock, Duration>& t)
        {
          using namespace chrono;
          typedef time_point<system_clock, nanoseconds> nano_sys_tmpt;
          wait_until(lock,
                        nano_sys_tmpt(ceil<nanoseconds>(t.time_since_epoch())));
          return system_clock::now() < t ? cv_status::no_timeout :
                                             cv_status::timeout;
        }

        template <class lock_type, class Clock, class Duration>
        cv_status
        wait_until(
                lock_type& lock,
                const chrono::time_point<Clock, Duration>& t)
        {
          using namespace chrono;
          system_clock::time_point     s_now = system_clock::now();
          typename Clock::time_point  c_now = Clock::now();
          wait_until(lock, s_now + ceil<nanoseconds>(t - c_now));
          return Clock::now() < t ? cv_status::no_timeout : cv_status::timeout;
        }

        template <class lock_type, class Clock, class Duration, class Predicate>
        bool
        wait_until(
                lock_type& lock,
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


        template <class lock_type, class Rep, class Period>
        cv_status
        wait_for(
                lock_type& lock,
                const chrono::duration<Rep, Period>& d)
        {
          using namespace chrono;
          system_clock::time_point s_now = system_clock::now();
          steady_clock::time_point c_now = steady_clock::now();
          wait_until(lock, s_now + ceil<nanoseconds>(d));
          return steady_clock::now() - c_now < d ? cv_status::no_timeout :
                                                   cv_status::timeout;

        }


        template <class lock_type, class Rep, class Period, class Predicate>
        bool
        wait_for(
                lock_type& lock,
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

        template <class lock_type>
        inline void wait_until(
            lock_type& lk,
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

        void notify_one() BOOST_NOEXCEPT
        {
            boost::pthread::pthread_mutex_scoped_lock internal_lock(&internal_mutex);
            BOOST_VERIFY(!pthread_cond_signal(&cond));
        }

        void notify_all() BOOST_NOEXCEPT
        {
            boost::pthread::pthread_mutex_scoped_lock internal_lock(&internal_mutex);
            BOOST_VERIFY(!pthread_cond_broadcast(&cond));
        }
    private: // used by boost::thread::try_join_until

        template <class lock_type>
        inline bool do_timed_wait(
          lock_type& m,
          struct timespec const &timeout)
        {
          int res=0;
          {
              thread_cv_detail::lock_on_exit<lock_type> guard;
              detail::interruption_checker check_for_interruption(&internal_mutex,&cond);
              guard.activate(m);
              res=pthread_cond_timedwait(&cond,&internal_mutex,&timeout);
          }
          this_thread::interruption_point();
          if(res==ETIMEDOUT)
          {
              return false;
          }
          if(res)
          {
              boost::throw_exception(condition_error(res, "condition_variable_any failed in pthread_cond_timedwait"));
          }
          return true;
        }


    };

}

#include <boost/config/abi_suffix.hpp>

#endif
