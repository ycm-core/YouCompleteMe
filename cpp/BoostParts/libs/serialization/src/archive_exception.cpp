/////////1/////////2/////////3/////////4/////////5/////////6/////////7/////////8
// archive_exception.cpp:

// (C) Copyright 2009 Robert Ramey - http://www.rrsd.com . 
// Use, modification and distribution is subject to the Boost Software
// License, Version 1.0. (See accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)

//  See http://www.boost.org for updates, documentation, and revision history.

#if (defined _MSC_VER) && (_MSC_VER == 1200)
#  pragma warning (disable : 4786) // too long name, harmless warning
#endif

#include <exception>
#include <boost/assert.hpp>
#include <string>

#define BOOST_ARCHIVE_SOURCE
#include <boost/archive/archive_exception.hpp>

namespace boost {
namespace archive {

BOOST_ARCHIVE_DECL(BOOST_PP_EMPTY())
archive_exception::archive_exception(
    exception_code c, 
    const char * e1,
    const char * e2
) : 
    code(c)
{
    m_msg = "programming error";
    switch(code){
    case no_exception:
        m_msg = "uninitialized exception";
        break;
    case unregistered_class:
        m_msg = "unregistered class";
        if(NULL != e1){
            m_msg += " - ";
            m_msg += e1;
        }    
        break;
    case invalid_signature:
        m_msg = "invalid signature";
        break;
    case unsupported_version:
        m_msg = "unsupported version";
        break;
    case pointer_conflict:
        m_msg = "pointer conflict";
        break;
    case incompatible_native_format:
        m_msg = "incompatible native format";
        if(NULL != e1){
            m_msg += " - ";
            m_msg += e1;
        }    
        break;
    case array_size_too_short:
        m_msg = "array size too short";
        break;
    case input_stream_error:
        m_msg = "input stream error";
        break;
    case invalid_class_name:
        m_msg = "class name too long";
        break;
    case unregistered_cast:
        m_msg = "unregistered void cast ";
        m_msg += (NULL != e1) ? e1 : "?";
        m_msg += "<-";
        m_msg += (NULL != e2) ? e2 : "?";
        break;
    case unsupported_class_version:
        m_msg = "class version ";
        m_msg += (NULL != e1) ? e1 : "<unknown class>";
        break;
    case other_exception:
        // if get here - it indicates a derived exception 
        // was sliced by passing by value in catch
        m_msg = "unknown derived exception";
        break;
    case multiple_code_instantiation:
        m_msg = "code instantiated in more than one module";
        if(NULL != e1){
            m_msg += " - ";
            m_msg += e1;
        }    
        break;
    case output_stream_error:
        m_msg = "output stream error";
        break;
    default:
        BOOST_ASSERT(false);
        break;
    }
}
BOOST_ARCHIVE_DECL(BOOST_PP_EMPTY())
archive_exception::~archive_exception() throw () {}

BOOST_ARCHIVE_DECL(const char *)
archive_exception::what( ) const throw()
{
    return m_msg.c_str();
}
BOOST_ARCHIVE_DECL(BOOST_PP_EMPTY())
archive_exception::archive_exception() : 
        code(no_exception)
{}

} // archive
} // boost
