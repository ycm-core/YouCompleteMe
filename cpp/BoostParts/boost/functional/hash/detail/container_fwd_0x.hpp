
// Copyright 2012 Daniel James.
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

#if !defined(BOOST_DETAIL_CONTAINER_FWD_0X_HPP)
#define BOOST_DETAIL_CONTAINER_FWD_0X_HPP

#include <boost/detail/container_fwd.hpp>

// std::array

#if !defined(BOOST_NO_0X_HDR_ARRAY)
    // Don't forward declare std::array for Dinkumware, as it seems to be
    // just 'using std::tr1::array'.
#   if (defined(BOOST_DETAIL_NO_CONTAINER_FWD) && \
        !defined(BOOST_DETAIL_TEST_FORCE_CONTAINER_FWD)) || \
        (defined(_YVALS) && !defined(__IBMCPP__)) || defined(_CPPLIB_VER)
#       include <array>
#    else
namespace std {
    template <class, std::size_t> class array;
}
#    endif
#endif

// std::tuple

#if !defined(BOOST_NO_0X_HDR_TUPLE)
#   if (defined(BOOST_DETAIL_NO_CONTAINER_FWD) && \
        !defined(BOOST_DETAIL_TEST_FORCE_CONTAINER_FWD)) || \
        defined(BOOST_NO_VARIADIC_TEMPLATES)
#       include <tuple>
#    else
namespace std {
    template <typename...> class tuple;
}
#    endif
#endif

#endif
