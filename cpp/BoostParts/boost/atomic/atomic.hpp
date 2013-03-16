#ifndef BOOST_ATOMIC_ATOMIC_HPP
#define BOOST_ATOMIC_ATOMIC_HPP

//  Copyright (c) 2011 Helge Bahmann
//
//  Distributed under the Boost Software License, Version 1.0.
//  See accompanying file LICENSE_1_0.txt or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

#include <cstddef>
#include <boost/cstdint.hpp>

#include <boost/memory_order.hpp>

#include <boost/atomic/detail/config.hpp>
#include <boost/atomic/detail/platform.hpp>
#include <boost/atomic/detail/type-classification.hpp>
#include <boost/type_traits/is_signed.hpp>

#ifdef BOOST_ATOMIC_HAS_PRAGMA_ONCE
#pragma once
#endif

namespace boost {

#ifndef BOOST_ATOMIC_CHAR_LOCK_FREE
#define BOOST_ATOMIC_CHAR_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_CHAR16_T_LOCK_FREE
#define BOOST_ATOMIC_CHAR16_T_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_CHAR32_T_LOCK_FREE
#define BOOST_ATOMIC_CHAR32_T_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_WCHAR_T_LOCK_FREE
#define BOOST_ATOMIC_WCHAR_T_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_SHORT_LOCK_FREE
#define BOOST_ATOMIC_SHORT_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_INT_LOCK_FREE
#define BOOST_ATOMIC_INT_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_LONG_LOCK_FREE
#define BOOST_ATOMIC_LONG_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_LLONG_LOCK_FREE
#define BOOST_ATOMIC_LLONG_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_POINTER_LOCK_FREE
#define BOOST_ATOMIC_POINTER_LOCK_FREE 0
#endif

#define BOOST_ATOMIC_ADDRESS_LOCK_FREE BOOST_ATOMIC_POINTER_LOCK_FREE

#ifndef BOOST_ATOMIC_BOOL_LOCK_FREE
#define BOOST_ATOMIC_BOOL_LOCK_FREE 0
#endif

#ifndef BOOST_ATOMIC_THREAD_FENCE
#define BOOST_ATOMIC_THREAD_FENCE 0
inline void atomic_thread_fence(memory_order)
{
}
#endif

#ifndef BOOST_ATOMIC_SIGNAL_FENCE
#define BOOST_ATOMIC_SIGNAL_FENCE 0
inline void atomic_signal_fence(memory_order order)
{
    atomic_thread_fence(order);
}
#endif

template<typename T>
class atomic :
    public atomics::detail::base_atomic<T, typename atomics::detail::classify<T>::type, atomics::detail::storage_size_of<T>::value, boost::is_signed<T>::value >
{
private:
    typedef T value_type;
    typedef atomics::detail::base_atomic<T, typename atomics::detail::classify<T>::type, atomics::detail::storage_size_of<T>::value, boost::is_signed<T>::value > super;
public:
    atomic(void) : super() {}
    explicit atomic(const value_type & v) : super(v) {}

    atomic & operator=(value_type v) volatile
    {
        super::operator=(v);
        return *const_cast<atomic *>(this);
    }
private:
    atomic(const atomic &) /* =delete */ ;
    atomic & operator=(const atomic &) /* =delete */ ;
};

typedef atomic<char> atomic_char;
typedef atomic<unsigned char> atomic_uchar;
typedef atomic<signed char> atomic_schar;
typedef atomic<uint8_t> atomic_uint8_t;
typedef atomic<int8_t> atomic_int8_t;
typedef atomic<unsigned short> atomic_ushort;
typedef atomic<short> atomic_short;
typedef atomic<uint16_t> atomic_uint16_t;
typedef atomic<int16_t> atomic_int16_t;
typedef atomic<unsigned int> atomic_uint;
typedef atomic<int> atomic_int;
typedef atomic<uint32_t> atomic_uint32_t;
typedef atomic<int32_t> atomic_int32_t;
typedef atomic<unsigned long> atomic_ulong;
typedef atomic<long> atomic_long;
typedef atomic<uint64_t> atomic_uint64_t;
typedef atomic<int64_t> atomic_int64_t;
#ifdef BOOST_HAS_LONG_LONG
typedef atomic<boost::ulong_long_type> atomic_ullong;
typedef atomic<boost::long_long_type> atomic_llong;
#endif
typedef atomic<void*> atomic_address;
typedef atomic<bool> atomic_bool;
typedef atomic<wchar_t> atomic_wchar_t;
#if !defined(BOOST_NO_CXX11_CHAR16_T)
typedef atomic<char16_t> atomic_char16_t;
#endif
#if !defined(BOOST_NO_CXX11_CHAR32_T)
typedef atomic<char32_t> atomic_char32_t;
#endif

typedef atomic<int_least8_t> atomic_int_least8_t;
typedef atomic<uint_least8_t> atomic_uint_least8_t;
typedef atomic<int_least16_t> atomic_int_least16_t;
typedef atomic<uint_least16_t> atomic_uint_least16_t;
typedef atomic<int_least32_t> atomic_int_least32_t;
typedef atomic<uint_least32_t> atomic_uint_least32_t;
typedef atomic<int_least64_t> atomic_int_least64_t;
typedef atomic<uint_least64_t> atomic_uint_least64_t;
typedef atomic<int_fast8_t> atomic_int_fast8_t;
typedef atomic<uint_fast8_t> atomic_uint_fast8_t;
typedef atomic<int_fast16_t> atomic_int_fast16_t;
typedef atomic<uint_fast16_t> atomic_uint_fast16_t;
typedef atomic<int_fast32_t> atomic_int_fast32_t;
typedef atomic<uint_fast32_t> atomic_uint_fast32_t;
typedef atomic<int_fast64_t> atomic_int_fast64_t;
typedef atomic<uint_fast64_t> atomic_uint_fast64_t;
typedef atomic<intmax_t> atomic_intmax_t;
typedef atomic<uintmax_t> atomic_uintmax_t;

typedef atomic<std::size_t> atomic_size_t;
typedef atomic<std::ptrdiff_t> atomic_ptrdiff_t;

// PGI seems to not support intptr_t/uintptr_t properly. BOOST_HAS_STDINT_H is not defined for this compiler by Boost.Config.
#if !defined(__PGIC__)

#if (defined(BOOST_WINDOWS) && !defined(_WIN32_WCE)) \
    || (defined(_XOPEN_UNIX) && (_XOPEN_UNIX+0 > 0)) \
    || defined(__CYGWIN__) \
    || defined(macintosh) || defined(__APPLE__) || defined(__APPLE_CC__) \
    || defined(__FreeBSD__) || defined(__NetBSD__) || defined(__OpenBSD__) || defined(__DragonFly__)
typedef atomic<intptr_t> atomic_intptr_t;
typedef atomic<uintptr_t> atomic_uintptr_t;
#elif defined(__GNUC__) || defined(__clang__)
#if defined(__INTPTR_TYPE__)
typedef atomic< __INTPTR_TYPE__ > atomic_intptr_t;
#endif
#if defined(__UINTPTR_TYPE__)
typedef atomic< __UINTPTR_TYPE__ > atomic_uintptr_t;
#endif
#endif

#endif

#ifndef BOOST_ATOMIC_FLAG_LOCK_FREE
#define BOOST_ATOMIC_FLAG_LOCK_FREE 0
class atomic_flag
{
public:
    atomic_flag(void) : v_(false) {}

    bool
    test_and_set(memory_order order = memory_order_seq_cst)
    {
        return v_.exchange(true, order);
    }

    void
    clear(memory_order order = memory_order_seq_cst) volatile
    {
        v_.store(false, order);
    }
private:
    atomic_flag(const atomic_flag &) /* = delete */ ;
    atomic_flag & operator=(const atomic_flag &) /* = delete */ ;
    atomic<bool> v_;
};
#endif

}

#endif
