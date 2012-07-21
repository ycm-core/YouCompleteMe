//////////////////////////////////////////////////////////////////////////////
//
// (C) Copyright 2011-2012 Vicente J. Botet Escriba
// Software License, Version 1.0. (See accompanying file
// LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// See http://www.boost.org/libs/thread for documentation.
//
//////////////////////////////////////////////////////////////////////////////

#ifndef BOOST_THREAD_DETAIL_MEMORY_HPP
#define BOOST_THREAD_DETAIL_MEMORY_HPP

#include <boost/container/allocator_traits.hpp>
#include <boost/container/scoped_allocator.hpp>
#include <boost/config.hpp>

namespace boost
{
  namespace thread_detail
  {
    template <class _Alloc>
    class allocator_destructor
    {
      typedef container::allocator_traits<_Alloc> alloc_traits;
    public:
      typedef typename alloc_traits::pointer pointer;
      typedef typename alloc_traits::size_type size_type;
    private:
      _Alloc& alloc_;
      size_type s_;
    public:
      allocator_destructor(_Alloc& a, size_type s)BOOST_NOEXCEPT
      : alloc_(a), s_(s)
      {}
      void operator()(pointer p)BOOST_NOEXCEPT
      {
        alloc_traits::deallocate(alloc_, p, s_);
      }
    };
  } //namespace thread_detail

  typedef container::allocator_arg_t allocator_arg_t;
  BOOST_CONSTEXPR allocator_arg_t allocator_arg = {};

  template <class T, class Alloc>
  struct uses_allocator: public container::uses_allocator<T, Alloc>
  {
  };

} // namespace boost


#endif //  BOOST_THREAD_DETAIL_MEMORY_HPP
