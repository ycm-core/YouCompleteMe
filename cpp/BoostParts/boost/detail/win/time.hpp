//  time.hpp  --------------------------------------------------------------//

//  Copyright 2010 Vicente J. Botet Escriba

//  Distributed under the Boost Software License, Version 1.0.
//  See http://www.boost.org/LICENSE_1_0.txt


#ifndef BOOST_DETAIL_WIN_TIME_HPP
#define BOOST_DETAIL_WIN_TIME_HPP

#include <boost/detail/win/basic_types.hpp>


namespace boost {
namespace detail {
namespace win32 {
#if defined( BOOST_USE_WINDOWS_H )
    typedef FILETIME FILETIME_;
    typedef PFILETIME PFILETIME_;
    typedef LPFILETIME LPFILETIME_;

    typedef SYSTEMTIME SYSTEMTIME_;
    typedef SYSTEMTIME* PSYSTEMTIME_;

    #ifndef UNDER_CE  // Windows CE does not define GetSystemTimeAsFileTime
    using ::GetSystemTimeAsFileTime;
    #endif
    using ::FileTimeToLocalFileTime;
    using ::GetSystemTime;
    using ::SystemTimeToFileTime;
    using ::GetTickCount;

#else
extern "C" {
    typedef struct _FILETIME {
        DWORD_ dwLowDateTime;
        DWORD_ dwHighDateTime;
    } FILETIME_, *PFILETIME_, *LPFILETIME_;

    typedef struct _SYSTEMTIME {
      WORD_ wYear;
      WORD_ wMonth;
      WORD_ wDayOfWeek;
      WORD_ wDay;
      WORD_ wHour;
      WORD_ wMinute;
      WORD_ wSecond;
      WORD_ wMilliseconds;
    } SYSTEMTIME_, *PSYSTEMTIME_;

    #ifndef UNDER_CE  // Windows CE does not define GetSystemTimeAsFileTime
    __declspec(dllimport) void WINAPI
        GetSystemTimeAsFileTime(FILETIME_* lpFileTime);
    #endif
    __declspec(dllimport) int WINAPI
        FileTimeToLocalFileTime(const FILETIME_* lpFileTime, 
                FILETIME_* lpLocalFileTime);
    __declspec(dllimport) void WINAPI
        GetSystemTime(SYSTEMTIME_* lpSystemTime);
    __declspec(dllimport) int WINAPI
        SystemTimeToFileTime(const SYSTEMTIME_* lpSystemTime, 
                FILETIME_* lpFileTime);
    __declspec(dllimport) unsigned long __stdcall 
        GetTickCount();
}
#endif
}
}
}

#endif // BOOST_DETAIL_WIN_TIME_HPP
