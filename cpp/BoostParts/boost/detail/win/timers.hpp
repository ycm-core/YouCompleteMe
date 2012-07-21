//  timers.hpp  --------------------------------------------------------------//

//  Copyright 2010 Vicente J. Botet Escriba

//  Distributed under the Boost Software License, Version 1.0.
//  See http://www.boost.org/LICENSE_1_0.txt


#ifndef BOOST_DETAIL_WIN_TIMERS_HPP
#define BOOST_DETAIL_WIN_TIMERS_HPP

#include <boost/detail/win/basic_types.hpp>


namespace boost
{
namespace detail
{
namespace win32
{
#if defined( BOOST_USE_WINDOWS_H )
    using ::QueryPerformanceCounter;
    using ::QueryPerformanceFrequency;
#else
extern "C" { 
    __declspec(dllimport) BOOL_ WINAPI
        QueryPerformanceCounter(
            LARGE_INTEGER_ *lpPerformanceCount
        );

    __declspec(dllimport) BOOL_ WINAPI
        QueryPerformanceFrequency(
            LARGE_INTEGER_ *lpFrequency
        );
}
#endif
}
}
}

#endif // BOOST_DETAIL_WIN_TIMERS_HPP
