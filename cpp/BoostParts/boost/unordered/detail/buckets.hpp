
// Copyright (C) 2003-2004 Jeremy B. Maitin-Shepard.
// Copyright (C) 2005-2011 Daniel James
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

#ifndef BOOST_UNORDERED_DETAIL_MANAGER_HPP_INCLUDED
#define BOOST_UNORDERED_DETAIL_MANAGER_HPP_INCLUDED

#if defined(_MSC_VER) && (_MSC_VER >= 1020)
# pragma once
#endif

#include <boost/unordered/detail/util.hpp>
#include <boost/unordered/detail/allocator_helpers.hpp>
#include <boost/type_traits/aligned_storage.hpp>
#include <boost/type_traits/alignment_of.hpp>
#include <boost/swap.hpp>
#include <boost/assert.hpp>
#include <boost/limits.hpp>
#include <boost/iterator.hpp>

#if defined(BOOST_MSVC)
#pragma warning(push)
#pragma warning(disable:4127) // conditional expression is constant
#endif

namespace boost { namespace unordered { namespace detail {

    template <typename Types> struct table;
    template <typename NodePointer> struct bucket;
    struct ptr_bucket;
    template <typename A, typename Bucket, typename Node, typename Policy>
    struct buckets;
    template <typename Types> struct table_impl;
    template <typename Types> struct grouped_table_impl;

    ///////////////////////////////////////////////////////////////////
    //
    // Node construction

    template <typename NodeAlloc>
    struct node_constructor
    {
    private:

        typedef NodeAlloc node_allocator;
        typedef boost::unordered::detail::allocator_traits<NodeAlloc>
            node_allocator_traits;
        typedef typename node_allocator_traits::value_type node;
        typedef typename node_allocator_traits::pointer node_pointer;
        typedef typename node::value_type value_type;

        node_allocator& alloc_;
        node_pointer node_;
        bool constructed_;

    public:

        node_constructor(node_allocator& n) :
            alloc_(n),
            node_(),
            constructed_(false)
        {
        }

        ~node_constructor();

        void construct_node();

        template <BOOST_UNORDERED_EMPLACE_TEMPLATE>
        void construct_value(BOOST_UNORDERED_EMPLACE_ARGS)
        {
            BOOST_ASSERT(node_ && !constructed_);
            boost::unordered::detail::construct_node(alloc_,
                boost::addressof(*node_), BOOST_UNORDERED_EMPLACE_FORWARD);
            node_->init(static_cast<typename node::link_pointer>(node_));
            constructed_ = true;
        }

        template <typename A0>
        void construct_value2(BOOST_FWD_REF(A0) a0)
        {
            BOOST_ASSERT(node_ && !constructed_);
#   if defined(BOOST_UNORDERED_VARIADIC_MOVE)
            boost::unordered::detail::construct_node(alloc_,
                boost::addressof(*node_), boost::forward<A0>(a0));
#   else
            boost::unordered::detail::construct_node(alloc_,
                boost::addressof(*node_),
                boost::unordered::detail::create_emplace_args(
                    boost::forward<A0>(a0)));
#   endif
            constructed_ = true;
            node_->init(static_cast<typename node::link_pointer>(node_));
        }

        value_type const& value() const {
            BOOST_ASSERT(node_ && constructed_);
            return node_->value();
        }

        node_pointer get()
        {
            return node_;
        }

        // no throw
        node_pointer release()
        {
            node_pointer p = node_;
            node_ = node_pointer();
            return p;
        }

    private:
        node_constructor(node_constructor const&);
        node_constructor& operator=(node_constructor const&);
    };
    
    template <typename Alloc>
    node_constructor<Alloc>::~node_constructor()
    {
        if (node_) {
            if (constructed_) {
                boost::unordered::detail::destroy_node(alloc_,
                    boost::addressof(*node_));
            }

            node_allocator_traits::deallocate(alloc_, node_, 1);
        }
    }

    template <typename Alloc>
    void node_constructor<Alloc>::construct_node()
    {
        if(!node_) {
            constructed_ = false;
            node_ = node_allocator_traits::allocate(alloc_, 1);
        }
        else if (constructed_) {
            boost::unordered::detail::destroy_node(alloc_,
                boost::addressof(*node_));
            constructed_ = false;
        }
    }

    ///////////////////////////////////////////////////////////////////
    //
    // Bucket

    template <typename NodePointer>
    struct bucket
    {
        typedef NodePointer previous_pointer;
        previous_pointer next_;

        bucket() : next_() {}

        previous_pointer first_from_start()
        {
            return next_;
        }

        enum { extra_node = true };
    };

    struct ptr_bucket
    {
        typedef ptr_bucket* previous_pointer;
        previous_pointer next_;

        ptr_bucket() : next_(0) {}

        previous_pointer first_from_start()
        {
            return this;
        }

        enum { extra_node = false };
    };

    template <typename LinkPointer>
    struct node_base
    {
        typedef LinkPointer link_pointer;
        link_pointer next_;

        node_base() : next_() {}
    };

}}}

namespace boost { namespace unordered { namespace iterator_detail {

    ////////////////////////////////////////////////////////////////////////////
    // Iterators
    //
    // all no throw

    template <typename NodePointer, typename Value> struct iterator;
    template <typename ConstNodePointer, typename NodePointer,
        typename Value> struct c_iterator;
    template <typename NodePointer, typename Value, typename Policy>
        struct l_iterator;
    template <typename ConstNodePointer, typename NodePointer,
        typename Value, typename Policy> struct cl_iterator;

    // Local Iterators
    //
    // all no throw

    template <typename NodePointer, typename Value, typename Policy>
    struct l_iterator
        : public boost::iterator<
            std::forward_iterator_tag, Value, std::ptrdiff_t,
            NodePointer, Value&>
    {
#if !defined(BOOST_NO_MEMBER_TEMPLATE_FRIENDS)
        template <typename ConstNodePointer, typename NodePointer2,
                typename Value2, typename Policy2>
        friend struct boost::unordered::iterator_detail::cl_iterator;
    private:
#endif
        typedef NodePointer node_pointer;
        typedef boost::unordered::iterator_detail::iterator<NodePointer, Value>
            iterator;
        node_pointer ptr_;
        std::size_t bucket_;
        std::size_t bucket_count_;

    public:

        l_iterator() : ptr_() {}

        l_iterator(iterator x, std::size_t b, std::size_t c)
            : ptr_(x.node_), bucket_(b), bucket_count_(c) {}

        Value& operator*() const {
            return ptr_->value();
        }

        Value* operator->() const {
            return ptr_->value_ptr();
        }

        l_iterator& operator++() {
            ptr_ = static_cast<node_pointer>(ptr_->next_);
            if (ptr_ && Policy::to_bucket(bucket_count_, ptr_->hash_)
                    != bucket_)
                ptr_ = node_pointer();
            return *this;
        }

        l_iterator operator++(int) {
            l_iterator tmp(*this);
            ++(*this);
            return tmp;
        }

        bool operator==(l_iterator x) const {
            return ptr_ == x.ptr_;
        }

        bool operator!=(l_iterator x) const {
            return ptr_ != x.ptr_;
        }
    };

    template <typename ConstNodePointer, typename NodePointer, typename Value,
             typename Policy>
    struct cl_iterator
        : public boost::iterator<
            std::forward_iterator_tag, Value, std::ptrdiff_t,
            ConstNodePointer, Value const&>
    {
        friend struct boost::unordered::iterator_detail::l_iterator
            <NodePointer, Value, Policy>;
    private:

        typedef NodePointer node_pointer;
        typedef boost::unordered::iterator_detail::iterator<NodePointer, Value>
            iterator;
        node_pointer ptr_;
        std::size_t bucket_;
        std::size_t bucket_count_;

    public:

        cl_iterator() : ptr_() {}

        cl_iterator(iterator x, std::size_t b, std::size_t c) :
            ptr_(x.node_), bucket_(b), bucket_count_(c) {}

        cl_iterator(boost::unordered::iterator_detail::l_iterator<
                NodePointer, Value, Policy> const& x) :
            ptr_(x.ptr_), bucket_(x.bucket_), bucket_count_(x.bucket_count_)
        {}

        Value const&
            operator*() const {
            return ptr_->value();
        }

        Value const* operator->() const {
            return ptr_->value_ptr();
        }

        cl_iterator& operator++() {
            ptr_ = static_cast<node_pointer>(ptr_->next_);
            if (ptr_ && Policy::to_bucket(bucket_count_, ptr_->hash_)
                    != bucket_)
                ptr_ = node_pointer();
            return *this;
        }

        cl_iterator operator++(int) {
            cl_iterator tmp(*this);
            ++(*this);
            return tmp;
        }

        friend bool operator==(cl_iterator const& x, cl_iterator const& y) {
            return x.ptr_ == y.ptr_;
        }

        friend bool operator!=(cl_iterator const& x, cl_iterator const& y) {
            return x.ptr_ != y.ptr_;
        }
    };

    template <typename NodePointer, typename Value>
    struct iterator
        : public boost::iterator<
            std::forward_iterator_tag, Value, std::ptrdiff_t,
            NodePointer, Value&>
    {
#if !defined(BOOST_NO_MEMBER_TEMPLATE_FRIENDS)
        template <typename, typename, typename>
        friend struct boost::unordered::iterator_detail::c_iterator;
        template <typename, typename, typename>
        friend struct boost::unordered::iterator_detail::l_iterator;
        template <typename, typename, typename, typename>
        friend struct boost::unordered::iterator_detail::cl_iterator;
        template <typename>
        friend struct boost::unordered::detail::table;
        template <typename, typename, typename, typename>
        friend struct boost::unordered::detail::buckets;
        template <typename>
        friend struct boost::unordered::detail::table_impl;
        template <typename>
        friend struct boost::unordered::detail::grouped_table_impl;
    private:
#endif
        typedef NodePointer node_pointer;
        node_pointer node_;

    public:

        iterator() : node_() {}

        explicit iterator(node_pointer const& x) : node_(x) {}

        Value& operator*() const {
            return node_->value();
        }

        Value* operator->() const {
            return &node_->value();
        }

        iterator& operator++() {
            node_ = static_cast<node_pointer>(node_->next_);
            return *this;
        }

        iterator operator++(int) {
            iterator tmp(node_);
            node_ = static_cast<node_pointer>(node_->next_);
            return tmp;
        }

        bool operator==(iterator const& x) const {
            return node_ == x.node_;
        }

        bool operator!=(iterator const& x) const {
            return node_ != x.node_;
        }
    };

    template <typename ConstNodePointer, typename NodePointer, typename Value>
    struct c_iterator
        : public boost::iterator<
            std::forward_iterator_tag, Value, std::ptrdiff_t,
            ConstNodePointer, Value const&>
    {
        friend struct boost::unordered::iterator_detail::iterator<
                NodePointer, Value>;

#if !defined(BOOST_NO_MEMBER_TEMPLATE_FRIENDS)
        template <typename>
        friend struct boost::unordered::detail::table;
        template <typename, typename, typename, typename>
        friend struct boost::unordered::detail::buckets;
        template <typename>
        friend struct boost::unordered::detail::table_impl;
        template <typename>
        friend struct boost::unordered::detail::grouped_table_impl;

    private:
#endif

        typedef NodePointer node_pointer;
        typedef boost::unordered::iterator_detail::iterator<NodePointer, Value>
            iterator;
        node_pointer node_;

    public:

        c_iterator() : node_() {}

        explicit c_iterator(node_pointer const& x) : node_(x) {}

        c_iterator(boost::unordered::iterator_detail::iterator<
                NodePointer, Value> const& x) : node_(x.node_) {}

        Value const& operator*() const {
            return node_->value();
        }

        Value const* operator->() const {
            return &node_->value();
        }

        c_iterator& operator++() {
            node_ = static_cast<node_pointer>(node_->next_);
            return *this;
        }

        c_iterator operator++(int) {
            c_iterator tmp(node_);
            node_ = static_cast<node_pointer>(node_->next_);
            return tmp;
        }

        friend bool operator==(c_iterator const& x, c_iterator const& y) {
            return x.node_ == y.node_;
        }

        friend bool operator!=(c_iterator const& x, c_iterator const& y) {
            return x.node_ != y.node_;
        }
    };
}}}

namespace boost { namespace unordered { namespace detail {

    ///////////////////////////////////////////////////////////////////
    //
    // Hash Policy
    //
    // Don't really want buckets to derive from this, but will for now.

    template <typename SizeT>
    struct prime_policy
    {
        template <typename Hash, typename T>
        static inline SizeT apply_hash(Hash const& hf, T const& x) {
            return hf(x);
        }

        static inline SizeT to_bucket(SizeT bucket_count, SizeT hash) {
            return hash % bucket_count;
        }

        static inline SizeT new_bucket_count(SizeT min) {
            return boost::unordered::detail::next_prime(min);
        }

        static inline SizeT prev_bucket_count(SizeT max) {
            return boost::unordered::detail::prev_prime(max);
        }
    };

    template <typename SizeT>
    struct mix64_policy
    {
        template <typename Hash, typename T>
        static inline SizeT apply_hash(Hash const& hf, T const& x) {
            SizeT key = hf(x);
            key = (~key) + (key << 21); // key = (key << 21) - key - 1;
            key = key ^ (key >> 24);
            key = (key + (key << 3)) + (key << 8); // key * 265
            key = key ^ (key >> 14);
            key = (key + (key << 2)) + (key << 4); // key * 21
            key = key ^ (key >> 28);
            key = key + (key << 31);
            return key;
        }

        static inline SizeT to_bucket(SizeT bucket_count, SizeT hash) {
            return hash & (bucket_count - 1);
        }

        static inline SizeT new_bucket_count(SizeT min) {
            if (min <= 4) return 4;
            --min;
            min |= min >> 1;
            min |= min >> 2;
            min |= min >> 4;
            min |= min >> 8;
            min |= min >> 16;
            min |= min >> 32;
            return min + 1;
        }

        static inline SizeT prev_bucket_count(SizeT max) {
            max |= max >> 1;
            max |= max >> 2;
            max |= max >> 4;
            max |= max >> 8;
            max |= max >> 16;
            max |= max >> 32;
            return (max >> 1) + 1;
        }
    };

    template <int digits, int radix>
    struct pick_policy_impl {
        typedef prime_policy<std::size_t> type;
    };

    template <>
    struct pick_policy_impl<64, 2> {
        typedef mix64_policy<std::size_t> type;
    };

    struct pick_policy :
        pick_policy_impl<
            std::numeric_limits<std::size_t>::digits,
            std::numeric_limits<std::size_t>::radix> {};

    ///////////////////////////////////////////////////////////////////
    //
    // Buckets

    template <typename A, typename Bucket, typename Node, typename Policy>
    struct buckets : Policy
    {
    private:
        buckets(buckets const&);
        buckets& operator=(buckets const&);
    public:
        typedef boost::unordered::detail::allocator_traits<A> traits;
        typedef typename traits::value_type value_type;

        typedef Policy policy;
        typedef Node node;
        typedef Bucket bucket;
        typedef typename boost::unordered::detail::rebind_wrap<A, node>::type
            node_allocator;
        typedef typename boost::unordered::detail::rebind_wrap<A, bucket>::type
            bucket_allocator;
        typedef boost::unordered::detail::allocator_traits<node_allocator>
            node_allocator_traits;
        typedef boost::unordered::detail::allocator_traits<bucket_allocator>
            bucket_allocator_traits;
        typedef typename node_allocator_traits::pointer
            node_pointer;
        typedef typename node_allocator_traits::const_pointer
            const_node_pointer;
        typedef typename bucket_allocator_traits::pointer
            bucket_pointer;
        typedef typename bucket::previous_pointer
            previous_pointer;
        typedef boost::unordered::detail::node_constructor<node_allocator>
            node_constructor;

        typedef boost::unordered::iterator_detail::
            iterator<node_pointer, value_type> iterator;
        typedef boost::unordered::iterator_detail::
            c_iterator<const_node_pointer, node_pointer, value_type> c_iterator;
        typedef boost::unordered::iterator_detail::
            l_iterator<node_pointer, value_type, policy> l_iterator;
        typedef boost::unordered::iterator_detail::
            cl_iterator<const_node_pointer, node_pointer, value_type, policy>
            cl_iterator;

        // Members

        bucket_pointer buckets_;
        std::size_t bucket_count_;
        std::size_t size_;
        boost::unordered::detail::compressed<bucket_allocator, node_allocator>
            allocators_;

        // Data access

        bucket_allocator const& bucket_alloc() const
        {
            return allocators_.first();
        }

        node_allocator const& node_alloc() const
        {
            return allocators_.second();
        }

        bucket_allocator& bucket_alloc()
        {
            return allocators_.first();
        }

        node_allocator& node_alloc()
        {
            return allocators_.second();
        }

        std::size_t max_bucket_count() const
        {
            // -1 to account for the start bucket.
            return policy::prev_bucket_count(
                bucket_allocator_traits::max_size(bucket_alloc()) - 1);
        }

        bucket_pointer get_bucket(std::size_t bucket_index) const
        {
            return buckets_ + static_cast<std::ptrdiff_t>(bucket_index);
        }

        previous_pointer get_previous_start() const
        {
            return this->get_bucket(this->bucket_count_)->first_from_start();
        }

        previous_pointer get_previous_start(std::size_t bucket_index) const
        {
            return this->get_bucket(bucket_index)->next_;
        }

        iterator get_start() const
        {
            return iterator(static_cast<node_pointer>(
                        this->get_previous_start()->next_));
        }

        iterator get_start(std::size_t bucket_index) const
        {
            previous_pointer prev = this->get_previous_start(bucket_index);
            return prev ? iterator(static_cast<node_pointer>(prev->next_)) :
                iterator();
        }

        float load_factor() const
        {
            BOOST_ASSERT(this->bucket_count_ != 0);
            return static_cast<float>(this->size_)
                / static_cast<float>(this->bucket_count_);
        }

        std::size_t bucket_size(std::size_t index) const
        {
            if (!this->size_) return 0;
            iterator it = this->get_start(index);
            if (!it.node_) return 0;

            std::size_t count = 0;
            while(it.node_ && policy::to_bucket(
                        this->bucket_count_, it.node_->hash_) == index)
            {
                ++count;
                ++it;
            }

            return count;
        }

        ////////////////////////////////////////////////////////////////////////
        // Constructors

        buckets(node_allocator const& a, std::size_t bucket_count) :
            buckets_(),
            bucket_count_(bucket_count),
            size_(),
            allocators_(a,a)
        {
        }

        buckets(buckets& b, boost::unordered::detail::move_tag m) :
            buckets_(),
            bucket_count_(b.bucket_count_),
            size_(),
            allocators_(b.allocators_, m)
        {
            swap(b);
        }

        template <typename Types>
        buckets(boost::unordered::detail::table<Types>& x,
                boost::unordered::detail::move_tag m) :
            buckets_(),
            bucket_count_(x.bucket_count_),
            size_(),
            allocators_(x.allocators_, m)
        {
            swap(x);
        }

        ////////////////////////////////////////////////////////////////////////
        // Create buckets
        // (never called in constructor to avoid exception issues)

        void create_buckets()
        {
            boost::unordered::detail::array_constructor<bucket_allocator>
                constructor(bucket_alloc());
    
            // Creates an extra bucket to act as the start node.
            constructor.construct(bucket(), this->bucket_count_ + 1);
    
            if (bucket::extra_node)
            {
                node_constructor a(this->node_alloc());
                a.construct_node();

                // Since this node is just to mark the beginning it doesn't
                // contain a value, so just construct node::node_base
                // which containers the pointer to the next element.
                node_allocator_traits::construct(node_alloc(),
                    static_cast<typename node::node_base*>(
                        boost::addressof(*a.get())),
                    typename node::node_base());

                (constructor.get() +
                    static_cast<std::ptrdiff_t>(this->bucket_count_))->next_ =
                        a.release();
            }

            this->buckets_ = constructor.release();
        }

        ////////////////////////////////////////////////////////////////////////
        // Swap and Move

        void swap(buckets& other, false_type = false_type())
        {
            BOOST_ASSERT(node_alloc() == other.node_alloc());
            boost::swap(buckets_, other.buckets_);
            boost::swap(bucket_count_, other.bucket_count_);
            boost::swap(size_, other.size_);
        }

        void swap(buckets& other, true_type)
        {
            allocators_.swap(other.allocators_);
            boost::swap(buckets_, other.buckets_);
            boost::swap(bucket_count_, other.bucket_count_);
            boost::swap(size_, other.size_);
        }

        void move_buckets_from(buckets& other)
        {
            BOOST_ASSERT(node_alloc() == other.node_alloc());
            BOOST_ASSERT(!this->buckets_);
            this->buckets_ = other.buckets_;
            this->bucket_count_ = other.bucket_count_;
            this->size_ = other.size_;
            other.buckets_ = bucket_pointer();
            other.bucket_count_ = 0;
            other.size_ = 0;
        }

        ////////////////////////////////////////////////////////////////////////
        // Delete/destruct

        inline void delete_node(c_iterator n)
        {
            boost::unordered::detail::destroy_node(
                node_alloc(), boost::addressof(*n.node_));
            node_allocator_traits::deallocate(node_alloc(), n.node_, 1);
            --size_;
        }

        std::size_t delete_nodes(c_iterator begin, c_iterator end)
        {
            std::size_t count = 0;

            while(begin != end) {
                c_iterator n = begin;
                ++begin;
                delete_node(n);
                ++count;
            }

            return count;
        }

        inline void delete_extra_node(bucket_pointer) {}

        inline void delete_extra_node(node_pointer n) {
            node_allocator_traits::destroy(node_alloc(),
                static_cast<typename node::node_base*>(boost::addressof(*n)));
            node_allocator_traits::deallocate(node_alloc(), n, 1);
        }

        inline ~buckets()
        {
            this->delete_buckets();
        }

        void delete_buckets()
        {
            if(this->buckets_) {
                previous_pointer prev = this->get_previous_start();

                while(prev->next_) {
                    node_pointer n = static_cast<node_pointer>(prev->next_);
                    prev->next_ = n->next_;
                    delete_node(iterator(n));
                }

                delete_extra_node(prev);

                bucket_pointer end = this->get_bucket(this->bucket_count_ + 1);
                for(bucket_pointer it = this->buckets_; it != end; ++it)
                {
                    bucket_allocator_traits::destroy(bucket_alloc(),
                        boost::addressof(*it));
                }

                bucket_allocator_traits::deallocate(bucket_alloc(),
                    this->buckets_, this->bucket_count_ + 1);
    
                this->buckets_ = bucket_pointer();
            }

            BOOST_ASSERT(!this->size_);
        }

        void clear()
        {
            if(!this->size_) return;

            previous_pointer prev = this->get_previous_start();

            while(prev->next_) {
                node_pointer n = static_cast<node_pointer>(prev->next_);
                prev->next_ = n->next_;
                delete_node(iterator(n));
            }

            bucket_pointer end = this->get_bucket(this->bucket_count_);
            for(bucket_pointer it = this->buckets_; it != end; ++it)
            {
                it->next_ = node_pointer();
            }

            BOOST_ASSERT(!this->size_);
        }

        // This is called after erasing a node or group of nodes to fix up
        // the bucket pointers.
        void fix_buckets(bucket_pointer this_bucket,
                previous_pointer prev, node_pointer next)
        {
            if (!next)
            {
                if (this_bucket->next_ == prev)
                    this_bucket->next_ = node_pointer();
            }
            else
            {
                bucket_pointer next_bucket = this->get_bucket(
                    policy::to_bucket(this->bucket_count_, next->hash_));

                if (next_bucket != this_bucket)
                {
                    next_bucket->next_ = prev;
                    if (this_bucket->next_ == prev)
                        this_bucket->next_ = node_pointer();
                }
            }
        }

        // This is called after erasing a range of nodes to fix any bucket
        // pointers into that range.
        void fix_buckets_range(std::size_t bucket_index,
                previous_pointer prev, node_pointer begin, node_pointer end)
        {
            node_pointer n = begin;
    
            // If we're not at the start of the current bucket, then
            // go to the start of the next bucket.
            if (this->get_bucket(bucket_index)->next_ != prev)
            {
                for(;;) {
                    n = static_cast<node_pointer>(n->next_);
                    if (n == end) return;
    
                    std::size_t new_bucket_index =
                        policy::to_bucket(this->bucket_count_, n->hash_);
                    if (bucket_index != new_bucket_index) {
                        bucket_index = new_bucket_index;
                        break;
                    }
                }
            }
    
            // Iterate through the remaining nodes, clearing out the bucket
            // pointers.
            this->get_bucket(bucket_index)->next_ = previous_pointer();
            for(;;) {
                n = static_cast<node_pointer>(n->next_);
                if (n == end) break;
    
                std::size_t new_bucket_index =
                    policy::to_bucket(this->bucket_count_, n->hash_);
                if (bucket_index != new_bucket_index) {
                    bucket_index = new_bucket_index;
                    this->get_bucket(bucket_index)->next_ = previous_pointer();
                }
            };
    
            // Finally fix the bucket containing the trailing node.
            if (n) {
                this->get_bucket(
                    policy::to_bucket(this->bucket_count_, n->hash_))->next_
                    = prev;
            }
        }
    };

    ////////////////////////////////////////////////////////////////////////////
    // Functions

    // Assigning and swapping the equality and hash function objects
    // needs strong exception safety. To implement that normally we'd
    // require one of them to be known to not throw and the other to
    // guarantee strong exception safety. Unfortunately they both only
    // have basic exception safety. So to acheive strong exception
    // safety we have storage space for two copies, and assign the new
    // copies to the unused space. Then switch to using that to use
    // them. This is implemented in 'set_hash_functions' which
    // atomically assigns the new function objects in a strongly
    // exception safe manner.

    template <class H, class P> class set_hash_functions;

    template <class H, class P>
    class functions
    {
        friend class boost::unordered::detail::set_hash_functions<H, P>;
        functions& operator=(functions const&);

        typedef compressed<H, P> function_pair;

        typedef typename boost::aligned_storage<
            sizeof(function_pair),
            boost::alignment_of<function_pair>::value>::type aligned_function;

        bool current_; // The currently active functions.
        aligned_function funcs_[2];

        function_pair const& current() const {
            return *static_cast<function_pair const*>(
                static_cast<void const*>(&funcs_[current_]));
        }

        void construct(bool which, H const& hf, P const& eq)
        {
            new((void*) &funcs_[which]) function_pair(hf, eq);
        }

        void construct(bool which, function_pair const& f)
        {
            new((void*) &funcs_[which]) function_pair(f);
        }
        
        void destroy(bool which)
        {
            boost::unordered::detail::destroy((function_pair*)(&funcs_[which]));
        }
        
    public:

        functions(H const& hf, P const& eq)
            : current_(false)
        {
            construct(current_, hf, eq);
        }

        functions(functions const& bf)
            : current_(false)
        {
            construct(current_, bf.current());
        }

        ~functions() {
            this->destroy(current_);
        }

        H const& hash_function() const {
            return current().first();
        }

        P const& key_eq() const {
            return current().second();
        }
    };
    
    template <class H, class P>
    class set_hash_functions
    {
        set_hash_functions(set_hash_functions const&);
        set_hash_functions& operator=(set_hash_functions const&);
    
        functions<H,P>& functions_;
        bool tmp_functions_;

    public:

        set_hash_functions(functions<H,P>& f, H const& h, P const& p)
          : functions_(f),
            tmp_functions_(!f.current_)
        {
            f.construct(tmp_functions_, h, p);
        }

        set_hash_functions(functions<H,P>& f, functions<H,P> const& other)
          : functions_(f),
            tmp_functions_(!f.current_)
        {
            f.construct(tmp_functions_, other.current());
        }

        ~set_hash_functions()
        {
            functions_.destroy(tmp_functions_);
        }

        void commit()
        {
            functions_.current_ = tmp_functions_;
            tmp_functions_ = !tmp_functions_;
        }
    };
}}}

#if defined(BOOST_MSVC)
#pragma warning(pop)
#endif

#endif
