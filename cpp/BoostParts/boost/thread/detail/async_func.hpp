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
// The async_func code is based on the one from libcxx.
//===----------------------------------------------------------------------===//

#ifndef BOOST_THREAD_DETAIL_ASYNC_FUNCT_HPP
#define BOOST_THREAD_DETAIL_ASYNC_FUNCT_HPP

#include <boost/config.hpp>

#include <boost/utility/result_of.hpp>
#include <boost/thread/detail/move.hpp>
#include <boost/thread/detail/invoke.hpp>
#include <boost/thread/detail/make_tuple_indices.hpp>

#if ! defined(BOOST_NO_CXX11_HDR_TUPLE)
#include <tuple>
#endif

namespace boost
{
  namespace detail
  {

#if ! defined(BOOST_NO_CXX11_VARIADIC_TEMPLATES) && \
    ! defined(BOOST_NO_CXX11_RVALUE_REFERENCES) && \
    ! defined(BOOST_NO_CXX11_HDR_TUPLE)

    template <class Fp, class... Args>
    class async_func
    {
        std::tuple<Fp, Args...> f_;

    public:
        //typedef typename invoke_of<_Fp, _Args...>::type Rp;
        typedef typename result_of<Fp(Args...)>::type result_type;

        BOOST_SYMBOL_VISIBLE
        explicit async_func(Fp&& f, Args&&... args)
            : f_(boost::move(f), boost::move(args)...) {}

        BOOST_SYMBOL_VISIBLE
        async_func(async_func&& f) : f_(boost::move(f.f_)) {}

        result_type operator()()
        {
            typedef typename make_tuple_indices<1+sizeof...(Args), 1>::type Index;
            return execute(Index());
        }
    private:
        template <size_t ...Indices>
        result_type
        execute(tuple_indices<Indices...>)
        {
            return invoke(boost::move(std::get<0>(f_)), boost::move(std::get<Indices>(f_))...);
        }
    };
#else
    template <class Fp>
    class async_func
    {
        Fp f_;

    public:
        BOOST_THREAD_COPYABLE_AND_MOVABLE(async_func)

        typedef typename result_of<Fp()>::type result_type;

        BOOST_SYMBOL_VISIBLE
        explicit async_func(BOOST_THREAD_FWD_REF(Fp) f)
            : f_(boost::move(f)) {}

        BOOST_SYMBOL_VISIBLE
        async_func(BOOST_THREAD_FWD_REF(async_func) f) : f_(boost::move(f.f_)) {}

        result_type operator()()
        {
            return execute();
        }
    private:
        result_type
        execute()
        {
            return f_();
        }
    };
#endif
  }
}

#endif // header
