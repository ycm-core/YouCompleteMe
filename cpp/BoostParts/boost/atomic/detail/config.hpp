#ifndef BOOST_ATOMIC_DETAIL_CONFIG_HPP
#define BOOST_ATOMIC_DETAIL_CONFIG_HPP

//  Copyright (c) 2012 Hartmut Kaiser
//
//  Distributed under the Boost Software License, Version 1.0.
//  See accompanying file LICENSE_1_0.txt or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

#include <boost/config.hpp>

#if (defined(_MSC_VER) && (_MSC_VER >= 1020)) || defined(__GNUC__) || defined(BOOST_CLANG) || defined(BOOST_INTEL) || defined(__COMO__) || defined(__DMC__)
#define BOOST_ATOMIC_HAS_PRAGMA_ONCE
#endif

#ifdef BOOST_ATOMIC_HAS_PRAGMA_ONCE
#pragma once
#endif

///////////////////////////////////////////////////////////////////////////////
//  Set up dll import/export options
#if (defined(BOOST_ATOMIC_DYN_LINK) || defined(BOOST_ALL_DYN_LINK)) && \
    !defined(BOOST_ATOMIC_STATIC_LINK)

#if defined(BOOST_ATOMIC_SOURCE)
#define BOOST_ATOMIC_DECL BOOST_SYMBOL_EXPORT
#define BOOST_ATOMIC_BUILD_DLL
#else
#define BOOST_ATOMIC_DECL BOOST_SYMBOL_IMPORT
#endif

#endif // building a shared library

#ifndef BOOST_ATOMIC_DECL
#define BOOST_ATOMIC_DECL
#endif

///////////////////////////////////////////////////////////////////////////////
//  Auto library naming
#if !defined(BOOST_ATOMIC_SOURCE) && !defined(BOOST_ALL_NO_LIB) && \
    !defined(BOOST_ATOMIC_NO_LIB)

#define BOOST_LIB_NAME boost_atomic

// tell the auto-link code to select a dll when required:
#if defined(BOOST_ALL_DYN_LINK) || defined(BOOST_ATOMIC_DYN_LINK)
#define BOOST_DYN_LINK
#endif

#include <boost/config/auto_link.hpp>

#endif  // auto-linking disabled

#endif
