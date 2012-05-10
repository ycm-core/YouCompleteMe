//=======================================================================
// Copyright 1997, 1998, 1999, 2000 University of Notre Dame.
// Authors: Andrew Lumsdaine, Lie-Quan Lee, Jeremy G. Siek
//
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)
//=======================================================================

#ifndef BOOST_GRAPH_TRAITS_HPP
#define BOOST_GRAPH_TRAITS_HPP

#include <boost/config.hpp>
#include <iterator>
#include <utility> /* Primarily for std::pair */
#include <boost/tuple/tuple.hpp>
#include <boost/mpl/if.hpp>
#include <boost/mpl/bool.hpp>
#include <boost/mpl/not.hpp>
#include <boost/type_traits/is_same.hpp>
#include <boost/iterator/iterator_categories.hpp>
#include <boost/iterator/iterator_adaptor.hpp>
#include <boost/pending/property.hpp>
#include <boost/detail/workaround.hpp>

namespace boost {

    template <typename G>
    struct graph_traits {
        typedef typename G::vertex_descriptor      vertex_descriptor;
        typedef typename G::edge_descriptor        edge_descriptor;
        typedef typename G::adjacency_iterator     adjacency_iterator;
        typedef typename G::out_edge_iterator      out_edge_iterator;
        typedef typename G::in_edge_iterator       in_edge_iterator;
        typedef typename G::vertex_iterator        vertex_iterator;
        typedef typename G::edge_iterator          edge_iterator;

        typedef typename G::directed_category      directed_category;
        typedef typename G::edge_parallel_category edge_parallel_category;
        typedef typename G::traversal_category     traversal_category;

        typedef typename G::vertices_size_type     vertices_size_type;
        typedef typename G::edges_size_type        edges_size_type;
        typedef typename G::degree_size_type       degree_size_type;

        static inline vertex_descriptor null_vertex();
    };

    template <typename G>
    inline typename graph_traits<G>::vertex_descriptor
    graph_traits<G>::null_vertex()
    { return G::null_vertex(); }

    // directed_category tags
    struct directed_tag { };
    struct undirected_tag { };
    struct bidirectional_tag : public directed_tag { };

    namespace detail {
        inline bool is_directed(directed_tag) { return true; }
        inline bool is_directed(undirected_tag) { return false; }
    }

    /** Return true if the given graph is directed. */
    template <typename Graph>
    bool is_directed(const Graph&) {
        typedef typename graph_traits<Graph>::directed_category Cat;
        return detail::is_directed(Cat());
    }

    /** Return true if the given graph is undirected. */
    template <typename Graph>
    bool is_undirected(const Graph& g) {
        return !is_directed(g);
    }

    /** @name Directed/Undirected Graph Traits */
    //@{
    namespace graph_detail {
        template <typename Tag>
        struct is_directed_tag
            : mpl::bool_<is_convertible<Tag, directed_tag>::value>
        { };
    } // namespace graph_detail

    template <typename Graph>
    struct is_directed_graph
        : graph_detail::is_directed_tag<
            typename graph_traits<Graph>::directed_category
        >
    { };

    template <typename Graph>
    struct is_undirected_graph
        : mpl::not_< is_directed_graph<Graph> >
    { };
    //@}

    // edge_parallel_category tags
    struct allow_parallel_edge_tag { };
    struct disallow_parallel_edge_tag { };

    namespace detail {
        inline bool allows_parallel(allow_parallel_edge_tag) { return true; }
        inline bool allows_parallel(disallow_parallel_edge_tag) { return false; }
    }

    template <typename Graph>
    bool allows_parallel_edges(const Graph&) {
        typedef typename graph_traits<Graph>::edge_parallel_category Cat;
        return detail::allows_parallel(Cat());
    }

    /** @name Parallel Edges Traits */
    //@{
    /**
     * The is_multigraph metafunction returns true if the graph allows
     * parallel edges. Technically, a multigraph is a simple graph that
     * allows parallel edges, but since there are no traits for the allowance
     * or disallowance of loops, this is a moot point.
     */
    template <typename Graph>
    struct is_multigraph
        : mpl::bool_<
            is_same<
                typename graph_traits<Graph>::edge_parallel_category,
                allow_parallel_edge_tag
            >::value
        >
    { };
    //@}

    // traversal_category tags
    struct incidence_graph_tag { };
    struct adjacency_graph_tag { };
    struct bidirectional_graph_tag : virtual incidence_graph_tag { };
    struct vertex_list_graph_tag { };
    struct edge_list_graph_tag { };
    struct adjacency_matrix_tag { };

    /** @name Taversal Category Traits
     * These traits classify graph types by their supported methods of
     * vertex and edge traversal.
     */
    //@{
    template <typename Graph>
    struct is_incidence_graph
        : mpl::bool_<
            is_convertible<
                typename graph_traits<Graph>::traversal_category,
                incidence_graph_tag
            >::value
        >
    { };

    template <typename Graph>
    struct is_bidirectional_graph
        : mpl::bool_<
            is_convertible<
                typename graph_traits<Graph>::traversal_category,
                bidirectional_graph_tag
            >::value
        >
    { };

    template <typename Graph>
    struct is_vertex_list_graph
        : mpl::bool_<
            is_convertible<
                typename graph_traits<Graph>::traversal_category,
                vertex_list_graph_tag
            >::value
        >
    { };

    template <typename Graph>
    struct is_edge_list_graph
        : mpl::bool_<
            is_convertible<
                typename graph_traits<Graph>::traversal_category,
                edge_list_graph_tag
            >::value
        >
    { };

    template <typename Graph>
    struct is_adjacency_matrix
        : mpl::bool_<
            is_convertible<
                typename graph_traits<Graph>::traversal_category,
                adjacency_matrix_tag
            >::value
        >
    { };
    //@}

    /** @name Directed Graph Traits
     * These metafunctions are used to fully classify directed vs. undirected
     * graphs. Recall that an undirected graph is also bidirectional, but it
     * cannot be both undirected and directed at the same time.
     */
    //@{
    template <typename Graph>
    struct is_directed_unidirectional_graph
        : mpl::and_<
            is_directed_graph<Graph>, mpl::not_< is_bidirectional_graph<Graph> >
        >
    { };

    template <typename Graph>
    struct is_directed_bidirectional_graph
        : mpl::and_<
            is_directed_graph<Graph>, is_bidirectional_graph<Graph>
        >
    { };
    //@}

    //?? not the right place ?? Lee
    typedef boost::forward_traversal_tag multi_pass_input_iterator_tag;

    // Forward declare graph_bundle_t property name (from
    // boost/graph/properties.hpp, which includes this file) for
    // bundled_result.
    enum graph_bundle_t {graph_bundle};

    template <typename G>
    struct graph_property_type {
      typedef typename G::graph_property_type type;
    };
    template <typename G>
    struct edge_property_type {
      typedef typename G::edge_property_type type;
    };
    template <typename G>
    struct vertex_property_type {
      typedef typename G::vertex_property_type type;
    };

    struct no_bundle { };
    struct no_graph_bundle : no_bundle { };
    struct no_vertex_bundle : no_bundle { };
    struct no_edge_bundle : no_bundle { };

    template<typename G>
    struct graph_bundle_type {
      typedef typename G::graph_bundled type;
    };

    template<typename G>
    struct vertex_bundle_type {
      typedef typename G::vertex_bundled type;
    };

    template<typename G>
    struct edge_bundle_type {
      typedef typename G::edge_bundled type;
    };

    namespace graph { namespace detail {
        template<typename Graph, typename Descriptor>
        class bundled_result {
            typedef typename graph_traits<Graph>::vertex_descriptor Vertex;
            typedef typename mpl::if_c<(is_same<Descriptor, Vertex>::value),
                                        vertex_bundle_type<Graph>,
                                        edge_bundle_type<Graph> >::type bundler;
        public:
            typedef typename bundler::type type;
        };

        template<typename Graph>
        class bundled_result<Graph, graph_bundle_t> {
            typedef typename graph_traits<Graph>::vertex_descriptor Vertex;
            typedef graph_bundle_type<Graph> bundler;
        public:
            typedef typename bundler::type type;
        };

    } } // namespace graph::detail

    namespace graph_detail {
      // A helper metafunction for determining whether or not a type is
      // bundled.
      template <typename T>
      struct is_no_bundle : mpl::bool_<is_convertible<T, no_bundle>::value>
      { };
    } // namespace graph_detail

    /** @name Graph Property Traits
     * These metafunctions (along with those above), can be used to access the
     * vertex and edge properties (bundled or otherwise) of vertices and
     * edges.
     */
    //@{
    template<typename Graph>
    struct has_graph_property
      : mpl::not_<
        typename detail::is_no_property<
          typename graph_property_type<Graph>::type
        >::type
      >::type
    { };

    template<typename Graph>
    struct has_bundled_graph_property
      : mpl::not_<
        graph_detail::is_no_bundle<typename graph_bundle_type<Graph>::type>
      >
    { };

    template <typename Graph>
    struct has_vertex_property
        : mpl::not_<
            typename detail::is_no_property<typename vertex_property_type<Graph>::type>
        >::type
    { };

    template <typename Graph>
    struct has_bundled_vertex_property
        : mpl::not_<
            graph_detail::is_no_bundle<typename vertex_bundle_type<Graph>::type>
        >
    { };

    template <typename Graph>
    struct has_edge_property
        : mpl::not_<
            typename detail::is_no_property<typename edge_property_type<Graph>::type>
        >::type
    { };

    template <typename Graph>
    struct has_bundled_edge_property
        : mpl::not_<
            graph_detail::is_no_bundle<typename edge_bundle_type<Graph>::type>
        >
    { };
    //@}

} // namespace boost

// Since pair is in namespace std, Koenig lookup will find source and
// target if they are also defined in namespace std.  This is illegal,
// but the alternative is to put source and target in the global
// namespace which causes name conflicts with other libraries (like
// SUIF).
namespace std {

  /* Some helper functions for dealing with pairs as edges */
  template <class T, class G>
  T source(pair<T,T> p, const G&) { return p.first; }

  template <class T, class G>
  T target(pair<T,T> p, const G&) { return p.second; }

}

#if defined(__GNUC__) && defined(__SGI_STL_PORT)
// For some reason g++ with STLport does not see the above definition
// of source() and target() unless we bring them into the boost
// namespace.
namespace boost {
  using std::source;
  using std::target;
}
#endif

#endif // BOOST_GRAPH_TRAITS_HPP
