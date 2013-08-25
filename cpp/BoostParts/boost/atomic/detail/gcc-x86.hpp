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

#if defined(__i386__) &&\
    (\
        defined(__GCC_HAVE_SYNC_COMPARE_AND_SWAP_8) ||\
        defined(__i586__) || defined(__i686__) || defined(__pentium4__) || defined(__nocona__) || defined(__core2__) || defined(__corei7__) ||\
        defined(__k6__) || defined(__athlon__) || defined(__k8__) || defined(__amdfam10__) || defined(__bdver1__) || defined(__bdver2__) || defined(__bdver3__) || defined(__btver1__) || defined(__btver2__)\
    )
#define BOOST_ATOMIC_X86_HAS_CMPXCHG8B 1
#endif

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
    BOOST_CONSTEXPR atomic_flag(void) BOOST_NOEXCEPT : v_(0) {}

    bool
    test_and_set(memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    clear(memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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

#if defined(__x86_64__) || defined(BOOST_ATOMIC_X86_HAS_CMPXCHG8B)
#define BOOST_ATOMIC_LLONG_LOCK_FREE 2
#else
#define BOOST_ATOMIC_LLONG_LOCK_FREE 0
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
class base_atomic<T, int, 1, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type v) BOOST_NOEXCEPT : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        return fetch_add(-v, order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_and(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for(; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<T, int, 2, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type v) BOOST_NOEXCEPT : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        return fetch_add(-v, order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_and(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<T, int, 4, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type v) BOOST_NOEXCEPT : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        return fetch_add(-v, order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_and(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<T, int, 8, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type v) BOOST_NOEXCEPT : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        return fetch_add(-v, order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_and(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<void *, void *, 4, Sign>
{
    typedef base_atomic this_type;
    typedef ptrdiff_t difference_type;
    typedef void * value_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type v) BOOST_NOEXCEPT : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type exchange(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
    {
        return true;
    }

    value_type
    fetch_add(difference_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        platform_fence_before(order);
        __asm__ (
        "lock ; xaddl %0, %1"
        : "+r" (v), "+m" (v_)
                );
        platform_fence_after(order);
        return reinterpret_cast<value_type>(v);
    }

    value_type
    fetch_sub(difference_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        return fetch_add(-v, order);
    }

    BOOST_ATOMIC_DECLARE_VOID_POINTER_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

template<typename T, bool Sign>
class base_atomic<T *, void *, 4, Sign>
{
    typedef base_atomic this_type;
    typedef T * value_type;
    typedef ptrdiff_t difference_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type v) BOOST_NOEXCEPT : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_add(difference_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    fetch_sub(difference_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        return fetch_add(-v, order);
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<void *, void *, 8, Sign>
{
    typedef base_atomic this_type;
    typedef ptrdiff_t difference_type;
    typedef void * value_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type v) BOOST_NOEXCEPT : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type exchange(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
    {
        return true;
    }

    value_type
    fetch_add(difference_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        platform_fence_before(order);
        __asm__ (
            "lock ; xaddq %0, %1"
            : "+r" (v), "+m" (v_)
        );
        platform_fence_after(order);
        return reinterpret_cast<value_type>(v);
    }

    value_type
    fetch_sub(difference_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        return fetch_add(-v, order);
    }

    BOOST_ATOMIC_DECLARE_VOID_POINTER_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

template<typename T, bool Sign>
class base_atomic<T *, void *, 8, Sign>
{
    typedef base_atomic this_type;
    typedef T * value_type;
    typedef ptrdiff_t difference_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type v) BOOST_NOEXCEPT : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            const_cast<volatile value_type &>(v_) = v;
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        value_type v = const_cast<const volatile value_type &>(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_add(difference_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    fetch_sub(difference_type v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
    {
        return fetch_add(-v, order);
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<T, void, 1, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef uint8_t storage_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type const& v) BOOST_NOEXCEPT :
        v_(reinterpret_cast<storage_type const&>(v))
    {}
    base_atomic(void) {}

    void
    store(value_type const& v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        storage_type tmp = const_cast<volatile storage_type &>(v_);
        platform_fence_after_load(order);
        value_type v;
        memcpy(&v, &tmp, sizeof(value_type));
        return v;
    }

    value_type
    exchange(value_type const& v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<T, void, 2, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef uint16_t storage_type;
public:
    BOOST_CONSTEXPR explicit base_atomic(value_type const& v) BOOST_NOEXCEPT :
        v_(reinterpret_cast<storage_type const&>(v))
    {}
    base_atomic(void) {}

    void
    store(value_type const& v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        storage_type tmp = const_cast<volatile storage_type &>(v_);
        platform_fence_after_load(order);
        value_type v;
        memcpy(&v, &tmp, sizeof(value_type));
        return v;
    }

    value_type
    exchange(value_type const& v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<T, void, 4, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef uint32_t storage_type;
public:
    explicit base_atomic(value_type const& v) BOOST_NOEXCEPT : v_(0)
    {
        memcpy(&v_, &v, sizeof(value_type));
    }
    base_atomic(void) {}

    void
    store(value_type const& v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        storage_type tmp = const_cast<volatile storage_type &>(v_);
        platform_fence_after_load(order);
        value_type v;
        memcpy(&v, &tmp, sizeof(value_type));
        return v;
    }

    value_type
    exchange(value_type const& v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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
class base_atomic<T, void, 8, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef uint64_t storage_type;
public:
    explicit base_atomic(value_type const& v) BOOST_NOEXCEPT : v_(0)
    {
        memcpy(&v_, &v, sizeof(value_type));
    }
    base_atomic(void) {}

    void
    store(value_type const& v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
    load(memory_order order = memory_order_seq_cst) const volatile BOOST_NOEXCEPT
    {
        storage_type tmp = const_cast<volatile storage_type &>(v_);
        platform_fence_after_load(order);
        value_type v;
        memcpy(&v, &tmp, sizeof(value_type));
        return v;
    }

    value_type
    exchange(value_type const& v, memory_order order = memory_order_seq_cst) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
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
        memory_order failure_order) volatile BOOST_NOEXCEPT
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile BOOST_NOEXCEPT
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

#if !defined(__x86_64__) && defined(BOOST_ATOMIC_X86_HAS_CMPXCHG8B)

template<typename T>
inline bool
platform_cmpxchg64_strong(T & expected, T desired, volatile T * ptr) BOOST_NOEXCEPT
{
#ifdef __GCC_HAVE_SYNC_COMPARE_AND_SWAP_8
    const T oldval = __sync_val_compare_and_swap(ptr, expected, desired);
    const bool result = (oldval == expected);
    expected = oldval;
    return result;
#else
    uint32_t scratch;
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
        : "D" ((uint32_t)desired), "c" ((uint32_t)(desired >> 32)), "S" (ptr), "0" (prev)
        : "memory");
    bool success = (prev == expected);
    expected = prev;
    return success;
#endif
}

// Intel 64 and IA-32 Architectures Software Developer's Manual, Volume 3A, 8.1.1. Guaranteed Atomic Operations:
//
// The Pentium processor (and newer processors since) guarantees that the following additional memory operations will always be carried out atomically:
// * Reading or writing a quadword aligned on a 64-bit boundary
//
// Luckily, the memory is almost always 8-byte aligned in our case because atomic<> uses 64 bit native types for storage and dynamic memory allocations
// have at least 8 byte alignment. The only unfortunate case is when atomic is placeod on the stack and it is not 8-byte aligned (like on 32 bit Windows).

template<typename T>
inline void
platform_store64(T value, volatile T * ptr) BOOST_NOEXCEPT
{
    if (((uint32_t)ptr & 0x00000007) == 0)
    {
#if defined(__SSE2__)
        __asm__ __volatile__
        (
            "movq %1, %%xmm0\n\t"
            "movq %%xmm0, %0\n\t"
            : "=m" (*ptr)
            : "m" (value)
            : "memory", "xmm0"
        );
#else
        __asm__ __volatile__
        (
            "fildll %1\n\t"
            "fistpll %0\n\t"
            : "=m" (*ptr)
            : "m" (value)
            : "memory"
        );
#endif
    }
    else
    {
        T expected = *ptr;
        while (!platform_cmpxchg64_strong(expected, value, ptr))
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
    }
}

template<typename T>
inline T
platform_load64(const volatile T * ptr) BOOST_NOEXCEPT
{
    T value = T();

    if (((uint32_t)ptr & 0x00000007) == 0)
    {
#if defined(__SSE2__)
        __asm__ __volatile__
        (
            "movq %1, %%xmm0\n\t"
            "movq %%xmm0, %0\n\t"
            : "=m" (value)
            : "m" (*ptr)
            : "memory", "xmm0"
        );
#else
        __asm__ __volatile__
        (
            "fildll %1\n\t"
            "fistpll %0\n\t"
            : "=m" (value)
            : "m" (*ptr)
            : "memory"
        );
#endif
    }
    else
    {
        // We don't care for comparison result here; the previous value will be stored into value anyway.
        platform_cmpxchg64_strong(value, value, const_cast<volatile T*>(ptr));
    }

    return value;
}

#endif

}
}
}

/* pull in 64-bit atomic type using cmpxchg8b above */
#if !defined(__x86_64__) && defined(BOOST_ATOMIC_X86_HAS_CMPXCHG8B)
#include <boost/atomic/detail/cas64strong.hpp>
#endif

#endif /* !defined(BOOST_ATOMIC_FORCE_FALLBACK) */

#endif
