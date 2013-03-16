#ifndef BOOST_ATOMIC_DETAIL_LOCKPOOL_HPP
#define BOOST_ATOMIC_DETAIL_LOCKPOOL_HPP

//  Copyright (c) 2011 Helge Bahmann
//
//  Distributed under the Boost Software License, Version 1.0.
//  See accompanying file LICENSE_1_0.txt or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

#include <boost/atomic/detail/config.hpp>
#ifndef BOOST_ATOMIC_FLAG_LOCK_FREE
#include <boost/thread/mutex.hpp>
#endif

#ifdef BOOST_ATOMIC_HAS_PRAGMA_ONCE
#pragma once
#endif

namespace boost {
namespace atomics {
namespace detail {

#ifndef BOOST_ATOMIC_FLAG_LOCK_FREE

class lockpool
{
public:
    typedef mutex lock_type;
    class scoped_lock
    {
    private:
        lock_type& mtx_;

        scoped_lock(scoped_lock const&) /* = delete */;
        scoped_lock& operator=(scoped_lock const&) /* = delete */;

    public:
        explicit
        scoped_lock(const volatile void * addr) : mtx_(get_lock_for(addr))
        {
            mtx_.lock();
        }
        ~scoped_lock()
        {
            mtx_.unlock();
        }
    };

private:
    static BOOST_ATOMIC_DECL lock_type& get_lock_for(const volatile void * addr);
};

#else

class lockpool
{
public:
    typedef atomic_flag lock_type;

    class scoped_lock
    {
    private:
        atomic_flag& flag_;

        scoped_lock(const scoped_lock &) /* = delete */;
        scoped_lock& operator=(const scoped_lock &) /* = delete */;

    public:
        explicit
        scoped_lock(const volatile void * addr) : flag_(get_lock_for(addr))
        {
            for (; flag_.test_and_set(memory_order_acquire);)
            {
#if defined(BOOST_ATOMIC_X86_PAUSE)
                BOOST_ATOMIC_X86_PAUSE();
#endif
            }
        }

        ~scoped_lock(void)
        {
            flag_.clear(memory_order_release);
        }
    };

private:
    static BOOST_ATOMIC_DECL lock_type& get_lock_for(const volatile void * addr);
};

#endif

}
}
}

#endif
