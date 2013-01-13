#ifndef BOOST_THREAD_THREAD_COMMON_HPP
#define BOOST_THREAD_THREAD_COMMON_HPP
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)
// (C) Copyright 2007-10 Anthony Williams
// (C) Copyright 20011-12 Vicente J. Botet Escriba

#include <boost/thread/detail/config.hpp>
#include <boost/thread/exceptions.hpp>
#ifndef BOOST_NO_IOSTREAM
#include <ostream>
#endif
#include <boost/thread/detail/move.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/xtime.hpp>
#include <boost/thread/detail/thread_heap_alloc.hpp>
#include <boost/assert.hpp>
#include <list>
#include <algorithm>
#include <boost/ref.hpp>
#include <boost/cstdint.hpp>
#include <boost/bind.hpp>
#include <stdlib.h>
#include <memory>
//#include <vector>
//#include <utility>
#include <boost/utility/enable_if.hpp>
#include <boost/type_traits/remove_reference.hpp>
#include <boost/io/ios_state.hpp>
#include <boost/type_traits/is_same.hpp>
#include <boost/type_traits/decay.hpp>
#include <boost/functional/hash.hpp>
#ifdef BOOST_THREAD_USES_CHRONO
#include <boost/chrono/system_clocks.hpp>
#include <boost/chrono/ceil.hpp>
#endif

#include <boost/config/abi_prefix.hpp>

#ifdef BOOST_MSVC
#pragma warning(push)
#pragma warning(disable:4251)
#endif

namespace boost
{

    namespace detail
    {
        template<typename F>
        class thread_data:
            public detail::thread_data_base
        {
        public:
            BOOST_THREAD_NO_COPYABLE(thread_data)
#ifndef BOOST_NO_CXX11_RVALUE_REFERENCES
              thread_data(BOOST_THREAD_RV_REF(F) f_):
                f(boost::forward<F>(f_))
              {}
// This overloading must be removed if we want the packaged_task's tests to pass.
//            thread_data(F& f_):
//                f(f_)
//            {}
#else

            thread_data(BOOST_THREAD_RV_REF(F) f_):
              f(f_)
            {}
            thread_data(F f_):
                f(f_)
            {}
#endif
            //thread_data() {}

            void run()
            {
                f();
            }

        private:
            F f;
        };

        template<typename F>
        class thread_data<boost::reference_wrapper<F> >:
            public detail::thread_data_base
        {
        private:
            F& f;
        public:
            BOOST_THREAD_NO_COPYABLE(thread_data)
            thread_data(boost::reference_wrapper<F> f_):
                f(f_)
            {}
            void run()
            {
                f();
            }
        };

        template<typename F>
        class thread_data<const boost::reference_wrapper<F> >:
            public detail::thread_data_base
        {
        private:
            F& f;
        public:
            BOOST_THREAD_NO_COPYABLE(thread_data)
            thread_data(const boost::reference_wrapper<F> f_):
                f(f_)
            {}
            void run()
            {
                f();
            }
        };
    }

    class BOOST_THREAD_DECL thread
    {
    public:
      typedef thread_attributes attributes;

      BOOST_THREAD_MOVABLE_ONLY(thread)
    private:

        void release_handle();

        detail::thread_data_ptr thread_info;

        void start_thread();
        void start_thread(const attributes& attr);

        explicit thread(detail::thread_data_ptr data);

        detail::thread_data_ptr get_thread_info BOOST_PREVENT_MACRO_SUBSTITUTION () const;

#ifndef BOOST_NO_CXX11_RVALUE_REFERENCES
        template<typename F>
        static inline detail::thread_data_ptr make_thread_info(BOOST_THREAD_RV_REF(F) f)
        {
            return detail::thread_data_ptr(detail::heap_new<detail::thread_data<typename boost::remove_reference<F>::type> >(
                boost::forward<F>(f)));
        }
        static inline detail::thread_data_ptr make_thread_info(void (*f)())
        {
            return detail::thread_data_ptr(detail::heap_new<detail::thread_data<void(*)()> >(
                boost::forward<void(*)()>(f)));
        }
#else
        template<typename F>
        static inline detail::thread_data_ptr make_thread_info(F f)
        {
            return detail::thread_data_ptr(detail::heap_new<detail::thread_data<F> >(f));
        }
        template<typename F>
        static inline detail::thread_data_ptr make_thread_info(BOOST_THREAD_RV_REF(F) f)
        {
            return detail::thread_data_ptr(detail::heap_new<detail::thread_data<F> >(f));
        }

#endif
        struct dummy;
    public:
#if 0 // This should not be needed anymore. Use instead BOOST_THREAD_MAKE_RV_REF.
#if BOOST_WORKAROUND(__SUNPRO_CC, < 0x5100)
        thread(const volatile thread&);
#endif
#endif
        thread() BOOST_NOEXCEPT;
        ~thread()
        {
    #if defined BOOST_THREAD_PROVIDES_THREAD_DESTRUCTOR_CALLS_TERMINATE_IF_JOINABLE
          if (joinable()) {
            std::terminate();
          }
    #else
            detach();
    #endif
        }
#ifndef BOOST_NO_CXX11_RVALUE_REFERENCES
        template <
          class F
        >
        explicit thread(BOOST_THREAD_RV_REF(F) f
        , typename disable_if<is_same<typename decay<F>::type, thread>, dummy* >::type=0
        ):
          thread_info(make_thread_info(thread_detail::decay_copy(boost::forward<F>(f))))
        {
            start_thread();
        }
        template <
          class F
        >
        thread(attributes& attrs, BOOST_THREAD_RV_REF(F) f):
          thread_info(make_thread_info(thread_detail::decay_copy(boost::forward<F>(f))))
        {
            start_thread(attrs);
        }

#else
#ifdef BOOST_NO_SFINAE
        template <class F>
        explicit thread(F f):
            thread_info(make_thread_info(f))
        {
            start_thread();
        }
        template <class F>
        thread(attributes& attrs, F f):
            thread_info(make_thread_info(f))
        {
            start_thread(attrs);
        }
#else
        template <class F>
        explicit thread(F f
            // todo Disable also if Or is_same<typename decay<F>::type, thread>
        , typename disable_if<boost::is_convertible<F&,BOOST_THREAD_RV_REF(F) >, dummy* >::type=0):
            thread_info(make_thread_info(f))
        {
            start_thread();
        }
        template <class F>
        thread(attributes& attrs, F f
        , typename disable_if<boost::is_convertible<F&,BOOST_THREAD_RV_REF(F) >, dummy* >::type=0):
            thread_info(make_thread_info(f))
        {
            start_thread(attrs);
        }
#endif
        template <class F>
        explicit thread(BOOST_THREAD_RV_REF(F) f
        , typename disable_if<is_same<typename decay<F>::type, thread>, dummy* >::type=0
        ):
            thread_info(make_thread_info(f))
        {
            start_thread();
        }

        template <class F>
        thread(attributes& attrs, BOOST_THREAD_RV_REF(F) f):
            thread_info(make_thread_info(f))
        {
            start_thread(attrs);
        }
#endif
        thread(BOOST_THREAD_RV_REF(thread) x)
        {
            thread_info=BOOST_THREAD_RV(x).thread_info;
            BOOST_THREAD_RV(x).thread_info.reset();
        }
#if 0 // This should not be needed anymore. Use instead BOOST_THREAD_MAKE_RV_REF.
#if BOOST_WORKAROUND(__SUNPRO_CC, < 0x5100)
        thread& operator=(thread x)
        {
            swap(x);
            return *this;
        }
#endif
#endif

        thread& operator=(BOOST_THREAD_RV_REF(thread) other) BOOST_NOEXCEPT
        {

#if defined BOOST_THREAD_PROVIDES_THREAD_MOVE_ASSIGN_CALLS_TERMINATE_IF_JOINABLE
            if (joinable()) std::terminate();
#endif
            thread_info=BOOST_THREAD_RV(other).thread_info;
            BOOST_THREAD_RV(other).thread_info.reset();
            return *this;
        }

        template <class F,class A1>
        thread(F f,A1 a1,typename disable_if<boost::is_convertible<F&,thread_attributes >, dummy* >::type=0):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1)))
        {
            start_thread();
        }
        template <class F,class A1,class A2>
        thread(F f,A1 a1,A2 a2):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1,a2)))
        {
            start_thread();
        }

        template <class F,class A1,class A2,class A3>
        thread(F f,A1 a1,A2 a2,A3 a3):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1,a2,a3)))
        {
            start_thread();
        }

        template <class F,class A1,class A2,class A3,class A4>
        thread(F f,A1 a1,A2 a2,A3 a3,A4 a4):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1,a2,a3,a4)))
        {
            start_thread();
        }

        template <class F,class A1,class A2,class A3,class A4,class A5>
        thread(F f,A1 a1,A2 a2,A3 a3,A4 a4,A5 a5):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1,a2,a3,a4,a5)))
        {
            start_thread();
        }

        template <class F,class A1,class A2,class A3,class A4,class A5,class A6>
        thread(F f,A1 a1,A2 a2,A3 a3,A4 a4,A5 a5,A6 a6):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1,a2,a3,a4,a5,a6)))
        {
            start_thread();
        }

        template <class F,class A1,class A2,class A3,class A4,class A5,class A6,class A7>
        thread(F f,A1 a1,A2 a2,A3 a3,A4 a4,A5 a5,A6 a6,A7 a7):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1,a2,a3,a4,a5,a6,a7)))
        {
            start_thread();
        }

        template <class F,class A1,class A2,class A3,class A4,class A5,class A6,class A7,class A8>
        thread(F f,A1 a1,A2 a2,A3 a3,A4 a4,A5 a5,A6 a6,A7 a7,A8 a8):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1,a2,a3,a4,a5,a6,a7,a8)))
        {
            start_thread();
        }

        template <class F,class A1,class A2,class A3,class A4,class A5,class A6,class A7,class A8,class A9>
        thread(F f,A1 a1,A2 a2,A3 a3,A4 a4,A5 a5,A6 a6,A7 a7,A8 a8,A9 a9):
            thread_info(make_thread_info(boost::bind(boost::type<void>(),f,a1,a2,a3,a4,a5,a6,a7,a8,a9)))
        {
            start_thread();
        }

        void swap(thread& x) BOOST_NOEXCEPT
        {
            thread_info.swap(x.thread_info);
        }

        class BOOST_SYMBOL_VISIBLE id;
        id get_id() const BOOST_NOEXCEPT;


        bool joinable() const BOOST_NOEXCEPT;
        void join();
#ifdef BOOST_THREAD_USES_CHRONO
        template <class Rep, class Period>
        bool try_join_for(const chrono::duration<Rep, Period>& rel_time)
        {
          return try_join_until(chrono::steady_clock::now() + rel_time);
        }
        template <class Clock, class Duration>
        bool try_join_until(const chrono::time_point<Clock, Duration>& t)
        {
          using namespace chrono;
          system_clock::time_point     s_now = system_clock::now();
          typename Clock::time_point  c_now = Clock::now();
          return try_join_until(s_now + ceil<nanoseconds>(t - c_now));
        }
        template <class Duration>
        bool try_join_until(const chrono::time_point<chrono::system_clock, Duration>& t)
        {
          using namespace chrono;
          typedef time_point<system_clock, nanoseconds> nano_sys_tmpt;
          return try_join_until(nano_sys_tmpt(ceil<nanoseconds>(t.time_since_epoch())));
        }
#endif
#if defined(BOOST_THREAD_PLATFORM_WIN32)
        bool timed_join(const system_time& abs_time);
    private:
        bool do_try_join_until(uintmax_t milli);
    public:
#ifdef BOOST_THREAD_USES_CHRONO
        bool try_join_until(const chrono::time_point<chrono::system_clock, chrono::nanoseconds>& tp)
        {
          chrono::milliseconds rel_time= chrono::ceil<chrono::milliseconds>(tp-chrono::system_clock::now());
          return do_try_join_until(rel_time.count());
        }
#endif


#else
        bool timed_join(const system_time& abs_time)
        {
          struct timespec const ts=detail::get_timespec(abs_time);
          return do_try_join_until(ts);
        }
#ifdef BOOST_THREAD_USES_CHRONO
        bool try_join_until(const chrono::time_point<chrono::system_clock, chrono::nanoseconds>& tp)
        {
          using namespace chrono;
          nanoseconds d = tp.time_since_epoch();
          timespec ts;
          seconds s = duration_cast<seconds>(d);
          ts.tv_sec = static_cast<long>(s.count());
          ts.tv_nsec = static_cast<long>((d - s).count());
          return do_try_join_until(ts);
        }
#endif
      private:
        bool do_try_join_until(struct timespec const &timeout);
      public:

#endif

        template<typename TimeDuration>
        inline bool timed_join(TimeDuration const& rel_time)
        {
            return timed_join(get_system_time()+rel_time);
        }

        void detach();

        static unsigned hardware_concurrency() BOOST_NOEXCEPT;

#define BOOST_THREAD_DEFINES_THREAD_NATIVE_HANDLE
        typedef detail::thread_data_base::native_handle_type native_handle_type;
        native_handle_type native_handle();

#if defined BOOST_THREAD_PROVIDES_DEPRECATED_FEATURES_SINCE_V3_0_0
        // Use thread::id when comparisions are needed
        // backwards compatibility
        bool operator==(const thread& other) const;
        bool operator!=(const thread& other) const;
#endif
        static inline void yield() BOOST_NOEXCEPT
        {
            this_thread::yield();
        }

        static inline void sleep(const system_time& xt)
        {
            this_thread::sleep(xt);
        }

        // extensions
        void interrupt();
        bool interruption_requested() const BOOST_NOEXCEPT;
    };

    inline void swap(thread& lhs,thread& rhs) BOOST_NOEXCEPT
    {
        return lhs.swap(rhs);
    }

#ifndef BOOST_NO_CXX11_RVALUE_REFERENCES
    inline thread&& move(thread& t) BOOST_NOEXCEPT
    {
        return static_cast<thread&&>(t);
    }
#endif

    BOOST_THREAD_DCL_MOVABLE(thread)

    namespace this_thread
    {
        thread::id BOOST_THREAD_DECL get_id() BOOST_NOEXCEPT;

        void BOOST_THREAD_DECL interruption_point();
        bool BOOST_THREAD_DECL interruption_enabled() BOOST_NOEXCEPT;
        bool BOOST_THREAD_DECL interruption_requested() BOOST_NOEXCEPT;

        inline BOOST_SYMBOL_VISIBLE void sleep(xtime const& abs_time)
        {
            sleep(system_time(abs_time));
        }
    }

    class BOOST_SYMBOL_VISIBLE thread::id
    {
    private:
        friend inline
        std::size_t
        hash_value(const thread::id &v)
        {
#if defined BOOST_THREAD_PROVIDES_BASIC_THREAD_ID
          return hash_value(v.thread_data);
#else
          return hash_value(v.thread_data.get());
#endif
        }

#if defined BOOST_THREAD_PROVIDES_BASIC_THREAD_ID
#if defined(BOOST_THREAD_PLATFORM_WIN32)
        typedef unsigned int data;
#else
        typedef thread::native_handle_type data;
#endif
#else
        typedef detail::thread_data_ptr data;
#endif
        data thread_data;

        id(data thread_data_):
            thread_data(thread_data_)
        {}
        friend class thread;
        friend id BOOST_THREAD_DECL this_thread::get_id() BOOST_NOEXCEPT;
    public:
        id() BOOST_NOEXCEPT:
#if defined BOOST_THREAD_PROVIDES_BASIC_THREAD_ID
#if defined(BOOST_THREAD_PLATFORM_WIN32)
        thread_data(0)
#else
        thread_data(0)
#endif
#else
        thread_data()
#endif
        {}

        id(const id& other) BOOST_NOEXCEPT :
            thread_data(other.thread_data)
        {}

        bool operator==(const id& y) const BOOST_NOEXCEPT
        {
            return thread_data==y.thread_data;
        }

        bool operator!=(const id& y) const BOOST_NOEXCEPT
        {
            return thread_data!=y.thread_data;
        }

        bool operator<(const id& y) const BOOST_NOEXCEPT
        {
            return thread_data<y.thread_data;
        }

        bool operator>(const id& y) const BOOST_NOEXCEPT
        {
            return y.thread_data<thread_data;
        }

        bool operator<=(const id& y) const BOOST_NOEXCEPT
        {
            return !(y.thread_data<thread_data);
        }

        bool operator>=(const id& y) const BOOST_NOEXCEPT
        {
            return !(thread_data<y.thread_data);
        }

#ifndef BOOST_NO_IOSTREAM
#ifndef BOOST_NO_MEMBER_TEMPLATE_FRIENDS
        template<class charT, class traits>
        friend BOOST_SYMBOL_VISIBLE
  std::basic_ostream<charT, traits>&
        operator<<(std::basic_ostream<charT, traits>& os, const id& x)
        {
            if(x.thread_data)
            {
                io::ios_flags_saver  ifs( os );
                return os<< std::hex << x.thread_data;
            }
            else
            {
                return os<<"{Not-any-thread}";
            }
        }
#else
        template<class charT, class traits>
        BOOST_SYMBOL_VISIBLE
  std::basic_ostream<charT, traits>&
        print(std::basic_ostream<charT, traits>& os) const
        {
            if(thread_data)
            {
              io::ios_flags_saver  ifs( os );
              return os<< std::hex << thread_data;
            }
            else
            {
                return os<<"{Not-any-thread}";
            }
        }

#endif
#endif
    };

#if !defined(BOOST_NO_IOSTREAM) && defined(BOOST_NO_MEMBER_TEMPLATE_FRIENDS)
    template<class charT, class traits>
    BOOST_SYMBOL_VISIBLE
    std::basic_ostream<charT, traits>&
    operator<<(std::basic_ostream<charT, traits>& os, const thread::id& x)
    {
        return x.print(os);
    }
#endif

#if defined BOOST_THREAD_PROVIDES_DEPRECATED_FEATURES_SINCE_V3_0_0
    inline bool thread::operator==(const thread& other) const
    {
        return get_id()==other.get_id();
    }

    inline bool thread::operator!=(const thread& other) const
    {
        return get_id()!=other.get_id();
    }
#endif

    namespace detail
    {
        struct thread_exit_function_base
        {
            virtual ~thread_exit_function_base()
            {}
            virtual void operator()()=0;
        };

        template<typename F>
        struct thread_exit_function:
            thread_exit_function_base
        {
            F f;

            thread_exit_function(F f_):
                f(f_)
            {}

            void operator()()
            {
                f();
            }
        };

        void BOOST_THREAD_DECL add_thread_exit_function(thread_exit_function_base*);
    }

    namespace this_thread
    {
        template<typename F>
        void at_thread_exit(F f)
        {
            detail::thread_exit_function_base* const thread_exit_func=detail::heap_new<detail::thread_exit_function<F> >(f);
            detail::add_thread_exit_function(thread_exit_func);
        }
    }
}

#ifdef BOOST_MSVC
#pragma warning(pop)
#endif

#include <boost/config/abi_suffix.hpp>

#endif
