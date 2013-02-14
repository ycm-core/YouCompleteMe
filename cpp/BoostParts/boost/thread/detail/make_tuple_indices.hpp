// Copyright (C) 2012 Vicente J. Botet Escriba
//
//  Distributed under the Boost Software License, Version 1.0. (See accompanying
//  file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

//===----------------------------------------------------------------------===//
//
//                     The LLVM Compiler Infrastructure
//
// This file is dual licensed under the MIT and the University of Illinois Open
// Source Licenses. See LICENSE.TXT for details.
//
// The make_tuple_indices code is based on the one from libcxx.
//===----------------------------------------------------------------------===//

#ifndef BOOST_THREAD_DETAIL_MAKE_TUPLE_INDICES_HPP
#define BOOST_THREAD_DETAIL_MAKE_TUPLE_INDICES_HPP

#include <boost/config.hpp>
#include <boost/static_assert.hpp>

namespace boost
{
  namespace detail
  {

#if ! defined(BOOST_NO_CXX11_VARIADIC_TEMPLATES) && \
    ! defined(BOOST_NO_CXX11_RVALUE_REFERENCES)

    // make_tuple_indices

    template <std::size_t...> struct tuple_indices
    {};

    template <std::size_t Sp, class IntTuple, std::size_t Ep>
    struct make_indices_imp;

    template <std::size_t Sp, std::size_t ...Indices, std::size_t Ep>
    struct make_indices_imp<Sp, tuple_indices<Indices...>, Ep>
    {
      typedef typename make_indices_imp<Sp+1, tuple_indices<Indices..., Sp>, Ep>::type type;
    };

    template <std::size_t Ep, std::size_t ...Indices>
    struct make_indices_imp<Ep, tuple_indices<Indices...>, Ep>
    {
      typedef tuple_indices<Indices...> type;
    };

    template <std::size_t Ep, std::size_t Sp = 0>
    struct make_tuple_indices
    {
      BOOST_STATIC_ASSERT_MSG(Sp <= Ep, "make_tuple_indices input error");
      typedef typename make_indices_imp<Sp, tuple_indices<>, Ep>::type type;
    };
#endif
  }
}

#endif // header
