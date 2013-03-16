#ifndef BOOST_ATOMIC_DETAIL_BASE_HPP
#define BOOST_ATOMIC_DETAIL_BASE_HPP

//  Copyright (c) 2009 Helge Bahmann
//
//  Distributed under the Boost Software License, Version 1.0.
//  See accompanying file LICENSE_1_0.txt or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

// Base class definition and fallback implementation.
// To be overridden (through partial specialization) by
// platform implementations.

#include <string.h>

#include <cstddef>
#include <boost/cstdint.hpp>
#include <boost/atomic/detail/config.hpp>
#include <boost/atomic/detail/lockpool.hpp>

#ifdef BOOST_ATOMIC_HAS_PRAGMA_ONCE
#pragma once
#endif

#define BOOST_ATOMIC_DECLARE_BASE_OPERATORS \
    operator value_type(void) volatile const \
    { \
        return load(memory_order_seq_cst); \
    } \
     \
    this_type & \
    operator=(value_type v) volatile \
    { \
        store(v, memory_order_seq_cst); \
        return *const_cast<this_type *>(this); \
    } \
     \
    bool \
    compare_exchange_strong( \
        value_type & expected, \
        value_type desired, \
        memory_order order = memory_order_seq_cst) volatile \
    { \
        return compare_exchange_strong(expected, desired, order, calculate_failure_order(order)); \
    } \
     \
    bool \
    compare_exchange_weak( \
        value_type & expected, \
        value_type desired, \
        memory_order order = memory_order_seq_cst) volatile \
    { \
        return compare_exchange_weak(expected, desired, order, calculate_failure_order(order)); \
    } \
     \

#define BOOST_ATOMIC_DECLARE_ADDITIVE_OPERATORS \
    value_type \
    operator++(int) volatile \
    { \
        return fetch_add(1); \
    } \
     \
    value_type \
    operator++(void) volatile \
    { \
        return fetch_add(1) + 1; \
    } \
     \
    value_type \
    operator--(int) volatile \
    { \
        return fetch_sub(1); \
    } \
     \
    value_type \
    operator--(void) volatile \
    { \
        return fetch_sub(1) - 1; \
    } \
     \
    value_type \
    operator+=(difference_type v) volatile \
    { \
        return fetch_add(v) + v; \
    } \
     \
    value_type \
    operator-=(difference_type v) volatile \
    { \
        return fetch_sub(v) - v; \
    } \

#define BOOST_ATOMIC_DECLARE_BIT_OPERATORS \
    value_type \
    operator&=(difference_type v) volatile \
    { \
        return fetch_and(v) & v; \
    } \
     \
    value_type \
    operator|=(difference_type v) volatile \
    { \
        return fetch_or(v) | v; \
    } \
     \
    value_type \
    operator^=(difference_type v) volatile \
    { \
        return fetch_xor(v) ^ v; \
    } \

#define BOOST_ATOMIC_DECLARE_POINTER_OPERATORS \
    BOOST_ATOMIC_DECLARE_BASE_OPERATORS \
    BOOST_ATOMIC_DECLARE_ADDITIVE_OPERATORS \

#define BOOST_ATOMIC_DECLARE_INTEGRAL_OPERATORS \
    BOOST_ATOMIC_DECLARE_BASE_OPERATORS \
    BOOST_ATOMIC_DECLARE_ADDITIVE_OPERATORS \
    BOOST_ATOMIC_DECLARE_BIT_OPERATORS \

namespace boost {
namespace atomics {
namespace detail {

inline memory_order
calculate_failure_order(memory_order order)
{
    switch(order) {
        case memory_order_acq_rel:
            return memory_order_acquire;
        case memory_order_release:
            return memory_order_relaxed;
        default:
            return order;
    }
}

template<typename T, typename C, unsigned int Size, bool Sign>
class base_atomic {
private:
    typedef base_atomic this_type;
    typedef T value_type;
    typedef lockpool::scoped_lock guard_type;
public:
    base_atomic(void) {}

    explicit base_atomic(const value_type & v)
    {
        memcpy(&v_, &v, sizeof(value_type));
    }

    void
    store(value_type const& v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<char *>(v_));

        memcpy(const_cast<char *>(v_), &v, sizeof(value_type));
    }

    value_type
    load(memory_order /*order*/ = memory_order_seq_cst) volatile const
    {
        guard_type guard(const_cast<const char *>(v_));

        value_type v;
        memcpy(&v, const_cast<const char *>(v_), sizeof(value_type));
        return v;
    }

    bool
    compare_exchange_strong(
        value_type & expected,
        value_type const& desired,
        memory_order /*success_order*/,
        memory_order /*failure_order*/) volatile
    {
        guard_type guard(const_cast<char *>(v_));

        if (memcmp(const_cast<char *>(v_), &expected, sizeof(value_type)) == 0) {
            memcpy(const_cast<char *>(v_), &desired, sizeof(value_type));
            return true;
        } else {
            memcpy(&expected, const_cast<char *>(v_), sizeof(value_type));
            return false;
        }
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

    value_type
    exchange(value_type const& v, memory_order /*order*/=memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<char *>(v_));

        value_type tmp;
        memcpy(&tmp, const_cast<char *>(v_), sizeof(value_type));

        memcpy(const_cast<char *>(v_), &v, sizeof(value_type));
        return tmp;
    }

    bool
    is_lock_free(void) const volatile
    {
        return false;
    }

    BOOST_ATOMIC_DECLARE_BASE_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;

    char v_[sizeof(value_type)];
};

template<typename T, unsigned int Size, bool Sign>
class base_atomic<T, int, Size, Sign> {
private:
    typedef base_atomic this_type;
    typedef T value_type;
    typedef T difference_type;
    typedef lockpool::scoped_lock guard_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        v_ = v;
    }

    value_type
    load(memory_order /*order*/ = memory_order_seq_cst) const volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type v = const_cast<const volatile value_type &>(v_);
        return v;
    }

    value_type
    exchange(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ = v;
        return old;
    }

    bool
    compare_exchange_strong(value_type & expected, value_type desired,
        memory_order /*success_order*/,
        memory_order /*failure_order*/) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        if (v_ == expected) {
            v_ = desired;
            return true;
        } else {
            expected = v_;
            return false;
        }
    }

    bool
    compare_exchange_weak(value_type & expected, value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type
    fetch_add(difference_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ += v;
        return old;
    }

    value_type
    fetch_sub(difference_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ -= v;
        return old;
    }

    value_type
    fetch_and(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ &= v;
        return old;
    }

    value_type
    fetch_or(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ |= v;
        return old;
    }

    value_type
    fetch_xor(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ ^= v;
        return old;
    }

    bool
    is_lock_free(void) const volatile
    {
        return false;
    }

    BOOST_ATOMIC_DECLARE_INTEGRAL_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

template<typename T, unsigned int Size, bool Sign>
class base_atomic<T *, void *, Size, Sign> {
private:
    typedef base_atomic this_type;
    typedef T * value_type;
    typedef ptrdiff_t difference_type;
    typedef lockpool::scoped_lock guard_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));
        v_ = v;
    }

    value_type
    load(memory_order /*order*/ = memory_order_seq_cst) const volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type v = const_cast<const volatile value_type &>(v_);
        return v;
    }

    value_type
    exchange(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ = v;
        return old;
    }

    bool
    compare_exchange_strong(value_type & expected, value_type desired,
        memory_order /*success_order*/,
        memory_order /*failure_order*/) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        if (v_ == expected) {
            v_ = desired;
            return true;
        } else {
            expected = v_;
            return false;
        }
    }

    bool
    compare_exchange_weak(value_type & expected, value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    value_type fetch_add(difference_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ += v;
        return old;
    }

    value_type fetch_sub(difference_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ -= v;
        return old;
    }

    bool
    is_lock_free(void) const volatile
    {
        return false;
    }

    BOOST_ATOMIC_DECLARE_POINTER_OPERATORS
private:
    base_atomic(const base_atomic  &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

template<unsigned int Size, bool Sign>
class base_atomic<void *, void *, Size, Sign> {
private:
    typedef base_atomic this_type;
    typedef void * value_type;
    typedef lockpool::scoped_lock guard_type;
public:
    explicit base_atomic(value_type v) : v_(v) {}
    base_atomic(void) {}

    void
    store(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));
        v_ = v;
    }

    value_type
    load(memory_order /*order*/ = memory_order_seq_cst) const volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type v = const_cast<const volatile value_type &>(v_);
        return v;
    }

    value_type
    exchange(value_type v, memory_order /*order*/ = memory_order_seq_cst) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        value_type old = v_;
        v_ = v;
        return old;
    }

    bool
    compare_exchange_strong(value_type & expected, value_type desired,
        memory_order /*success_order*/,
        memory_order /*failure_order*/) volatile
    {
        guard_type guard(const_cast<value_type *>(&v_));

        if (v_ == expected) {
            v_ = desired;
            return true;
        } else {
            expected = v_;
            return false;
        }
    }

    bool
    compare_exchange_weak(value_type & expected, value_type desired,
        memory_order success_order,
        memory_order failure_order) volatile
    {
        return compare_exchange_strong(expected, desired, success_order, failure_order);
    }

    bool
    is_lock_free(void) const volatile
    {
        return false;
    }

    BOOST_ATOMIC_DECLARE_BASE_OPERATORS
private:
    base_atomic(const base_atomic &) /* = delete */ ;
    void operator=(const base_atomic &) /* = delete */ ;
    value_type v_;
};

}
}
}

#endif
