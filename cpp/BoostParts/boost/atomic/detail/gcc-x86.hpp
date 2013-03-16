#ifndef BOOST_ATOMIC_DETAIL_GCC_X86_HPP
#define BOOST_ATOMIC_DETAIL_GCC_X86_HPP

//  Copyright (c) 2009 Helge Bahmann
//  Copyright (c) 2012 Tim Blechmann
//
//  Distributed under the Boost Software License, Version 1.0.
//  See accompanying file LICENSE_1_0.txt or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

#include <cstddef>
#include <boost/cstdint.hpp>
#include <boost/atomic/detail/config.hpp>

#ifdef BOOST_ATOMIC_HAS_PRAGMA_ONCE
#pragma once
#endif

namespace boost {
namespace atomics {
namespace detail {

#if defined(__x86_64__) || defined(__SSE2__)
# define BOOST_ATOMIC_X86_FENCE_INSTR "mfence\n"
#else
# define BOOST_ATOMIC_X86_FENCE_INSTR "lock ; addl $0, (%%esp)\n"
#endif

#define BOOST_ATOMIC_X86_PAUSE() __asm__ __volatile__ ("pause\n")

inline void
platform_fence_before(memory_order order)
{
    switch(order)
    {
    case memory_order_relaxed:
    case memory_order_acquire:
    case memory_order_consume:
        break;
    case memory_order_release:
    case memory_order_acq_rel:
        __asm__ __volatile__ ("" ::: "memory");
        /* release */
        break;
    case memory_order_seq_cst:
        __asm__ __volatile__ ("" ::: "memory");
        /* seq */
        break;
    default:;
    }
}

inline void
platform_fence_after(memory_order order)
{
    switch(order)
    {
    case memory_order_relaxed:
    case memory_order_release:
        break;
    case memory_order_acquire:
    case memory_order_acq_rel:
        __asm__ __volatile__ ("" ::: "memory");
        /* acquire */
        break;
    case memory_order_consume:
        /* consume */
        break;
    case memory_order_seq_cst:
        __asm__ __volatile__ ("" ::: "memory");
        /* seq */
        break;
    default:;
    }
}

inline void
platform_fence_after_load(memory_order order)
{
    switch(order)
    {
    case memory_order_relaxed:
    case memory_order_release:
        break;
    case memory_order_acquire:
    case memory_order_acq_rel:
        __asm__ __volatile__ ("" ::: "memory");
        break;
    case memory_order_consume:
        break;
    case memory_order_seq_cst:
        __asm__ __volatile__ ("" ::: "memory");
        break;
    default:;
    }
}

inline void
platform_fence_before_store(memory_order order)
{
    switch(order)
    {
    case memory_order_relaxed:
    case memory_order_acquire:
    case memory_order_consume:
        break;
    case memory_order_release:
    case memory_order_acq_rel:
        __asm__ __volatile__ ("" ::: "memory");
        /* release */
        break;
    case memory_order_seq_cst:
        __asm__ __volatile__ ("" ::: "memory");
        /* seq */
        break;
    default:;
    }
}

inline void
platform_fence_after_store(memory_order order)
{
    switch(order)
    {
    case memory_order_relaxed:
    case memory_order_release:
        break;
    case memory_order_acquire:
    case memory_order_acq_rel:
        __asm__ __volatile__ ("" ::: "memory");
        /* acquire */
        break;
    case memory_order_consume:
        /* consume */
        break;
    case memory_order_seq_cst:
        __asm__ __volatile__ ("" ::: "memory");
        /* seq */
        break;
    default:;
    }
}

}
}

class atomic_flag
{
private:
    atomic_flag(const atomic_flag &) /* = delete */ ;
    atomic_flag & operator=(const atomic_flag &) /* = delete */ ;
    uint32_t v_;
public:
    atomic_flag(void) : v_(0) {}

    bool
    test_and_set(memory_order order = memory_order_seq_cst) volatile
    {
        uint32_t v = 1;
        atomics::detail::platform_fence_before(order);
        __asm__ __volatile__ (
            "xchgl %0, %1"
            : "+r" (v), "+m" (v_)
        );
        atomics::detail::platform_fence_after(order);
        return v;
    }

    void
    clear(memory_order order = memory_order_seq_cst) volatile
    {
        if (order == memory_order_seq_cst) {
            uint32_t v = 0;
            __asm__ __volatile__ (
                "xchgl %0, %1"
                : "+r" (v), "+m" (v_)
            );
        } else {
            atomics::detail::platform_fence_before(order);
            v_ = 0;
        }
    }
};

} /* namespace boost */

#define BOOST_ATOMIC_FLAG_LOCK_FREE 2

#include <boost/atomic/detail/base.hpp>

#if !defined(BOOST_ATOMIC_FORCE_FALLBACK)

#define BOOST_ATOMIC_CHAR_LOCK_FREE 2
#define BOOST_ATOMIC_CHAR16_T_LOCK_FREE 2
#define BOOST_ATOMIC_CHAR32_T_LOCK_FREE 2
#define BOOST_ATOMIC_WCHAR_T_LOCK_FREE 2
#define BOOST_ATOMIC_SHORT_LOCK_FREE 2
#define BOOST_ATOMIC_INT_LOCK_FREE 2
#define BOOST_ATOMIC_LONG_LOCK_FREE 2

#if defined(__x86_64__)
#define BOOST_ATOMIC_LLONG_LOCK_FREE 2
#else
#define BOOST_ATOMIC_LLONG_LOCK_FREE 1
#endif

#define BOOST_ATOMIC_POINTER_LOCK_FREE 2
#define BOOST_ATOMIC_BOOL_LOCK_FREE 2

namespace boost {

#define BOOST_ATOMIC_THREAD_FENCE 2
inline void
atomic_thread_fence(memory_order order)
{
    switch(order)
    {
    case memory_order_relaxed:
        break;
    case memory_order_release:
        __asm__ __volatile__ ("" ::: "memory");
        break;
    case memory_order_acquire:
        __asm__ __volatile__ ("" ::: "memory");
        break;
    case memory_order_acq_rel:
        __asm__ __volatile__ ("" ::: "memory");
        break;
    case memory_order_consume:
        break;
    case memory_order_seq_cst:
        __asm__ __volatile__ (BOOST_ATOMIC_X86_FENCE_INSTR ::: "memory");
        break;
    default:;
    }
}

#define BOOST_ATOMIC_SIGNAL_FENCE 2
inline void
atomic_signal_fence(memory_order)
{
    __asm__ __volatile__ ("" ::: "memory");
}

namespace atomics {
namespace detail {

template<typename T, bool Sign>
class base_atomic<T, int, 1, Sign> {
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "lock ; xaddb %0, %1"
            : "+q" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    value_type
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        return fetch_add(-v, order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "xchgb %0, %1"
            : "+q" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgb %2, %1"
            : "+a" (previous), "+m" (v_)
            : "q" (desired)
        );
        bool success = (previous == expected);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = previous;
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_and(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for(; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_INTEGRAL_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

template<typename T, bool Sign>
class base_atomic<T, int, 2, Sign> {
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "lock ; xaddw %0, %1"
            : "+q" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    value_type
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        return fetch_add(-v, order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "xchgw %0, %1"
            : "+q" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgw %2, %1"
            : "+a" (previous), "+m" (v_)
            : "q" (desired)
        );
        bool success = (previous == expected);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = previous;
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_and(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_INTEGRAL_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

template<typename T, bool Sign>
class base_atomic<T, int, 4, Sign> {
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "lock ; xaddl %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    value_type
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        return fetch_add(-v, order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "xchgl %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgl %2, %1"
            : "+a" (previous), "+m" (v_)
            : "r" (desired)
        );
        bool success = (previous == expected);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = previous;
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_and(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_INTEGRAL_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

#if defined(__x86_64__)
template<typename T, bool Sign>
class base_atomic<T, int, 8, Sign> {
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "lock ; xaddq %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    value_type
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        return fetch_add(-v, order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "xchgq %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgq %2, %1"
            : "+a" (previous), "+m" (v_)
            : "r" (desired)
        );
        bool success = (previous == expected);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = previous;
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_and(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_INTEGRAL_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

#endif

/* pointers */

#if !defined(__x86_64__)

template<bool Sign>
class base_atomic<void *, void *, 4, Sign> {
    typedef base_atomic this_type;
    typedef void * value_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "xchgl %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    bool compare_exchange_strong(value_type & expected, value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgl %2, %1"
            : "+a" (previous), "+m" (v_)
            : "r" (desired)
        );
        bool success = (previous == expected);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = previous;
        return success;
    }

    bool compare_exchange_weak(value_type & expected, value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_BASE_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

template<typename T, bool Sign>
class base_atomic<T *, void *, 4, Sign> {
    typedef base_atomic this_type;
    typedef T * value_type;
    typedef ptrdiff_t difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "xchgl %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgl %2, %1"
            : "+a" (previous), "+m" (v_)
            : "r" (desired)
        );
        bool success = (previous == expected);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = previous;
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_add(difference_type v, memory_order order = memory_order_seq_cst) volatile
    {
        v = v * sizeof(*v_);
        platform_fence_before(order);
        __asm__ (
            "lock ; xaddl %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return reinterpret_cast<value_type>(v);
    }

    value_type
    fetch_sub(difference_type v, memory_order order = memory_order_seq_cst) volatile
    {
        return fetch_add(-v, order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_POINTER_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

#else

template<bool Sign>
class base_atomic<void *, void *, 8, Sign> {
    typedef base_atomic this_type;
    typedef void * value_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "xchgq %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    bool compare_exchange_strong(value_type & expected, value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgq %2, %1"
            : "+a" (previous), "+m" (v_)
            : "r" (desired)
        );
        bool success = (previous == expected);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = previous;
        return success;
    }

    bool compare_exchange_weak(value_type & expected, value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_BASE_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

template<typename T, bool Sign>
class base_atomic<T *, void *, 8, Sign> {
    typedef base_atomic this_type;
    typedef T * value_type;
    typedef ptrdiff_t difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        __asm__ (
            "xchgq %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return v;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgq %2, %1"
            : "+a" (previous), "+m" (v_)
            : "r" (desired)
        );
        bool success = (previous == expected);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = previous;
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_add(difference_type v, memory_order order = memory_order_seq_cst) volatile
    {
        v = v * sizeof(*v_);
        platform_fence_before(order);
        __asm__ (
            "lock ; xaddq %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return reinterpret_cast<value_type>(v);
    }

    value_type
    fetch_sub(difference_type v, memory_order order = memory_order_seq_cst) volatile
    {
        return fetch_add(-v, order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_POINTER_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

#endif

template<typename T, bool Sign>
class base_atomic<T, void, 1, Sign> {
    typedef base_atomic this_type;
    typedef T value_type;
    typedef uint8_t storage_type;
public:
    explicit base_atomic(value_type const& v)
    {
        memcpy(&v_, &v, sizeof(value_type));
    }
    base_atomic(void) {}

    void
    store(value_type const& v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            storage_type tmp;
            memcpy(&tmp, &v, sizeof(value_type));
            platform_fence_before(order);
            const_cast<volatile storage_type &>(v_) = tmp;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        storage_type tmp = const_cast<volatile storage_type &>(v_);
        platform_fence_after_load(order);
        value_type v;
        memcpy(&v, &tmp, sizeof(value_type));
        return v;
    }

    value_type
    exchange(value_type const& v, memory_order order = memory_order_seq_cst) volatile
    {
        storage_type tmp;
        memcpy(&tmp, &v, sizeof(value_type));
        platform_fence_before(order);
        __asm__ (
            "xchgb %0, %1"
            : "+q" (tmp), "+m" (v_)
        );
        platform_fence_after(order);
        value_type res;
        memcpy(&res, &tmp, sizeof(value_type));
        return res;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type const& desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        storage_type expected_s, desired_s;
        memcpy(&expected_s, &expected, sizeof(value_type));
        memcpy(&desired_s, &desired, sizeof(value_type));
        storage_type previous_s = expected_s;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgb %2, %1"
            : "+a" (previous_s), "+m" (v_)
            : "q" (desired_s)
        );
        bool success = (previous_s == expected_s);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        memcpy(&expected, &previous_s, sizeof(value_type));
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type const& desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_BASE_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    storage_type v_;
};

template<typename T, bool Sign>
class base_atomic<T, void, 2, Sign> {
    typedef base_atomic this_type;
    typedef T value_type;
    typedef uint16_t storage_type;
public:
    explicit base_atomic(value_type const& v)
    {
        memcpy(&v_, &v, sizeof(value_type));
    }
    base_atomic(void) {}

    void
    store(value_type const& v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            storage_type tmp;
            memcpy(&tmp, &v, sizeof(value_type));
            platform_fence_before(order);
            const_cast<volatile storage_type &>(v_) = tmp;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        storage_type tmp = const_cast<volatile storage_type &>(v_);
        platform_fence_after_load(order);
        value_type v;
        memcpy(&v, &tmp, sizeof(value_type));
        return v;
    }

    value_type
    exchange(value_type const& v, memory_order order = memory_order_seq_cst) volatile
    {
        storage_type tmp;
        memcpy(&tmp, &v, sizeof(value_type));
        platform_fence_before(order);
        __asm__ (
            "xchgw %0, %1"
            : "+q" (tmp), "+m" (v_)
        );
        platform_fence_after(order);
        value_type res;
        memcpy(&res, &tmp, sizeof(value_type));
        return res;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type const& desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        storage_type expected_s, desired_s;
        memcpy(&expected_s, &expected, sizeof(value_type));
        memcpy(&desired_s, &desired, sizeof(value_type));
        storage_type previous_s = expected_s;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgw %2, %1"
            : "+a" (previous_s), "+m" (v_)
            : "q" (desired_s)
        );
        bool success = (previous_s == expected_s);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        memcpy(&expected, &previous_s, sizeof(value_type));
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type const& desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_BASE_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    storage_type v_;
};

template<typename T, bool Sign>
class base_atomic<T, void, 4, Sign> {
    typedef base_atomic this_type;
    typedef T value_type;
    typedef uint32_t storage_type;
public:
    explicit base_atomic(value_type const& v) : v_(0)
    {
        memcpy(&v_, &v, sizeof(value_type));
    }
    base_atomic(void) {}

    void
    store(value_type const& v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            storage_type tmp = 0;
            memcpy(&tmp, &v, sizeof(value_type));
            platform_fence_before(order);
            const_cast<volatile storage_type &>(v_) = tmp;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        storage_type tmp = const_cast<volatile storage_type &>(v_);
        platform_fence_after_load(order);
        value_type v;
        memcpy(&v, &tmp, sizeof(value_type));
        return v;
    }

    value_type
    exchange(value_type const& v, memory_order order = memory_order_seq_cst) volatile
    {
        storage_type tmp = 0;
        memcpy(&tmp, &v, sizeof(value_type));
        platform_fence_before(order);
        __asm__ (
            "xchgl %0, %1"
            : "+q" (tmp), "+m" (v_)
        );
        platform_fence_after(order);
        value_type res;
        memcpy(&res, &tmp, sizeof(value_type));
        return res;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type const& desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        storage_type expected_s = 0, desired_s = 0;
        memcpy(&expected_s, &expected, sizeof(value_type));
        memcpy(&desired_s, &desired, sizeof(value_type));
        storage_type previous_s = expected_s;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgl %2, %1"
            : "+a" (previous_s), "+m" (v_)
            : "q" (desired_s)
        );
        bool success = (previous_s == expected_s);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        memcpy(&expected, &previous_s, sizeof(value_type));
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type const& desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_BASE_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    storage_type v_;
};

#if defined(__x86_64__)
template<typename T, bool Sign>
class base_atomic<T, void, 8, Sign> {
    typedef base_atomic this_type;
    typedef T value_type;
    typedef uint64_t storage_type;
public:
    explicit base_atomic(value_type const& v) : v_(0)
    {
        memcpy(&v_, &v, sizeof(value_type));
    }
    base_atomic(void) {}

    void
    store(value_type const& v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            storage_type tmp = 0;
            memcpy(&tmp, &v, sizeof(value_type));
            platform_fence_before(order);
            const_cast<volatile storage_type &>(v_) = tmp;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        storage_type tmp = const_cast<volatile storage_type &>(v_);
        platform_fence_after_load(order);
        value_type v;
        memcpy(&v, &tmp, sizeof(value_type));
        return v;
    }

    value_type
    exchange(value_type const& v, memory_order order = memory_order_seq_cst) volatile
    {
        storage_type tmp = 0;
        memcpy(&tmp, &v, sizeof(value_type));
        platform_fence_before(order);
        __asm__ (
            "xchgq %0, %1"
            : "+q" (tmp), "+m" (v_)
        );
        platform_fence_after(order);
        value_type res;
        memcpy(&res, &tmp, sizeof(value_type));
        return res;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type const& desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        storage_type expected_s = 0, desired_s = 0;
        memcpy(&expected_s, &expected, sizeof(value_type));
        memcpy(&desired_s, &desired, sizeof(value_type));
        storage_type previous_s = expected_s;
        platform_fence_before(success_order);
        __asm__ (
            "lock ; cmpxchgq %2, %1"
            : "+a" (previous_s), "+m" (v_)
            : "q" (desired_s)
        );
        bool success = (previous_s == expected_s);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        memcpy(&expected, &previous_s, sizeof(value_type));
        return success;
    }

    bool
    compare_exchange_weak(
        value_type & expected,
        value_type const& desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return true;
    }

    BOOST_ATOMIC_DECLARE_BASE_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    storage_type v_;
};
#endif

#if !defined(__x86_64__) && (defined(__i686__) || defined (__GCC_HAVE_SYNC_COMPARE_AND_SWAP_8))

template<typename T>
inline bool
platform_cmpxchg64_strong(T & expected, T desired, volatile T * ptr)
{
#ifdef __GCC_HAVE_SYNC_COMPARE_AND_SWAP_8
    const T oldval = __sync_val_compare_and_swap(ptr, expected, desired);
    const bool result = (oldval == expected);
    expected = oldval;
    return result;
#else
    int scratch;
    T prev = expected;
    /* Make sure ebx is saved and restored properly in case
    this object is compiled as "position independent". Since
    programmers on x86 tend to forget specifying -DPIC or
    similar, always assume PIC.

    To make this work uniformly even in the non-PIC case,
    setup register constraints such that ebx can not be
    used by accident e.g. as base address for the variable
    to be modified. Accessing "scratch" should always be okay,
    as it can only be placed on the stack (and therefore
    accessed through ebp or esp only).

    In theory, could push/pop ebx onto/off the stack, but movs
    to a prepared stack slot turn out to be faster. */
    __asm__ __volatile__ (
        "movl %%ebx, %1\n"
        "movl %2, %%ebx\n"
        "lock; cmpxchg8b 0(%4)\n"
        "movl %1, %%ebx\n"
        : "=A" (prev), "=m" (scratch)
        : "D" ((int)desired), "c" ((int)(desired >> 32)), "S" (ptr), "0" (prev)
        : "memory");
    bool success = (prev == expected);
    expected = prev;
    return success;
#endif
}

template<typename T>
inline void
platform_store64(T value, volatile T * ptr)
{
    T expected = *ptr;
    for (; !platform_cmpxchg64_strong(expected, value, ptr);)
    {
        BOOST_ATOMIC_X86_PAUSE();
    }
}

template<typename T>
inline T
platform_load64(const volatile T * ptr)
{
    T expected = *ptr;
    for (; !platform_cmpxchg64_strong(expected, expected, const_cast<volatile T*>(ptr));)
    {
        BOOST_ATOMIC_X86_PAUSE();
    }
    return expected;
}

#endif

}
}
}

/* pull in 64-bit atomic type using cmpxchg8b above */
#if !defined(__x86_64__) && (defined(__i686__) || defined (__GCC_HAVE_SYNC_COMPARE_AND_SWAP_8))
#include <boost/atomic/detail/cas64strong.hpp>
#endif

#endif /* !defined(BOOST_ATOMIC_FORCE_FALLBACK) */

#endif
