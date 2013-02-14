//////////////////////////////////////////////////////////////////////////////
//
// (C) Copyright Ion Gaztanaga 2005-2012. Distributed under the Boost
// Software License, Version 1.0. (See accompanying file
// LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//
// See http://www.boost.org/libs/container for documentation.
//
//////////////////////////////////////////////////////////////////////////////

#ifndef BOOST_CONTAINER_DETAIL_UTILITIES_HPP
#define BOOST_CONTAINER_DETAIL_UTILITIES_HPP

#include "config_begin.hpp"
#include <cstdio>
#include <boost/type_traits/is_fundamental.hpp>
#include <boost/type_traits/is_pointer.hpp>
#include <boost/type_traits/is_enum.hpp>
#include <boost/type_traits/is_member_pointer.hpp>
#include <boost/type_traits/is_class.hpp>
#include <boost/move/utility.hpp>
#include <boost/move/iterator.hpp>
#include <boost/container/detail/mpl.hpp>
#include <boost/container/detail/type_traits.hpp>
#include <boost/container/allocator_traits.hpp>
#include <boost/detail/no_exceptions_support.hpp>
#include <algorithm>
#include <iterator>

namespace boost {
namespace container {
namespace container_detail {

template <typename T>
inline T* addressof(T& obj)
{
   return static_cast<T*>(
	   static_cast<void*>(
	      const_cast<char*>(
            &reinterpret_cast<const char&>(obj)
   )));
}

template<class T>
const T &max_value(const T &a, const T &b)
{  return a > b ? a : b;   }

template<class T>
const T &min_value(const T &a, const T &b)
{  return a < b ? a : b;   }

template <class SizeType>
SizeType
   get_next_capacity(const SizeType max_size
                    ,const SizeType capacity
                    ,const SizeType n)
{
//   if (n > max_size - capacity)
//      throw std::length_error("get_next_capacity");

   const SizeType m3 = max_size/3;

   if (capacity < m3)
      return capacity + max_value(3*(capacity+1)/5, n);

   if (capacity < m3*2)
      return capacity + max_value((capacity+1)/2, n);

   return max_size;
}

template <class T>
inline T* to_raw_pointer(T* p)
{  return p; }

template <class Pointer>
inline typename Pointer::element_type*
   to_raw_pointer(const Pointer &p)
{  return boost::container::container_detail::to_raw_pointer(p.operator->());  }

//!To avoid ADL problems with swap
template <class T>
inline void do_swap(T& x, T& y)
{
   using std::swap;
   swap(x, y);
}

template<class AllocatorType>
inline void swap_alloc(AllocatorType &, AllocatorType &, container_detail::false_type)
   BOOST_CONTAINER_NOEXCEPT
{}

template<class AllocatorType>
inline void swap_alloc(AllocatorType &l, AllocatorType &r, container_detail::true_type)
{  container_detail::do_swap(l, r);   }

template<class AllocatorType>
inline void assign_alloc(AllocatorType &, const AllocatorType &, container_detail::false_type)
   BOOST_CONTAINER_NOEXCEPT
{}

template<class AllocatorType>
inline void assign_alloc(AllocatorType &l, const AllocatorType &r, container_detail::true_type)
{  l = r;   }

template<class AllocatorType>
inline void move_alloc(AllocatorType &, AllocatorType &, container_detail::false_type)
   BOOST_CONTAINER_NOEXCEPT
{}

template<class AllocatorType>
inline void move_alloc(AllocatorType &l, AllocatorType &r, container_detail::true_type)
{  l = ::boost::move(r);   }

//Rounds "orig_size" by excess to round_to bytes
template<class SizeType>
inline SizeType get_rounded_size(SizeType orig_size, SizeType round_to)
{
   return ((orig_size-1)/round_to+1)*round_to;
}

template <std::size_t OrigSize, std::size_t RoundTo>
struct ct_rounded_size
{
   enum { value = ((OrigSize-1)/RoundTo+1)*RoundTo };
};

}  //namespace container_detail {

//////////////////////////////////////////////////////////////////////////////
//
//                               uninitialized_move_alloc
//
//////////////////////////////////////////////////////////////////////////////

//! <b>Effects</b>:
//!   \code
//!   for (; first != last; ++result, ++first)
//!      allocator_traits::construct(a, &*result, boost::move(*first));
//!   \endcode
//!
//! <b>Returns</b>: result
template
   <typename A,
    typename I, // I models InputIterator
    typename F> // F models ForwardIterator
F uninitialized_move_alloc(A &a, I f, I l, F r)
{
   F back = r;
   BOOST_TRY{
      while (f != l) {
         allocator_traits<A>::construct(a, container_detail::to_raw_pointer(&*r), boost::move(*f));
         ++f; ++r;
      }
   }
   BOOST_CATCH(...){
	   for (; back != r; ++back){
         allocator_traits<A>::destroy(a, container_detail::to_raw_pointer(&*back));
      }
	   BOOST_RETHROW;
   }
   BOOST_CATCH_END
   return r;
}

//////////////////////////////////////////////////////////////////////////////
//
//                               uninitialized_move_alloc_n
//
//////////////////////////////////////////////////////////////////////////////

//! <b>Effects</b>:
//!   \code
//!   for (; n--; ++result, ++first)
//!      allocator_traits::construct(a, &*result, boost::move(*first));
//!   \endcode
//!
//! <b>Returns</b>: result
template
   <typename A,
    typename I, // I models InputIterator
    typename F> // F models ForwardIterator
F uninitialized_move_alloc_n(A &a, I f, typename std::iterator_traits<I>::difference_type n, F r)
{
   F back = r;
   BOOST_TRY{
      while (n--) {
         allocator_traits<A>::construct(a, container_detail::to_raw_pointer(&*r), boost::move(*f));
         ++f; ++r;
      }
   }
   BOOST_CATCH(...){
	   for (; back != r; ++back){
         allocator_traits<A>::destroy(a, container_detail::to_raw_pointer(&*back));
      }
	   BOOST_RETHROW;
   }
   BOOST_CATCH_END
   return r;
}

//////////////////////////////////////////////////////////////////////////////
//
//                               uninitialized_move_alloc_n_source
//
//////////////////////////////////////////////////////////////////////////////

//! <b>Effects</b>:
//!   \code
//!   for (; n--; ++result, ++first)
//!      allocator_traits::construct(a, &*result, boost::move(*first));
//!   \endcode
//!
//! <b>Returns</b>: first (after incremented)
template
   <typename A,
    typename I, // I models InputIterator
    typename F> // F models ForwardIterator
I uninitialized_move_alloc_n_source(A &a, I f, typename std::iterator_traits<I>::difference_type n, F r)
{
   F back = r;
   BOOST_TRY{
      while (n--) {
         allocator_traits<A>::construct(a, container_detail::to_raw_pointer(&*r), boost::move(*f));
         ++f; ++r;
      }
   }
   BOOST_CATCH(...){
	   for (; back != r; ++back){
         allocator_traits<A>::destroy(a, container_detail::to_raw_pointer(&*back));
      }
	   BOOST_RETHROW;
   }
   BOOST_CATCH_END
   return f;
}

//////////////////////////////////////////////////////////////////////////////
//
//                               uninitialized_copy_alloc
//
//////////////////////////////////////////////////////////////////////////////

//! <b>Effects</b>:
//!   \code
//!   for (; first != last; ++result, ++first)
//!      allocator_traits::construct(a, &*result, *first);
//!   \endcode
//!
//! <b>Returns</b>: result
template
   <typename A,
    typename I, // I models InputIterator
    typename F> // F models ForwardIterator
F uninitialized_copy_alloc(A &a, I f, I l, F r)
{
   F back = r;
   BOOST_TRY{
      while (f != l) {
         allocator_traits<A>::construct(a, container_detail::to_raw_pointer(&*r), *f);
         ++f; ++r;
      }
   }
   BOOST_CATCH(...){
	   for (; back != r; ++back){
         allocator_traits<A>::destroy(a, container_detail::to_raw_pointer(&*back));
      }
	   BOOST_RETHROW;
   }
   BOOST_CATCH_END
   return r;
}

//////////////////////////////////////////////////////////////////////////////
//
//                               uninitialized_copy_alloc_n
//
//////////////////////////////////////////////////////////////////////////////

//! <b>Effects</b>:
//!   \code
//!   for (; n--; ++result, ++first)
//!      allocator_traits::construct(a, &*result, *first);
//!   \endcode
//!
//! <b>Returns</b>: result
template
   <typename A,
    typename I, // I models InputIterator
    typename F> // F models ForwardIterator
F uninitialized_copy_alloc_n(A &a, I f, typename std::iterator_traits<I>::difference_type n, F r)
{
   F back = r;
   BOOST_TRY{
      while (n--) {
         allocator_traits<A>::construct(a, container_detail::to_raw_pointer(&*r), *f);
         ++f; ++r;
      }
   }
   BOOST_CATCH(...){
	   for (; back != r; ++back){
         allocator_traits<A>::destroy(a, container_detail::to_raw_pointer(&*back));
      }
	   BOOST_RETHROW;
   }
   BOOST_CATCH_END
   return r;
}

//////////////////////////////////////////////////////////////////////////////
//
//                               uninitialized_copy_alloc_n_source
//
//////////////////////////////////////////////////////////////////////////////

//! <b>Effects</b>:
//!   \code
//!   for (; n--; ++result, ++first)
//!      allocator_traits::construct(a, &*result, *first);
//!   \endcode
//!
//! <b>Returns</b>: first (after incremented)
template
   <typename A,
    typename I, // I models InputIterator
    typename F> // F models ForwardIterator
I uninitialized_copy_alloc_n_source(A &a, I f, typename std::iterator_traits<I>::difference_type n, F r)
{
   F back = r;
   BOOST_TRY{
      while (n--) {
         allocator_traits<A>::construct(a, container_detail::to_raw_pointer(&*r), *f);
         ++f; ++r;
      }
   }
   BOOST_CATCH(...){
	   for (; back != r; ++back){
         allocator_traits<A>::destroy(a, container_detail::to_raw_pointer(&*back));
      }
	   BOOST_RETHROW;
   }
   BOOST_CATCH_END
   return f;
}

//////////////////////////////////////////////////////////////////////////////
//
//                               uninitialized_copy_alloc
//
//////////////////////////////////////////////////////////////////////////////

//! <b>Effects</b>:
//!   \code
//!   for (; first != last; ++result, ++first)
//!      allocator_traits::construct(a, &*result, *first);
//!   \endcode
//!
//! <b>Returns</b>: result
template
   <typename A,
    typename F, // F models ForwardIterator
    typename T>
void uninitialized_fill_alloc(A &a, F f, F l, const T &t)
{
   F back = f;
   BOOST_TRY{
      while (f != l) {
         allocator_traits<A>::construct(a, container_detail::to_raw_pointer(&*f), t);
         ++f;
      }
   }
   BOOST_CATCH(...){
	   for (; back != l; ++back){
         allocator_traits<A>::destroy(a, container_detail::to_raw_pointer(&*back));
      }
	   BOOST_RETHROW;
   }
   BOOST_CATCH_END
}

//////////////////////////////////////////////////////////////////////////////
//
//                            uninitialized_copy_or_move_alloc
//
//////////////////////////////////////////////////////////////////////////////

template
<typename A
,typename I    // I models InputIterator
,typename F>   // F models ForwardIterator
F uninitialized_copy_or_move_alloc
   (A &a, I f, I l, F r
   ,typename boost::container::container_detail::enable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   return ::boost::container::uninitialized_move_alloc(a, f, l, r);
}

template
<typename A
,typename I    // I models InputIterator
,typename F>   // F models ForwardIterator
F uninitialized_copy_or_move_alloc
   (A &a, I f, I l, F r
   ,typename boost::container::container_detail::disable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   return ::boost::container::uninitialized_copy_alloc(a, f, l, r);
}

//////////////////////////////////////////////////////////////////////////////
//
//                            uninitialized_copy_or_move_alloc_n
//
//////////////////////////////////////////////////////////////////////////////

template
<typename A
,typename I    // I models InputIterator
,typename F>   // F models ForwardIterator
F uninitialized_copy_or_move_alloc_n
   (A &a, I f, typename std::iterator_traits<I>::difference_type n, F r
   ,typename boost::container::container_detail::enable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   return ::boost::container::uninitialized_move_alloc_n(a, f, n, r);
}

template
<typename A
,typename I    // I models InputIterator
,typename F>   // F models ForwardIterator
F uninitialized_copy_or_move_alloc_n
   (A &a, I f, typename std::iterator_traits<I>::difference_type n, F r
   ,typename boost::container::container_detail::disable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   return ::boost::container::uninitialized_copy_alloc_n(a, f, n, r);
}


//////////////////////////////////////////////////////////////////////////////
//
//                            uninitialized_copy_or_move_alloc_n_source
//
//////////////////////////////////////////////////////////////////////////////

template
<typename A
,typename I    // I models InputIterator
,typename F>   // F models ForwardIterator
I uninitialized_copy_or_move_alloc_n_source
   (A &a, I f, typename std::iterator_traits<I>::difference_type n, F r
   ,typename boost::container::container_detail::enable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   return ::boost::container::uninitialized_move_alloc_n_source(a, f, n, r);
}

template
<typename A
,typename I    // I models InputIterator
,typename F>   // F models ForwardIterator
I uninitialized_copy_or_move_alloc_n_source
   (A &a, I f, typename std::iterator_traits<I>::difference_type n, F r
   ,typename boost::container::container_detail::disable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   return ::boost::container::uninitialized_copy_alloc_n_source(a, f, n, r);
}

//////////////////////////////////////////////////////////////////////////////
//
//                         copy_or_move
//
//////////////////////////////////////////////////////////////////////////////

template
<typename I,   // I models InputIterator
typename F>   // F models ForwardIterator
inline F copy_or_move(I f, I l, F r
   ,typename boost::container::container_detail::enable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   while (f != l) {
      *r = ::boost::move(*f);
      ++f; ++r;
   }
   return r;
}

template
<typename I,   // I models InputIterator
typename F>   // F models ForwardIterator
inline F copy_or_move(I f, I l, F r
   ,typename boost::container::container_detail::disable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   while (f != l) {
      *r = *f;
      ++f; ++r;
   }
   return r;
}

//////////////////////////////////////////////////////////////////////////////
//
//                         copy_or_move_n
//
//////////////////////////////////////////////////////////////////////////////

template
<typename I,   // I models InputIterator
typename F>   // F models ForwardIterator
inline F copy_or_move_n(I f, typename std::iterator_traits<I>::difference_type n, F r
   ,typename boost::container::container_detail::enable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   while (n--) {
      *r = ::boost::move(*f);
      ++f; ++r;
   }
   return r;
}

template
<typename I,   // I models InputIterator
typename F>   // F models ForwardIterator
inline F copy_or_move_n(I f, typename std::iterator_traits<I>::difference_type n, F r
   ,typename boost::container::container_detail::disable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   while (n--) {
      *r = *f;
      ++f; ++r;
   }
   return r;
}

//////////////////////////////////////////////////////////////////////////////
//
//                         copy_or_move_n_source
//
//////////////////////////////////////////////////////////////////////////////

template
<typename I,   // I models InputIterator
typename F>   // F models ForwardIterator
inline I copy_or_move_n_source(I f, typename std::iterator_traits<I>::difference_type n, F r
   ,typename boost::container::container_detail::enable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   while (n--) {
      *r = ::boost::move(*f);
      ++f; ++r;
   }
   return f;
}

template
<typename I,   // I models InputIterator
typename F>   // F models ForwardIterator
inline I copy_or_move_n_source(I f, typename std::iterator_traits<I>::difference_type n, F r
   ,typename boost::container::container_detail::disable_if
      < boost::move_detail::is_move_iterator<I> >::type* = 0)
{
   while (n--) {
      *r = *f;
      ++f; ++r;
   }
   return f;
}

}  //namespace container {
}  //namespace boost {


#include <boost/container/detail/config_end.hpp>

#endif   //#ifndef BOOST_CONTAINER_DETAIL_UTILITIES_HPP
