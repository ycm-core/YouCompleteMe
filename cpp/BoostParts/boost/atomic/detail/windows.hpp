#ifndef BOOST_ATOMIC_DETAIL_WINDOWS_HPP
#define BOOST_ATOMIC_DETAIL_WINDOWS_HPP

//  Copyright (c) 2009 Helge Bahmann
//  Copyright (c) 2012 Andrey Semashev
//
//  Distributed under the Boost Software License, Version 1.0.
//  See accompanying file LICENSE_1_0.txt or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

#include <cstddef>
#include <boost/cstdint.hpp>
#include <boost/type_traits/make_signed.hpp>
#include <boost/atomic/detail/config.hpp>
#include <boost/atomic/detail/interlocked.hpp>

#ifdef BOOST_ATOMIC_HAS_PRAGMA_ONCE
#pragma once
#endif

#ifdef _MSC_VER
#pragma warning(push)
// 'order' : unreferenced formal parameter
#pragma warning(disable: 4100)
#endif

namespace boost {
namespace atomics {
namespace detail {

#if defined(_MSC_VER) && (defined(_M_AMD64) || defined(_M_IX86))
extern "C" void _mm_pause(void);
#pragma intrinsic(_mm_pause)
#define BOOST_ATOMIC_X86_PAUSE() _mm_pause()
#else
#define BOOST_ATOMIC_X86_PAUSE()
#endif

// Define hardware barriers
#if defined(_MSC_VER) && (defined(_M_AMD64) || (defined(_M_IX86) && defined(_M_IX86_FP) && _M_IX86_FP >= 2))
extern "C" void _mm_mfence(void);
#pragma intrinsic(_mm_mfence)
#endif

BOOST_FORCEINLINE void hardware_full_fence(void)
{
#if defined(_MSC_VER) && (defined(_M_AMD64) || (defined(_M_IX86) && defined(_M_IX86_FP) && _M_IX86_FP >= 2))
    // Use mfence only if SSE2 is available
    _mm_mfence();
#else
    long tmp;
    BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&tmp, 0);
#endif
}

// Define compiler barriers
#if defined(_MSC_VER) && _MSC_VER >= 1310 && !defined(_WIN32_WCE)
extern "C" void _ReadWriteBarrier();
#pragma intrinsic(_ReadWriteBarrier)
#define BOOST_ATOMIC_READ_WRITE_BARRIER() _ReadWriteBarrier()
#endif

#ifndef BOOST_ATOMIC_READ_WRITE_BARRIER
#define BOOST_ATOMIC_READ_WRITE_BARRIER()
#endif

BOOST_FORCEINLINE void
platform_fence_before(memory_order)
{
    BOOST_ATOMIC_READ_WRITE_BARRIER();
}

BOOST_FORCEINLINE void
platform_fence_after(memory_order)
{
    BOOST_ATOMIC_READ_WRITE_BARRIER();
}

BOOST_FORCEINLINE void
platform_fence_before_store(memory_order)
{
    BOOST_ATOMIC_READ_WRITE_BARRIER();
}

BOOST_FORCEINLINE void
platform_fence_after_store(memory_order)
{
    BOOST_ATOMIC_READ_WRITE_BARRIER();
}

BOOST_FORCEINLINE void
platform_fence_after_load(memory_order order)
{
    BOOST_ATOMIC_READ_WRITE_BARRIER();

    // On x86 and x86_64 there is no need for a hardware barrier,
    // even if seq_cst memory order is requested, because all
    // seq_cst writes are implemented with lock-prefixed operations
    // or xchg which has implied lock prefix. Therefore normal loads
    // are already ordered with seq_cst stores on these architectures.

#if !(defined(_MSC_VER) && (defined(_M_AMD64) || defined(_M_IX86)))
    if (order == memory_order_seq_cst)
        hardware_full_fence();
#endif
}

} // namespace detail
} // namespace atomics

#define BOOST_ATOMIC_THREAD_FENCE 2
BOOST_FORCEINLINE void
atomic_thread_fence(memory_order order)
{
    BOOST_ATOMIC_READ_WRITE_BARRIER();
    if (order == memory_order_seq_cst)
        atomics::detail::hardware_full_fence();
}

#define BOOST_ATOMIC_SIGNAL_FENCE 2
BOOST_FORCEINLINE void
atomic_signal_fence(memory_order)
{
    BOOST_ATOMIC_READ_WRITE_BARRIER();
}

#undef BOOST_ATOMIC_READ_WRITE_BARRIER

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
        atomics::detail::platform_fence_before(order);
        const uint32_t old = (uint32_t)BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&v_, 1);
        atomics::detail::platform_fence_after(order);
        return old != 0;
    }

    void
    clear(memory_order order = memory_order_seq_cst) volatile
    {
        atomics::detail::platform_fence_before_store(order);
        BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&v_, 0);
        atomics::detail::platform_fence_after_store(order);
    }
};

} // namespace boost

#define BOOST_ATOMIC_FLAG_LOCK_FREE 2

#include <boost/atomic/detail/base.hpp>

#if !defined(BOOST_ATOMIC_FORCE_FALLBACK)

#define BOOST_ATOMIC_CHAR_LOCK_FREE 2
#define BOOST_ATOMIC_SHORT_LOCK_FREE 2
#define BOOST_ATOMIC_INT_LOCK_FREE 2
#define BOOST_ATOMIC_LONG_LOCK_FREE 2
#if defined(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE64)
#define BOOST_ATOMIC_LLONG_LOCK_FREE 2
#else
#define BOOST_ATOMIC_LLONG_LOCK_FREE 0
#endif
#define BOOST_ATOMIC_POINTER_LOCK_FREE 2
#define BOOST_ATOMIC_BOOL_LOCK_FREE 2

namespace boost {
namespace atomics {
namespace detail {

#if defined(_MSC_VER)
#pragma warning(push)
// 'char' : forcing value to bool 'true' or 'false' (performance warning)
#pragma warning(disable: 4800)
#endif

template<typename T, bool Sign>
class base_atomic<T, int, 1, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
#ifdef BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE8
    typedef value_type storage_type;
#else
    typedef uint32_t storage_type;
#endif
    typedef T difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            v_ = static_cast< storage_type >(v);
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = static_cast< value_type >(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
#ifdef BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD8
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD8(&v_, v));
#else
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD(&v_, v));
#endif
        platform_fence_after(order);
        return v;
    }

    value_type
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        typedef typename make_signed< value_type >::type signed_value_type;
        return fetch_add(static_cast< value_type >(-static_cast< signed_value_type >(v)), order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
#ifdef BOOST_ATOMIC_INTERLOCKED_EXCHANGE8
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE8(&v_, v));
#else
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&v_, v));
#endif
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
#ifdef BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE8
        value_type oldval = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE8(&v_, desired, previous));
#else
        value_type oldval = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE(&v_, desired, previous));
#endif
        bool success = (previous == oldval);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = oldval;
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
#ifdef BOOST_ATOMIC_INTERLOCKED_AND8
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_AND8(&v_, v));
        platform_fence_after(order);
        return v;
#elif defined(BOOST_ATOMIC_INTERLOCKED_AND)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_AND(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
#ifdef BOOST_ATOMIC_INTERLOCKED_OR8
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_OR8(&v_, v));
        platform_fence_after(order);
        return v;
#elif defined(BOOST_ATOMIC_INTERLOCKED_OR)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_OR(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
#ifdef BOOST_ATOMIC_INTERLOCKED_XOR8
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_XOR8(&v_, v));
        platform_fence_after(order);
        return v;
#elif defined(BOOST_ATOMIC_INTERLOCKED_XOR)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_XOR(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
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
    storage_type v_;
};

#if defined(_MSC_VER)
#pragma warning(pop)
#endif

template<typename T, bool Sign>
class base_atomic<T, int, 2, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
#ifdef BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE16
    typedef value_type storage_type;
#else
    typedef uint32_t storage_type;
#endif
    typedef T difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            v_ = static_cast< storage_type >(v);
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = static_cast< value_type >(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
#ifdef BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD16
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD16(&v_, v));
#else
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD(&v_, v));
#endif
        platform_fence_after(order);
        return v;
    }

    value_type
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        typedef typename make_signed< value_type >::type signed_value_type;
        return fetch_add(static_cast< value_type >(-static_cast< signed_value_type >(v)), order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
#ifdef BOOST_ATOMIC_INTERLOCKED_EXCHANGE16
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE16(&v_, v));
#else
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&v_, v));
#endif
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
#ifdef BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE16
        value_type oldval = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE16(&v_, desired, previous));
#else
        value_type oldval = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE(&v_, desired, previous));
#endif
        bool success = (previous == oldval);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = oldval;
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
#ifdef BOOST_ATOMIC_INTERLOCKED_AND16
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_AND16(&v_, v));
        platform_fence_after(order);
        return v;
#elif defined(BOOST_ATOMIC_INTERLOCKED_AND)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_AND(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
#ifdef BOOST_ATOMIC_INTERLOCKED_OR16
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_OR16(&v_, v));
        platform_fence_after(order);
        return v;
#elif defined(BOOST_ATOMIC_INTERLOCKED_OR)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_OR(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
#ifdef BOOST_ATOMIC_INTERLOCKED_XOR16
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_XOR16(&v_, v));
        platform_fence_after(order);
        return v;
#elif defined(BOOST_ATOMIC_INTERLOCKED_XOR)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_XOR(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
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
    storage_type v_;
};

template<typename T, bool Sign>
class base_atomic<T, int, 4, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef value_type storage_type;
    typedef T difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            v_ = static_cast< storage_type >(v);
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = static_cast< value_type >(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD(&v_, v));
        platform_fence_after(order);
        return v;
    }

    value_type
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        typedef typename make_signed< value_type >::type signed_value_type;
        return fetch_add(static_cast< value_type >(-static_cast< signed_value_type >(v)), order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&v_, v));
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
        value_type oldval = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE(&v_, desired, previous));
        bool success = (previous == oldval);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = oldval;
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
#if defined(BOOST_ATOMIC_INTERLOCKED_AND)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_AND(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
#if defined(BOOST_ATOMIC_INTERLOCKED_OR)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_OR(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for(; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
#if defined(BOOST_ATOMIC_INTERLOCKED_XOR)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_XOR(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
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
    storage_type v_;
};

#if defined(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE64)

template<typename T, bool Sign>
class base_atomic<T, int, 8, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
    typedef value_type storage_type;
    typedef T difference_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        if (order != memory_order_seq_cst) {
            platform_fence_before(order);
            v_ = static_cast< storage_type >(v);
        } else {
            exchange(v, order);
        }
    }

    value_type
    load(memory_order order = memory_order_seq_cst) const volatile
    {
        value_type v = static_cast< value_type >(v_);
        platform_fence_after_load(order);
        return v;
    }

    value_type
    fetch_add(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD64(&v_, v));
        platform_fence_after(order);
        return v;
    }

    value_type
    fetch_sub(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        typedef typename make_signed< value_type >::type signed_value_type;
        return fetch_add(static_cast< value_type >(-static_cast< signed_value_type >(v)), order);
    }

    value_type
    exchange(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE64(&v_, v));
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
        value_type oldval = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE64(&v_, desired, previous));
        bool success = (previous == oldval);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = oldval;
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
#if defined(BOOST_ATOMIC_INTERLOCKED_AND64)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_AND64(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp & v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
    }

    value_type
    fetch_or(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
#if defined(BOOST_ATOMIC_INTERLOCKED_OR64)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_OR64(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp | v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
    }

    value_type
    fetch_xor(value_type v, memory_order order = memory_order_seq_cst) volatile
    {
#if defined(BOOST_ATOMIC_INTERLOCKED_XOR64)
        platform_fence_before(order);
        v = static_cast< value_type >(BOOST_ATOMIC_INTERLOCKED_XOR64(&v_, v));
        platform_fence_after(order);
        return v;
#else
        value_type tmp = load(memory_order_relaxed);
        for (; !compare_exchange_weak(tmp, tmp ^ v, order, memory_order_relaxed);)
        {
            BOOST_ATOMIC_X86_PAUSE();
        }
        return tmp;
#endif
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
    storage_type v_;
};

#endif // defined(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE64)

// MSVC 2012 fails to recognize sizeof(T) as a constant expression in template specializations
enum msvc_sizeof_pointer_workaround { sizeof_pointer = sizeof(void*) };

template<bool Sign>
class base_atomic<void*, void*, sizeof_pointer, Sign>
{
    typedef base_atomic this_type;
    typedef void* value_type;
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
        v = (value_type)BOOST_ATOMIC_INTERLOCKED_EXCHANGE_POINTER(&v_, v);
        platform_fence_after(order);
        return v;
    }

    bool compare_exchange_strong(value_type & expected, value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        value_type previous = expected;
        platform_fence_before(success_order);
        value_type oldval = (value_type)BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE_POINTER(&v_, desired, previous);
        bool success = (previous == oldval);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = oldval;
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
class base_atomic<T*, void*, sizeof_pointer, Sign>
{
    typedef base_atomic this_type;
    typedef T* value_type;
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
        v = (value_type)BOOST_ATOMIC_INTERLOCKED_EXCHANGE_POINTER(&v_, v);
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
        value_type oldval = (value_type)BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE_POINTER(&v_, desired, previous);
        bool success = (previous == oldval);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        expected = oldval;
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
        value_type res = (value_type)BOOST_ATOMIC_INTERLOCKED_EXCHANGE_ADD_POINTER(&v_, v);
        platform_fence_after(order);
        return res;
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


template<typename T, bool Sign>
class base_atomic<T, void, 1, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
#ifdef BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE8
    typedef uint8_t storage_type;
#else
    typedef uint32_t storage_type;
#endif
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
#ifdef BOOST_ATOMIC_INTERLOCKED_EXCHANGE8
        tmp = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE8(&v_, tmp));
#else
        tmp = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&v_, tmp));
#endif
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
        platform_fence_before(success_order);
#ifdef BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE8
        storage_type oldval = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE8(&v_, desired_s, expected_s));
#else
        storage_type oldval = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE(&v_, desired_s, expected_s));
#endif
        bool success = (oldval == expected_s);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        memcpy(&expected, &oldval, sizeof(value_type));
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
class base_atomic<T, void, 2, Sign>
{
    typedef base_atomic this_type;
    typedef T value_type;
#ifdef BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE16
    typedef uint16_t storage_type;
#else
    typedef uint32_t storage_type;
#endif
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
#ifdef BOOST_ATOMIC_INTERLOCKED_EXCHANGE16
        tmp = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE16(&v_, tmp));
#else
        tmp = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&v_, tmp));
#endif
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
        platform_fence_before(success_order);
#ifdef BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE16
        storage_type oldval = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE16(&v_, desired_s, expected_s));
#else
        storage_type oldval = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE(&v_, desired_s, expected_s));
#endif
        bool success = (oldval == expected_s);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        memcpy(&expected, &oldval, sizeof(value_type));
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
class base_atomic<T, void, 4, Sign>
{
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
        tmp = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE(&v_, tmp));
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
        platform_fence_before(success_order);
        storage_type oldval = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE(&v_, desired_s, expected_s));
        bool success = (oldval == expected_s);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        memcpy(&expected, &oldval, sizeof(value_type));
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

#if defined(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE64)

template<typename T, bool Sign>
class base_atomic<T, void, 8, Sign>
{
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
        tmp = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_EXCHANGE64(&v_, tmp));
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
        platform_fence_before(success_order);
        storage_type oldval = static_cast< storage_type >(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE64(&v_, desired_s, expected_s));
        bool success = (oldval == expected_s);
        if (success)
            platform_fence_after(success_order);
        else
            platform_fence_after(failure_order);
        memcpy(&expected, &oldval, sizeof(value_type));
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

#endif // defined(BOOST_ATOMIC_INTERLOCKED_COMPARE_EXCHANGE64)

} // namespace detail
} // namespace atomics
} // namespace boost

#endif /* !defined(BOOST_ATOMIC_FORCE_FALLBACK) */

#ifdef _MSC_VER
#pragma warning(pop)
#endif

#endif
