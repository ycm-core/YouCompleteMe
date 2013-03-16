//////////////////////////////////////////////////////////////////////////////
//
// (C) Copyright Ion Gaztanaga 2005-2012. Distributed under the Boost
// Software License, Version 1.0. (See accompanying file
// LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// See http://www.boost.org/libs/interprocess for documentation.
//
//////////////////////////////////////////////////////////////////////////////

#ifndef BOOST_INTERPROCESS_DETAIL_OS_THREAD_FUNCTIONS_HPP
#define BOOST_INTERPROCESS_DETAIL_OS_THREAD_FUNCTIONS_HPP

#include <boost/interprocess/detail/config_begin.hpp>
#include <boost/interprocess/detail/workaround.hpp>
#include <boost/interprocess/streams/bufferstream.hpp>
#include <boost/interprocess/detail/posix_time_types_wrk.hpp>

#if (defined BOOST_INTERPROCESS_WINDOWS)
#  include <boost/interprocess/detail/win32_api.hpp>
#else
#  ifdef BOOST_HAS_UNISTD_H
#     include <pthread.h>
#     include <unistd.h>
#     include <sched.h>
#     include <time.h>
#  else
#     error Unknown platform
#  endif
#endif

namespace boost {
namespace interprocess {
namespace ipcdetail{

#if (defined BOOST_INTERPROCESS_WINDOWS)

typedef unsigned long OS_process_id_t;
typedef unsigned long OS_thread_id_t;
typedef OS_thread_id_t OS_systemwide_thread_id_t;

//process
inline OS_process_id_t get_current_process_id()
{  return winapi::get_current_process_id();  }

inline OS_process_id_t get_invalid_process_id()
{  return OS_process_id_t(0);  }

//thread
inline OS_thread_id_t get_current_thread_id()
{  return winapi::get_current_thread_id();  }

inline OS_thread_id_t get_invalid_thread_id()
{  return OS_thread_id_t(0xffffffff);  }

inline bool equal_thread_id(OS_thread_id_t id1, OS_thread_id_t id2)
{  return id1 == id2;  }

inline void thread_yield()
{  winapi::sched_yield();  }

inline void thread_sleep(unsigned int ms)
{  winapi::Sleep(ms);  }

//systemwide thread
inline OS_systemwide_thread_id_t get_current_systemwide_thread_id()
{
   return get_current_thread_id();
}

inline void systemwide_thread_id_copy
   (const volatile OS_systemwide_thread_id_t &from, volatile OS_systemwide_thread_id_t &to)
{
   to = from;
}

inline bool equal_systemwide_thread_id(const OS_systemwide_thread_id_t &id1, const OS_systemwide_thread_id_t &id2)
{
   return equal_thread_id(id1, id2);
}

inline OS_systemwide_thread_id_t get_invalid_systemwide_thread_id()
{
   return get_invalid_thread_id();
}

inline long double get_current_process_creation_time()
{
   winapi::interprocess_filetime CreationTime, ExitTime, KernelTime, UserTime;

   get_process_times
      ( winapi::get_current_process(), &CreationTime, &ExitTime, &KernelTime, &UserTime);

   typedef long double ldouble_t;
   const ldouble_t resolution = (100.0l/1000000000.0l);
   return CreationTime.dwHighDateTime*(ldouble_t(1u<<31u)*2.0l*resolution) +
              CreationTime.dwLowDateTime*resolution;
}


#else    //#if (defined BOOST_INTERPROCESS_WINDOWS)

typedef pthread_t OS_thread_id_t;
typedef pid_t     OS_process_id_t;

struct OS_systemwide_thread_id_t
{
   OS_systemwide_thread_id_t()
      :  pid(), tid()
   {}

   OS_systemwide_thread_id_t(pid_t p, pthread_t t)
      :  pid(p), tid(t)
   {}

   OS_systemwide_thread_id_t(const OS_systemwide_thread_id_t &x)
      :  pid(x.pid), tid(x.tid)
   {}

   OS_systemwide_thread_id_t(const volatile OS_systemwide_thread_id_t &x)
      :  pid(x.pid), tid(x.tid)
   {}

   OS_systemwide_thread_id_t & operator=(const OS_systemwide_thread_id_t &x)
   {  pid = x.pid;   tid = x.tid;   return *this;   }

   OS_systemwide_thread_id_t & operator=(const volatile OS_systemwide_thread_id_t &x)
   {  pid = x.pid;   tid = x.tid;   return *this;  }

   void operator=(const OS_systemwide_thread_id_t &x) volatile
   {  pid = x.pid;   tid = x.tid;   }

   pid_t       pid;
   pthread_t   tid;
};

inline void systemwide_thread_id_copy
   (const volatile OS_systemwide_thread_id_t &from, volatile OS_systemwide_thread_id_t &to)
{
   to.pid = from.pid;
   to.tid = from.tid;
}

//process
inline OS_process_id_t get_current_process_id()
{  return ::getpid();  }

inline OS_process_id_t get_invalid_process_id()
{  return pid_t(0);  }

//thread
inline OS_thread_id_t get_current_thread_id()
{  return ::pthread_self();  }

inline OS_thread_id_t get_invalid_thread_id()
{
   static pthread_t invalid_id;
   return invalid_id;
}

inline bool equal_thread_id(OS_thread_id_t id1, OS_thread_id_t id2)
{  return 0 != pthread_equal(id1, id2);  }

inline void thread_yield()
{  ::sched_yield();  }

inline void thread_sleep(unsigned int ms)
{
   const struct timespec rqt = { ms/1000u, (ms%1000u)*1000000u  };
   ::nanosleep(&rqt, 0);
}

//systemwide thread
inline OS_systemwide_thread_id_t get_current_systemwide_thread_id()
{
   return OS_systemwide_thread_id_t(::getpid(), ::pthread_self());
}

inline bool equal_systemwide_thread_id(const OS_systemwide_thread_id_t &id1, const OS_systemwide_thread_id_t &id2)
{
   return (0 != pthread_equal(id1.tid, id2.tid)) && (id1.pid == id2.pid);
}

inline OS_systemwide_thread_id_t get_invalid_systemwide_thread_id()
{
   return OS_systemwide_thread_id_t(get_invalid_process_id(), get_invalid_thread_id());
}

inline long double get_current_process_creation_time()
{ return 0.0L; }

#endif   //#if (defined BOOST_INTERPROCESS_WINDOWS)

typedef char pid_str_t[sizeof(OS_process_id_t)*3+1];

inline void get_pid_str(pid_str_t &pid_str, OS_process_id_t pid)
{
   bufferstream bstream(pid_str, sizeof(pid_str));
   bstream << pid << std::ends;
}

inline void get_pid_str(pid_str_t &pid_str)
{  get_pid_str(pid_str, get_current_process_id());  }

}  //namespace ipcdetail{
}  //namespace interprocess {
}  //namespace boost {

#include <boost/interprocess/detail/config_end.hpp>

#endif   //BOOST_INTERPROCESS_DETAIL_OS_THREAD_FUNCTIONS_HPP
