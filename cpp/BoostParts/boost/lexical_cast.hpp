#ifndef BOOST_LEXICAL_CAST_INCLUDED
#define BOOST_LEXICAL_CAST_INCLUDED

// MS compatible compilers support #pragma once

#if defined(_MSC_VER) && (_MSC_VER >= 1020)
# pragma once
#endif

// Boost lexical_cast.hpp header  -------------------------------------------//
//
// See http://www.boost.org/libs/conversion for documentation.
// See end of this header for rights and permissions.
//
// what:  lexical_cast custom keyword cast
// who:   contributed by Kevlin Henney,
//        enhanced with contributions from Terje Slettebo,
//        with additional fixes and suggestions from Gennaro Prota,
//        Beman Dawes, Dave Abrahams, Daryle Walker, Peter Dimov,
//        Alexander Nasonov, Antony Polukhin, Justin Viiret, Michael Hofmann,
//        Cheng Yang, Matthew Bradbury, David W. Birdsall and other Boosters
// when:  November 2000, March 2003, June 2005, June 2006, March 2011 - 2012

#include <boost/config.hpp>
#if defined(BOOST_NO_STRINGSTREAM) || defined(BOOST_NO_STD_WSTRING)
#define BOOST_LCAST_NO_WCHAR_T
#endif

#include <climits>
#include <cstddef>
#include <string>
#include <cstring>
#include <cstdio>
#include <typeinfo>
#include <exception>
#include <boost/limits.hpp>
#include <boost/mpl/if.hpp>
#include <boost/throw_exception.hpp>
#include <boost/type_traits/ice.hpp>
#include <boost/type_traits/is_pointer.hpp>
#include <boost/static_assert.hpp>
#include <boost/detail/lcast_precision.hpp>
#include <boost/detail/workaround.hpp>


#ifndef BOOST_NO_STD_LOCALE
#   include <locale>
#else
#   ifndef BOOST_LEXICAL_CAST_ASSUME_C_LOCALE
#       warning "Unable to use <locale> header. boost::lexical_cast will use the 'C' locale."
#       define BOOST_LEXICAL_CAST_ASSUME_C_LOCALE
#   endif
#endif

#ifdef BOOST_NO_STRINGSTREAM
#include <strstream>
#else
#include <sstream>
#endif

#ifdef BOOST_NO_TYPEID
#define BOOST_LCAST_THROW_BAD_CAST(S, T) throw_exception(bad_lexical_cast())
#else
#define BOOST_LCAST_THROW_BAD_CAST(Source, Target) \
    throw_exception(bad_lexical_cast(typeid(Source), typeid(Target)))
#endif

namespace boost
{
    // exception used to indicate runtime lexical_cast failure
    class BOOST_SYMBOL_VISIBLE bad_lexical_cast :
    // workaround MSVC bug with std::bad_cast when _HAS_EXCEPTIONS == 0
#if defined(BOOST_MSVC) && defined(_HAS_EXCEPTIONS) && !_HAS_EXCEPTIONS
        public std::exception
#else
        public std::bad_cast
#endif

#if defined(__BORLANDC__) && BOOST_WORKAROUND( __BORLANDC__, < 0x560 )
        // under bcc32 5.5.1 bad_cast doesn't derive from exception
        , public std::exception
#endif

    {
    public:
        bad_lexical_cast() :
#ifndef BOOST_NO_TYPEID
          source(&typeid(void)), target(&typeid(void))
#else
          source(0), target(0) // this breaks getters
#endif
        {
        }

        bad_lexical_cast(
            const std::type_info &source_type_arg,
            const std::type_info &target_type_arg) :
            source(&source_type_arg), target(&target_type_arg)
        {
        }

        const std::type_info &source_type() const
        {
            return *source;
        }
        const std::type_info &target_type() const
        {
            return *target;
        }

        virtual const char *what() const throw()
        {
            return "bad lexical cast: "
                   "source type value could not be interpreted as target";
        }
        virtual ~bad_lexical_cast() throw()
        {
        }
    private:
        const std::type_info *source;
        const std::type_info *target;
    };

    namespace detail // widest_char
    {
        template <typename TargetChar, typename SourceChar>
        struct widest_char
        {
            typedef BOOST_DEDUCED_TYPENAME boost::mpl::if_c<
                (sizeof(TargetChar) > sizeof(SourceChar))
                , TargetChar
                , SourceChar >::type type;
        };
    }
} // namespace boost

#if !defined(BOOST_NO_TEMPLATE_PARTIAL_SPECIALIZATION) && !defined(__SUNPRO_CC)

#include <cmath>
#include <istream>
#include <boost/numeric/conversion/cast.hpp>
#include <boost/type_traits/make_unsigned.hpp>
#include <boost/type_traits/is_signed.hpp>
#include <boost/type_traits/is_integral.hpp>
#include <boost/type_traits/is_arithmetic.hpp>
#include <boost/type_traits/remove_pointer.hpp>
#include <boost/math/special_functions/sign.hpp>
#include <boost/math/special_functions/fpclassify.hpp>
#include <boost/range/iterator_range_core.hpp>
#include <boost/container/container_fwd.hpp>
#ifndef BOOST_NO_CWCHAR
#   include <cwchar>
#endif

namespace boost {
    namespace detail // widest_char<...> (continuation)
    {
        struct not_a_character_type{};

        template <typename CharT>
        struct widest_char<not_a_character_type, CharT >
        {
            typedef CharT type;
        };

        template <typename CharT>
        struct widest_char< CharT, not_a_character_type >
        {
            typedef CharT type;
        };

        template <>
        struct widest_char< not_a_character_type, not_a_character_type >
        {
            typedef char type;
        };
    }

    namespace detail // is_char_or_wchar<...> and stream_char<...> templates
    {
        // returns true, if T is one of the character types
        template <typename T>
        struct is_char_or_wchar
        {
            typedef ::boost::type_traits::ice_or<
                    ::boost::is_same< T, char >::value,
                    #ifndef BOOST_LCAST_NO_WCHAR_T
                        ::boost::is_same< T, wchar_t >::value,
                    #endif
                    #ifndef BOOST_NO_CHAR16_T
                        ::boost::is_same< T, char16_t >::value,
                    #endif
                    #ifndef BOOST_NO_CHAR32_T
                        ::boost::is_same< T, char32_t >::value,
                    #endif
                    ::boost::is_same< T, unsigned char >::value,
                    ::boost::is_same< T, signed char >::value
            > result_type;

            BOOST_STATIC_CONSTANT(bool, value = (result_type::value) );
        };

        // selectors for choosing stream character type
        // returns one of char, wchar_t, char16_t, char32_t or not_a_character_type types
        template <typename Type>
        struct stream_char
        {
            typedef BOOST_DEDUCED_TYPENAME boost::mpl::if_c<
                is_char_or_wchar<Type >::value,
                Type,
                boost::detail::not_a_character_type
            >::type type;
        };

        template <>
        struct stream_char<unsigned char>
        {
            typedef char type;
        };

        template <>
        struct stream_char<signed char>
        {
            typedef char type;
        };

        template<typename CharT>
        struct stream_char<CharT*>
        {
            typedef BOOST_DEDUCED_TYPENAME stream_char<CharT>::type type;
        };

        template<typename CharT>
        struct stream_char<const CharT*>
        {
            typedef BOOST_DEDUCED_TYPENAME stream_char<CharT>::type type;
        };

        template<typename CharT>
        struct stream_char<iterator_range<CharT*> >
        {
            typedef BOOST_DEDUCED_TYPENAME stream_char<CharT*>::type type;
        };

        template<typename CharT>
        struct stream_char<iterator_range<const CharT*> >
        {
            typedef BOOST_DEDUCED_TYPENAME stream_char<const CharT*>::type type;
        };

        template<class CharT, class Traits, class Alloc>
        struct stream_char< std::basic_string<CharT, Traits, Alloc> >
        {
            typedef CharT type;
        };

        template<class CharT, class Traits, class Alloc>
        struct stream_char< ::boost::container::basic_string<CharT, Traits, Alloc> >
        {
            typedef CharT type;
        };

#if !defined(BOOST_LCAST_NO_WCHAR_T) && defined(BOOST_NO_INTRINSIC_WCHAR_T)
        template<>
        struct stream_char<wchar_t>
        {
            typedef boost::detail::not_a_character_type type;
        };

        template<>
        struct stream_char<wchar_t*>
        {
            typedef wchar_t type;
        };

        template<>
        struct stream_char<const wchar_t*>
        {
            typedef wchar_t type;
        };
#endif
    }

    namespace detail // deduce_char_traits template
    {

        template<class CharT, class Target, class Source>
        struct deduce_char_traits
        {
            typedef std::char_traits<CharT> type;
        };

        template<class CharT, class Traits, class Alloc, class Source>
        struct deduce_char_traits< CharT
                                 , std::basic_string<CharT,Traits,Alloc>
                                 , Source
                                 >
        {
            typedef Traits type;
        };

        template<class CharT, class Target, class Traits, class Alloc>
        struct deduce_char_traits< CharT
                                 , Target
                                 , std::basic_string<CharT,Traits,Alloc>
                                 >
        {
            typedef Traits type;
        };

        template<class CharT, class Traits, class Alloc, class Source>
        struct deduce_char_traits< CharT
                                 , ::boost::container::basic_string<CharT,Traits,Alloc>
                                 , Source
                                 >
        {
            typedef Traits type;
        };

        template<class CharT, class Target, class Traits, class Alloc>
        struct deduce_char_traits< CharT
                                 , Target
                                 , ::boost::container::basic_string<CharT,Traits,Alloc>
                                 >
        {
            typedef Traits type;
        };

        template<class CharT, class Traits, class Alloc1, class Alloc2>
        struct deduce_char_traits< CharT
                                 , std::basic_string<CharT,Traits,Alloc1>
                                 , std::basic_string<CharT,Traits,Alloc2>
                                 >
        {
            typedef Traits type;
        };

        template<class CharT, class Traits, class Alloc1, class Alloc2>
        struct deduce_char_traits< CharT
                                 , ::boost::container::basic_string<CharT,Traits,Alloc1>
                                 , ::boost::container::basic_string<CharT,Traits,Alloc2>
                                 >
        {
            typedef Traits type;
        };

        template<class CharT, class Traits, class Alloc1, class Alloc2>
        struct deduce_char_traits< CharT
                                 , ::boost::container::basic_string<CharT,Traits,Alloc1>
                                 , ::std::basic_string<CharT,Traits,Alloc2>
                                 >
        {
            typedef Traits type;
        };

        template<class CharT, class Traits, class Alloc1, class Alloc2>
        struct deduce_char_traits< CharT
                                 , ::std::basic_string<CharT,Traits,Alloc1>
                                 , ::boost::container::basic_string<CharT,Traits,Alloc2>
                                 >
        {
            typedef Traits type;
        };
    }

    namespace detail // lcast_src_length
    {
        // Return max. length of string representation of Source;
        template< class Source // Source type of lexical_cast.
                >
        struct lcast_src_length
        {
            BOOST_STATIC_CONSTANT(std::size_t, value = 1);
            // To check coverage, build the test with
            // bjam --v2 profile optimization=off
            static void check_coverage() {}
        };

        // Helper for integral types.
        // Notes on length calculation:
        // Max length for 32bit int with grouping "\1" and thousands_sep ',':
        // "-2,1,4,7,4,8,3,6,4,7"
        //  ^                    - is_signed
        //   ^                   - 1 digit not counted by digits10
        //    ^^^^^^^^^^^^^^^^^^ - digits10 * 2
        //
        // Constant is_specialized is used instead of constant 1
        // to prevent buffer overflow in a rare case when
        // <boost/limits.hpp> doesn't add missing specialization for
        // numeric_limits<T> for some integral type T.
        // When is_specialized is false, the whole expression is 0.
        template<class Source>
        struct lcast_src_length_integral
        {
#ifndef BOOST_NO_LIMITS_COMPILE_TIME_CONSTANTS
            BOOST_STATIC_CONSTANT(std::size_t, value =
                  std::numeric_limits<Source>::is_signed +
                  std::numeric_limits<Source>::is_specialized + /* == 1 */
                  std::numeric_limits<Source>::digits10 * 2
              );
#else
            BOOST_STATIC_CONSTANT(std::size_t, value = 156);
            BOOST_STATIC_ASSERT(sizeof(Source) * CHAR_BIT <= 256);
#endif
        };

#define BOOST_LCAST_DEF(T)               \
    template<> struct lcast_src_length<T> \
        : lcast_src_length_integral<T>           \
    { static void check_coverage() {} };

        BOOST_LCAST_DEF(short)
        BOOST_LCAST_DEF(unsigned short)
        BOOST_LCAST_DEF(int)
        BOOST_LCAST_DEF(unsigned int)
        BOOST_LCAST_DEF(long)
        BOOST_LCAST_DEF(unsigned long)
#if defined(BOOST_HAS_LONG_LONG)
        BOOST_LCAST_DEF(boost::ulong_long_type)
        BOOST_LCAST_DEF(boost::long_long_type )
#elif defined(BOOST_HAS_MS_INT64)
        BOOST_LCAST_DEF(unsigned __int64)
        BOOST_LCAST_DEF(         __int64)
#endif

#undef BOOST_LCAST_DEF

#ifndef BOOST_LCAST_NO_COMPILE_TIME_PRECISION
        // Helper for floating point types.
        // -1.23456789e-123456
        // ^                   sign
        //  ^                  leading digit
        //   ^                 decimal point
        //    ^^^^^^^^         lcast_precision<Source>::value
        //            ^        "e"
        //             ^       exponent sign
        //              ^^^^^^ exponent (assumed 6 or less digits)
        // sign + leading digit + decimal point + "e" + exponent sign == 5
        template<class Source>
        struct lcast_src_length_floating
        {
            BOOST_STATIC_ASSERT(
                    std::numeric_limits<Source>::max_exponent10 <=  999999L &&
                    std::numeric_limits<Source>::min_exponent10 >= -999999L
                );
            BOOST_STATIC_CONSTANT(std::size_t, value =
                    5 + lcast_precision<Source>::value + 6
                );
        };

        template<>
        struct lcast_src_length<float>
          : lcast_src_length_floating<float>
        {
            static void check_coverage() {}
        };

        template<>
        struct lcast_src_length<double>
          : lcast_src_length_floating<double>
        {
            static void check_coverage() {}
        };

        template<>
        struct lcast_src_length<long double>
          : lcast_src_length_floating<long double>
        {
            static void check_coverage() {}
        };

#endif // #ifndef BOOST_LCAST_NO_COMPILE_TIME_PRECISION
    }

    namespace detail // '0', '+' and '-' constants
    {
        template<typename CharT> struct lcast_char_constants;

        template<>
        struct lcast_char_constants<char>
        {
            BOOST_STATIC_CONSTANT(char, zero  = '0');
            BOOST_STATIC_CONSTANT(char, minus = '-');
            BOOST_STATIC_CONSTANT(char, plus = '+');
            BOOST_STATIC_CONSTANT(char, lowercase_e = 'e');
            BOOST_STATIC_CONSTANT(char, capital_e = 'E');
            BOOST_STATIC_CONSTANT(char, c_decimal_separator = '.');
        };

#ifndef BOOST_LCAST_NO_WCHAR_T
        template<>
        struct lcast_char_constants<wchar_t>
        {
            BOOST_STATIC_CONSTANT(wchar_t, zero  = L'0');
            BOOST_STATIC_CONSTANT(wchar_t, minus = L'-');
            BOOST_STATIC_CONSTANT(wchar_t, plus = L'+');
            BOOST_STATIC_CONSTANT(wchar_t, lowercase_e = L'e');
            BOOST_STATIC_CONSTANT(wchar_t, capital_e = L'E');
            BOOST_STATIC_CONSTANT(wchar_t, c_decimal_separator = L'.');
        };
#endif

#if !defined(BOOST_NO_CHAR16_T) && !defined(BOOST_NO_UNICODE_LITERALS)
        template<>
        struct lcast_char_constants<char16_t>
        {
            BOOST_STATIC_CONSTANT(char16_t, zero  = u'0');
            BOOST_STATIC_CONSTANT(char16_t, minus = u'-');
            BOOST_STATIC_CONSTANT(char16_t, plus = u'+');
            BOOST_STATIC_CONSTANT(char16_t, lowercase_e = u'e');
            BOOST_STATIC_CONSTANT(char16_t, capital_e = u'E');
            BOOST_STATIC_CONSTANT(char16_t, c_decimal_separator = u'.');
        };
#endif

#if !defined(BOOST_NO_CHAR32_T) && !defined(BOOST_NO_UNICODE_LITERALS)
        template<>
        struct lcast_char_constants<char32_t>
        {
            BOOST_STATIC_CONSTANT(char32_t, zero  = U'0');
            BOOST_STATIC_CONSTANT(char32_t, minus = U'-');
            BOOST_STATIC_CONSTANT(char32_t, plus = U'+');
            BOOST_STATIC_CONSTANT(char32_t, lowercase_e = U'e');
            BOOST_STATIC_CONSTANT(char32_t, capital_e = U'E');
            BOOST_STATIC_CONSTANT(char32_t, c_decimal_separator = U'.');
        };
#endif
    }

    namespace detail // lcast_to_unsigned
    {
#if (defined _MSC_VER)
# pragma warning( push )
// C4146: unary minus operator applied to unsigned type, result still unsigned
# pragma warning( disable : 4146 )
#elif defined( __BORLANDC__ )
# pragma option push -w-8041
#endif
        template<class T>
        inline
        BOOST_DEDUCED_TYPENAME make_unsigned<T>::type lcast_to_unsigned(T value)
        {
            typedef BOOST_DEDUCED_TYPENAME make_unsigned<T>::type result_type;
            result_type uvalue = static_cast<result_type>(value);
            return value < 0 ? -uvalue : uvalue;
        }
#if (defined _MSC_VER)
# pragma warning( pop )
#elif defined( __BORLANDC__ )
# pragma option pop
#endif
    }

    namespace detail // lcast_put_unsigned
    {
        template<class Traits, class T, class CharT>
        CharT* lcast_put_unsigned(const T n_param, CharT* finish)
        {
#ifndef BOOST_NO_LIMITS_COMPILE_TIME_CONSTANTS
            BOOST_STATIC_ASSERT(!std::numeric_limits<T>::is_signed);
#endif

            typedef typename Traits::int_type int_type;
            CharT const czero = lcast_char_constants<CharT>::zero;
            int_type const zero = Traits::to_int_type(czero);
            BOOST_DEDUCED_TYPENAME boost::mpl::if_c<
                    (sizeof(int_type) > sizeof(T))
                    , int_type
                    , T
            >::type n = n_param;

#ifndef BOOST_LEXICAL_CAST_ASSUME_C_LOCALE
            std::locale loc;
            if (loc != std::locale::classic()) {
                typedef std::numpunct<CharT> numpunct;
                numpunct const& np = BOOST_USE_FACET(numpunct, loc);
                std::string const grouping = np.grouping();
                std::string::size_type const grouping_size = grouping.size();

                if ( grouping_size && grouping[0] > 0 )
                {

#ifndef BOOST_NO_LIMITS_COMPILE_TIME_CONSTANTS
                // Check that ulimited group is unreachable:
                BOOST_STATIC_ASSERT(std::numeric_limits<T>::digits10 < CHAR_MAX);
#endif
                    CharT thousands_sep = np.thousands_sep();
                    std::string::size_type group = 0; // current group number
                    char last_grp_size = grouping[0];
                    char left = last_grp_size;

                    do
                    {
                        if(left == 0)
                        {
                            ++group;
                            if(group < grouping_size)
                            {
                                char const grp_size = grouping[group];
                                last_grp_size = grp_size <= 0 ? CHAR_MAX : grp_size;
                            }

                            left = last_grp_size;
                            --finish;
                            Traits::assign(*finish, thousands_sep);
                        }

                        --left;

                        --finish;
                        int_type const digit = static_cast<int_type>(n % 10U);
                        Traits::assign(*finish, Traits::to_char_type(zero + digit));
                        n /= 10;
                    } while(n);
                    return finish;
                }
            }
#endif
            {
                do
                {
                    --finish;
                    int_type const digit = static_cast<int_type>(n % 10U);
                    Traits::assign(*finish, Traits::to_char_type(zero + digit));
                    n /= 10;
                } while(n);
            }

            return finish;
        }
    }

    namespace detail // lcast_ret_unsigned
    {
        template<class Traits, class T, class CharT>
        inline bool lcast_ret_unsigned(T& value, const CharT* const begin, const CharT* end)
        {
#ifndef BOOST_NO_LIMITS_COMPILE_TIME_CONSTANTS
            BOOST_STATIC_ASSERT(!std::numeric_limits<T>::is_signed);
#endif
            typedef typename Traits::int_type int_type;
            CharT const czero = lcast_char_constants<CharT>::zero;
            --end;
            value = 0;

            if (begin > end || *end < czero || *end >= czero + 10)
                return false;
            value = *end - czero;
            --end;
            T multiplier = 1;
            bool multiplier_overflowed = false;

#ifndef BOOST_LEXICAL_CAST_ASSUME_C_LOCALE
            std::locale loc;
            if (loc != std::locale::classic()) {
                typedef std::numpunct<CharT> numpunct;
                numpunct const& np = BOOST_USE_FACET(numpunct, loc);
                std::string const& grouping = np.grouping();
                std::string::size_type const grouping_size = grouping.size();

                /* According to Programming languages - C++
                 * we MUST check for correct grouping
                 */
                if (grouping_size && grouping[0] > 0)
                {
                    unsigned char current_grouping = 0;
                    CharT const thousands_sep = np.thousands_sep();
                    char remained = grouping[current_grouping] - 1;
                    bool shall_we_return = true;

                    for(;end>=begin; --end)
                    {
                        if (remained) {
                            T const multiplier_10 = multiplier * 10;
                            if (multiplier_10 / 10 != multiplier) multiplier_overflowed = true;

                            T const dig_value = *end - czero;
                            T const new_sub_value = multiplier_10 * dig_value;

                            if (*end < czero || *end >= czero + 10
                                    /* detecting overflow */
                                    || (dig_value && new_sub_value / dig_value != multiplier_10)
                                    || static_cast<T>((std::numeric_limits<T>::max)()-new_sub_value) < value
                                    || (multiplier_overflowed && dig_value)
                                    )
                                return false;

                            value += new_sub_value;
                            multiplier *= 10;
                            --remained;
                        } else {
                            if ( !Traits::eq(*end, thousands_sep) ) //|| begin == end ) return false;
                            {
                                /*
                                 * According to Programming languages - C++
                                 * Digit grouping is checked. That is, the positions of discarded
                                 * separators is examined for consistency with
                                 * use_facet<numpunct<charT> >(loc ).grouping()
                                 *
                                 * BUT what if there is no separators at all and grouping()
                                 * is not empty? Well, we have no extraced separators, so we
                                 * won`t check them for consistency. This will allow us to
                                 * work with "C" locale from other locales
                                 */
                                shall_we_return = false;
                                break;
                            } else {
                                if ( begin == end ) return false;
                                if (current_grouping < grouping_size-1 ) ++current_grouping;
                                remained = grouping[current_grouping];
                            }
                        }
                    }

                    if (shall_we_return) return true;
                }
            }
#endif
            {
                while ( begin <= end )
                {
                    T const multiplier_10 = multiplier * 10;
                    if (multiplier_10 / 10 != multiplier) multiplier_overflowed = true;

                    T const dig_value = *end - czero;
                    T const new_sub_value = multiplier_10 * dig_value;

                    if (*end < czero || *end >= czero + 10
                            /* detecting overflow */
                            || (dig_value && new_sub_value / dig_value != multiplier_10)
                            || static_cast<T>((std::numeric_limits<T>::max)()-new_sub_value) < value
                            || (multiplier_overflowed && dig_value)
                            )
                        return false;

                    value += new_sub_value;
                    multiplier *= 10;
                    --end;
                }
            }
            return true;
        }
    }

    namespace detail
    {
        template <class CharT>
        bool lc_iequal(const CharT* val, const CharT* lcase, const CharT* ucase, unsigned int len) {
            for( unsigned int i=0; i < len; ++i ) {
                if ( val[i] != lcase[i] && val[i] != ucase[i] ) return false;
            }

            return true;
        }

        /* Returns true and sets the correct value if found NaN or Inf. */
        template <class CharT, class T>
        inline bool parse_inf_nan_impl(const CharT* begin, const CharT* end, T& value
            , const CharT* lc_NAN, const CharT* lc_nan
            , const CharT* lc_INFINITY, const CharT* lc_infinity
            , const CharT opening_brace, const CharT closing_brace)
        {
            using namespace std;
            if (begin == end) return false;
            const CharT minus = lcast_char_constants<CharT>::minus;
            const CharT plus = lcast_char_constants<CharT>::plus;
            const int inifinity_size = 8;

            bool has_minus = false;
            /* Parsing +/- */
            if( *begin == minus)
            {
                ++ begin;
                has_minus = true;
            }
            else if( *begin == plus ) ++begin;

            if( end-begin < 3 ) return false;
            if( lc_iequal(begin, lc_nan, lc_NAN, 3) )
            {
                begin += 3;
                if (end != begin) /* It is 'nan(...)' or some bad input*/
                {
                    if(end-begin<2) return false; // bad input
                    -- end;
                    if( *begin != opening_brace || *end != closing_brace) return false; // bad input
                }

                if( !has_minus ) value = std::numeric_limits<T>::quiet_NaN();
                else value = (boost::math::changesign) (std::numeric_limits<T>::quiet_NaN());
                return true;
            } else
            if (( /* 'INF' or 'inf' */
                  end-begin==3
                  &&
                  lc_iequal(begin, lc_infinity, lc_INFINITY, 3)
                )
                ||
                ( /* 'INFINITY' or 'infinity' */
                  end-begin==inifinity_size
                  &&
                  lc_iequal(begin, lc_infinity, lc_INFINITY, inifinity_size)
                )
             )
            {
                if( !has_minus ) value = std::numeric_limits<T>::infinity();
                else value = (boost::math::changesign) (std::numeric_limits<T>::infinity());
                return true;
            }

            return false;
        }

        template <class CharT, class T>
        bool put_inf_nan_impl(CharT* begin, CharT*& end, const T& value
                         , const CharT* lc_nan
                         , const CharT* lc_infinity)
        {
            using namespace std;
            const CharT minus = lcast_char_constants<CharT>::minus;
            if ( (boost::math::isnan)(value) )
            {
                if ( (boost::math::signbit)(value) )
                {
                    *begin = minus;
                    ++ begin;
                }

                memcpy(begin, lc_nan, 3 * sizeof(CharT));
                end = begin + 3;
                return true;
            } else if ( (boost::math::isinf)(value) )
            {
                if ( (boost::math::signbit)(value) )
                {
                    *begin = minus;
                    ++ begin;
                }

                memcpy(begin, lc_infinity, 3 * sizeof(CharT));
                end = begin + 3;
                return true;
            }

            return false;
        }


#ifndef BOOST_LCAST_NO_WCHAR_T
        template <class T>
        bool parse_inf_nan(const wchar_t* begin, const wchar_t* end, T& value)
        {
            return parse_inf_nan_impl(begin, end, value
                               , L"NAN", L"nan"
                               , L"INFINITY", L"infinity"
                               , L'(', L')');
        }

        template <class T>
        bool put_inf_nan(wchar_t* begin, wchar_t*& end, const T& value)
        {
            return put_inf_nan_impl(begin, end, value, L"nan", L"infinity");
        }

#endif
#if !defined(BOOST_NO_CHAR16_T) && !defined(BOOST_NO_UNICODE_LITERALS)
        template <class T>
        bool parse_inf_nan(const char16_t* begin, const char16_t* end, T& value)
        {
            return parse_inf_nan_impl(begin, end, value
                               , u"NAN", u"nan"
                               , u"INFINITY", u"infinity"
                               , u'(', u')');
        }

        template <class T>
        bool put_inf_nan(char16_t* begin, char16_t*& end, const T& value)
        {
            return put_inf_nan_impl(begin, end, value, u"nan", u"infinity");
        }
#endif
#if !defined(BOOST_NO_CHAR32_T) && !defined(BOOST_NO_UNICODE_LITERALS)
        template <class T>
        bool parse_inf_nan(const char32_t* begin, const char32_t* end, T& value)
        {
            return parse_inf_nan_impl(begin, end, value
                               , U"NAN", U"nan"
                               , U"INFINITY", U"infinity"
                               , U'(', U')');
        }

        template <class T>
        bool put_inf_nan(char32_t* begin, char32_t*& end, const T& value)
        {
            return put_inf_nan_impl(begin, end, value, U"nan", U"infinity");
        }
#endif

        template <class CharT, class T>
        bool parse_inf_nan(const CharT* begin, const CharT* end, T& value)
        {
            return parse_inf_nan_impl(begin, end, value
                               , "NAN", "nan"
                               , "INFINITY", "infinity"
                               , '(', ')');
        }

        template <class CharT, class T>
        bool put_inf_nan(CharT* begin, CharT*& end, const T& value)
        {
            return put_inf_nan_impl(begin, end, value, "nan", "infinity");
        }
    }


    namespace detail // lcast_ret_float
    {
        template <class T>
        struct mantissa_holder_type
        {
            /* Can not be used with this type */
        };

        template <>
        struct mantissa_holder_type<float>
        {
            typedef unsigned int type;
        };

        template <>
        struct mantissa_holder_type<double>
        {
#if defined(BOOST_HAS_LONG_LONG)
            typedef boost::ulong_long_type type;
#elif defined(BOOST_HAS_MS_INT64)
            typedef unsigned __int64 type;
#endif
        };

        template<class Traits, class T, class CharT>
        inline bool lcast_ret_float(T& value, const CharT* begin, const CharT* end)
        {

#ifndef BOOST_LEXICAL_CAST_ASSUME_C_LOCALE
            std::locale loc;
            typedef std::numpunct<CharT> numpunct;
            numpunct const& np = BOOST_USE_FACET(numpunct, loc);
            std::string const grouping(
                    (loc == std::locale::classic())
                    ? std::string()
                    : np.grouping()
            );
            std::string::size_type const grouping_size = grouping.size();
            CharT const thousands_sep = grouping_size ? np.thousands_sep() : 0;
            CharT const decimal_point = np.decimal_point();
            bool found_grouping = false;
            std::string::size_type last_grouping_pos = grouping_size - 1;
#else
            CharT const decimal_point = lcast_char_constants<CharT>::c_decimal_separator;
#endif

            CharT const czero = lcast_char_constants<CharT>::zero;
            CharT const minus = lcast_char_constants<CharT>::minus;
            CharT const plus = lcast_char_constants<CharT>::plus;
            CharT const capital_e = lcast_char_constants<CharT>::capital_e;
            CharT const lowercase_e = lcast_char_constants<CharT>::lowercase_e;

            value = static_cast<T>(0);

            if (parse_inf_nan(begin, end, value)) return true;

            typedef typename Traits::int_type int_type;
            typedef BOOST_DEDUCED_TYPENAME mantissa_holder_type<T>::type mantissa_type;
            int_type const zero = Traits::to_int_type(czero);
            if (begin == end) return false;

            /* Getting the plus/minus sign */
            bool has_minus = false;
            if ( *begin == minus ) {
                ++ begin;
                has_minus = true;
                if (begin == end) return false;
            } else if ( *begin == plus ) {
                ++begin;
                if (begin == end) return false;
            }

            bool found_decimal = false;
            bool found_number_before_exp = false;
            int pow_of_10 = 0;
            mantissa_type mantissa=0;
            bool is_mantissa_full = false;

            char length_since_last_delim = 0;

            while ( begin != end )
            {
                if (found_decimal) {
                    /* We allow no thousand_separators after decimal point */

                    mantissa_type tmp_mantissa = mantissa * 10u;
                    if ( *begin == lowercase_e || *begin == capital_e ) break;
                    if ( *begin < czero || *begin >= czero + 10 ) return false;
                    if (    is_mantissa_full
                            || tmp_mantissa / 10u != mantissa
                            || (std::numeric_limits<mantissa_type>::max)()-(*begin - zero) < tmp_mantissa
                            ) {
                        is_mantissa_full = true;
                        ++ begin;
                        continue;
                    }

                    -- pow_of_10;
                    mantissa = tmp_mantissa;
                    mantissa += *begin - zero;

                    found_number_before_exp = true;
                } else {

                    if (*begin >= czero && *begin < czero + 10) {

                        /* Checking for mantissa overflow. If overflow will
                         * occur, them we only increase multiplyer
                         */
                        mantissa_type tmp_mantissa = mantissa * 10u;
                        if(     !is_mantissa_full
                                && tmp_mantissa / 10u == mantissa
                                && (std::numeric_limits<mantissa_type>::max)()-(*begin - zero) >= tmp_mantissa
                            )
                        {
                            mantissa = tmp_mantissa;
                            mantissa += *begin - zero;
                        } else
                        {
                            is_mantissa_full = true;
                            ++ pow_of_10;
                        }

                        found_number_before_exp = true;
                        ++ length_since_last_delim;
                    } else if ( *begin == decimal_point || *begin == lowercase_e || *begin == capital_e) {
#ifndef BOOST_LEXICAL_CAST_ASSUME_C_LOCALE
                        /* If ( we need to check grouping
                         *      and (   grouping missmatches
                         *              or grouping position is incorrect
                         *              or we are using the grouping position 0 twice
                         *           )
                         *    ) then return error
                         */
                        if( grouping_size && found_grouping
                            && (
                                   length_since_last_delim != grouping[0]
                                   || last_grouping_pos>1
                                   || (last_grouping_pos==0 && grouping_size>1)
                                )
                           ) return false;
#endif

                        if(*begin == decimal_point) {
                            ++ begin;
                            found_decimal = true;
                            if (!found_number_before_exp && begin==end) return false;
                            continue;
                        }else {
                            if (!found_number_before_exp) return false;
                            break;
                        }
                    }
#ifndef BOOST_LEXICAL_CAST_ASSUME_C_LOCALE
                    else if (grouping_size && *begin == thousands_sep){
                        if(found_grouping)
                        {
                            /* It is not he first time, when we find thousands separator,
                             * so we need to chek, is the distance between two groupings
                             * equal to grouping[last_grouping_pos] */

                            if (length_since_last_delim != grouping[last_grouping_pos] )
                            {
                                if (!last_grouping_pos) return false;
                                else
                                {
                                    -- last_grouping_pos;
                                    if (length_since_last_delim != grouping[last_grouping_pos]) return false;
                                }
                            } else
                                /* We are calling the grouping[0] twice, when grouping size is more than 1 */
                                if (grouping_size>1u && last_grouping_pos+1<grouping_size) return false;

                        } else {
                            /* Delimiter at the begining ',000' */
                            if (!length_since_last_delim) return false;

                            found_grouping = true;
                            if (length_since_last_delim > grouping[last_grouping_pos] ) return false;
                        }

                        length_since_last_delim = 0;
                        ++ begin;

                        /* Delimiter at the end '100,' */
                        if (begin == end) return false;
                        continue;
                    }
#endif
                    else return false;
                }

                ++begin;
            }

            // Exponent found
            if ( begin != end && ( *begin == lowercase_e || *begin == capital_e ) ) {
                ++ begin;
                if ( begin == end ) return false;

                bool exp_has_minus = false;
                if( *begin == minus ) {
                    exp_has_minus = true;
                    ++ begin;
                    if ( begin == end ) return false;
                } else if (*begin == plus ) {
                    ++ begin;
                    if ( begin == end ) return false;
                }

                int exp_pow_of_10 = 0;
                while ( begin != end )
                {
                    if ( *begin < czero
                            || *begin >= czero + 10
                            || exp_pow_of_10 * 10 < exp_pow_of_10) /* Overflows are checked lower more precisely*/
                        return false;

                    exp_pow_of_10 *= 10;
                    exp_pow_of_10 += *begin - zero;
                    ++ begin;
                };

                if ( exp_pow_of_10 ) {
                    /* Overflows are checked lower */
                    if ( exp_has_minus ) {
                        pow_of_10 -= exp_pow_of_10;
                    } else {
                        pow_of_10 += exp_pow_of_10;
                    }
                }
            }

            /* We need a more accurate algorithm... We can not use current algorithm
             * with long doubles (and with doubles if sizeof(double)==sizeof(long double)).
             */
            long double result = std::pow(10.0L, pow_of_10) * mantissa;
            value = static_cast<T>( has_minus ? (boost::math::changesign)(result) : result);

            if ( (boost::math::isinf)(value) || (boost::math::isnan)(value) ) return false;

            return true;
        }
    }

    namespace detail // stl_buf_unlocker
    {
        template< class BufferType, class CharT >
        class stl_buf_unlocker: public BufferType{
        public:
            typedef BufferType base_class;
#ifndef BOOST_NO_USING_TEMPLATE
            using base_class::pptr;
            using base_class::pbase;
            using base_class::setg;
            using base_class::setp;
#else
            CharT* pptr() const { return base_class::pptr(); }
            CharT* pbase() const { return base_class::pbase(); }
            void setg(CharT* gbeg, CharT* gnext, CharT* gend){ return base_class::setg(gbeg, gnext, gend); }
            void setp(CharT* pbeg, CharT* pend) { return setp(pbeg, pend); }
#endif
        };
    }

    namespace detail
    {
        struct do_not_construct_out_stream_t{};
    }

    namespace detail // optimized stream wrapper
    {
        // String representation of Source has an upper limit.
        template< class CharT // a result of widest_char transformation
                , class Traits // usually char_traits<CharT>
                , bool RequiresStringbuffer
                >
        class lexical_stream_limited_src
        {

#if defined(BOOST_NO_STRINGSTREAM)
            typedef std::ostrstream                         out_stream_t;
            typedef stl_buf_unlocker<std::strstreambuf, char>  unlocked_but_t;
#elif defined(BOOST_NO_STD_LOCALE)
            typedef std::ostringstream                      out_stream_t;
            typedef stl_buf_unlocker<std::stringbuf, char>  unlocked_but_t;
#else
            typedef std::basic_ostringstream<CharT, Traits>       out_stream_t;
            typedef stl_buf_unlocker<std::basic_stringbuf<CharT, Traits>, CharT> unlocked_but_t;
#endif
            typedef BOOST_DEDUCED_TYPENAME ::boost::mpl::if_c<
                RequiresStringbuffer,
                out_stream_t,
                do_not_construct_out_stream_t
            >::type deduced_out_stream_t;

            // A string representation of Source is written to [start, finish).
            CharT* start;
            CharT* finish;
            deduced_out_stream_t out_stream;

        public:
            lexical_stream_limited_src(CharT* sta, CharT* fin)
              : start(sta)
              , finish(fin)
            {}

        private:
            // Undefined:
            lexical_stream_limited_src(lexical_stream_limited_src const&);
            void operator=(lexical_stream_limited_src const&);

/************************************ HELPER FUNCTIONS FOR OPERATORS << ( ... ) ********************************/
            bool shl_char(CharT ch)
            {
                Traits::assign(*start, ch);
                finish = start + 1;
                return true;
            }

#ifndef BOOST_LCAST_NO_WCHAR_T
            template <class T>
            bool shl_char(T ch)
            {
                BOOST_STATIC_ASSERT_MSG(( sizeof(T) <= sizeof(CharT)) ,
                    "boost::lexical_cast does not support conversions from wide character to char types."
                    "Use boost::locale instead" );
#ifndef BOOST_LEXICAL_CAST_ASSUME_C_LOCALE
                std::locale loc;
                wchar_t w = BOOST_USE_FACET(std::ctype<wchar_t>, loc).widen(ch);
#else
                wchar_t w = ch;
#endif
                Traits::assign(*start, w);
                finish = start + 1;
                return true;
            }
#endif

            bool shl_char_array(CharT const* str)
            {
                start = const_cast<CharT*>(str);
                finish = start + Traits::length(str);
                return true;
            }

#ifndef BOOST_LCAST_NO_WCHAR_T
            template <class T>
            bool shl_char_array(T const* str)
            {
                BOOST_STATIC_ASSERT_MSG(( sizeof(T) <= sizeof(CharT)),
                    "boost::lexical_cast does not support conversions from wide characters to char types."
                    "Use boost::locale instead" );
                return shl_input_streamable(str);
            }
#endif

            template<typename InputStreamable>
            bool shl_input_streamable(InputStreamable& input)
            {
#if defined(BOOST_NO_STRINGSTREAM) || defined(BOOST_NO_STD_LOCALE)
                // If you have compilation error at this point, than your STL library
                // does not support such conversions. Try updating it.
                BOOST_STATIC_ASSERT((boost::is_same<char, CharT>::value));
#endif
                bool const result = !(out_stream << input).fail();
                const unlocked_but_t* const p
                        = static_cast<unlocked_but_t*>(out_stream.rdbuf()) ;
                start = p->pbase();
                finish = p->pptr();
                return result;
            }

            template <class T>
            inline bool shl_signed(T n)
            {
                start = lcast_put_unsigned<Traits>(lcast_to_unsigned(n), finish);
                if(n < 0)
                {
                    --start;
                    CharT const minus = lcast_char_constants<CharT>::minus;
                    Traits::assign(*start, minus);
                }
                return true;
            }

            template <class T, class SomeCharT>
            bool shl_real_type(const T& val, SomeCharT* begin, SomeCharT*& end)
            {
                if (put_inf_nan(begin, end, val)) return true;
                lcast_set_precision(out_stream, &val);
                return shl_input_streamable(val);
            }

#if (defined _MSC_VER)
# pragma warning( push )
// C4996: This function or variable may be unsafe. Consider using sprintf_s instead
# pragma warning( disable : 4996 )
#endif
            static bool shl_real_type(float val, char* begin, char*& end)
            {   using namespace std;
                if (put_inf_nan(begin, end, val)) return true;
                end = begin;
                const double val_as_double = val;
                end += sprintf(begin,"%.*g", static_cast<int>(boost::detail::lcast_get_precision<float>()), val_as_double);
                return end > begin;
            }

            static bool shl_real_type(double val, char* begin, char*& end)
            {   using namespace std;
                if (put_inf_nan(begin, end, val)) return true;
                end = begin;
                end += sprintf(begin,"%.*g", static_cast<int>(boost::detail::lcast_get_precision<double>()), val);
                return end > begin;
            }

#ifndef __MINGW32__
            static bool shl_real_type(long double val, char* begin, char*& end)
            {   using namespace std;
                if (put_inf_nan(begin, end, val)) return true;
                end = begin;
                end += sprintf(begin,"%.*Lg", static_cast<int>(boost::detail::lcast_get_precision<long double>()), val );
                return end > begin;
            }
#endif

#if (defined _MSC_VER)
# pragma warning( pop )
#endif


#if !defined(BOOST_LCAST_NO_WCHAR_T) && !defined(BOOST_NO_SWPRINTF) && !defined(__MINGW32__)
            static bool shl_real_type(float val, wchar_t* begin, wchar_t*& end)
            {   using namespace std;
                if (put_inf_nan(begin, end, val)) return true;
                const double val_as_double = val;
                end = begin + swprintf(begin, end-begin,
                                       L"%.*g",
                                       static_cast<int>(boost::detail::lcast_get_precision<float >()),
                                       val_as_double );
                return end > begin;
            }

            static bool shl_real_type(double val, wchar_t* begin, wchar_t*& end)
            {   using namespace std;
                if (put_inf_nan(begin, end, val)) return true;
                end = begin + swprintf(begin, end-begin,
                                          L"%.*g", static_cast<int>(boost::detail::lcast_get_precision<double >()), val );
                return end > begin;
            }

            static bool shl_real_type(long double val, wchar_t* begin, wchar_t*& end)
            {   using namespace std;
                if (put_inf_nan(begin, end, val)) return true;
                end = begin + swprintf(begin, end-begin,
                                          L"%.*Lg", static_cast<int>(boost::detail::lcast_get_precision<long double >()), val );
                return end > begin;
            }
#endif

/************************************ OPERATORS << ( ... ) ********************************/
        public:
            template<class Alloc>
            bool operator<<(std::basic_string<CharT,Traits,Alloc> const& str)
            {
                start = const_cast<CharT*>(str.data());
                finish = start + str.length();
                return true;
            }

            template<class Alloc>
            bool operator<<(::boost::container::basic_string<CharT,Traits,Alloc> const& str)
            {
                start = const_cast<CharT*>(str.data());
                finish = start + str.length();
                return true;
            }

            bool operator<<(bool value)
            {
                CharT const czero = lcast_char_constants<CharT>::zero;
                Traits::assign(*start, Traits::to_char_type(czero + value));
                finish = start + 1;
                return true;
            }

            bool operator<<(const iterator_range<CharT*>& rng)
            {
                start = rng.begin();
                finish = rng.end();
                return true;
            }

            bool operator<<(const iterator_range<const CharT*>& rng)
            {
                start = const_cast<CharT*>(rng.begin());
                finish = const_cast<CharT*>(rng.end());
                return true;
            }

            bool operator<<(const iterator_range<const signed char*>& rng)
            {
                return (*this) << iterator_range<char*>(
                    const_cast<char*>(reinterpret_cast<const char*>(rng.begin())),
                    const_cast<char*>(reinterpret_cast<const char*>(rng.end()))
                );
            }

            bool operator<<(const iterator_range<const unsigned char*>& rng)
            {
                return (*this) << iterator_range<char*>(
                    const_cast<char*>(reinterpret_cast<const char*>(rng.begin())),
                    const_cast<char*>(reinterpret_cast<const char*>(rng.end()))
                );
            }

            bool operator<<(const iterator_range<signed char*>& rng)
            {
                return (*this) << iterator_range<char*>(
                    reinterpret_cast<char*>(rng.begin()),
                    reinterpret_cast<char*>(rng.end())
                );
            }

            bool operator<<(const iterator_range<unsigned char*>& rng)
            {
                return (*this) << iterator_range<char*>(
                    reinterpret_cast<char*>(rng.begin()),
                    reinterpret_cast<char*>(rng.end())
                );
            }

            bool operator<<(char ch)                    { return shl_char(ch); }
            bool operator<<(unsigned char ch)           { return ((*this) << static_cast<char>(ch)); }
            bool operator<<(signed char ch)             { return ((*this) << static_cast<char>(ch)); }
#if !defined(BOOST_LCAST_NO_WCHAR_T)
            bool operator<<(wchar_t const* str)         { return shl_char_array(str); }
            bool operator<<(wchar_t * str)              { return shl_char_array(str); }
#ifndef BOOST_NO_INTRINSIC_WCHAR_T
            bool operator<<(wchar_t ch)                 { return shl_char(ch); }
#endif
#endif
#if !defined(BOOST_NO_CHAR16_T) && !defined(BOOST_NO_UNICODE_LITERALS)
            bool operator<<(char16_t ch)                { return shl_char(ch); }
            bool operator<<(char16_t * str)             { return shl_char_array(str); }
            bool operator<<(char16_t const * str)       { return shl_char_array(str); }
#endif
#if !defined(BOOST_NO_CHAR32_T) && !defined(BOOST_NO_UNICODE_LITERALS)
            bool operator<<(char32_t ch)                { return shl_char(ch); }
            bool operator<<(char32_t * str)             { return shl_char_array(str); }
            bool operator<<(char32_t const * str)       { return shl_char_array(str); }
#endif
            bool operator<<(unsigned char const* ch)    { return ((*this) << reinterpret_cast<char const*>(ch)); }
            bool operator<<(unsigned char * ch)         { return ((*this) << reinterpret_cast<char *>(ch)); }
            bool operator<<(signed char const* ch)      { return ((*this) << reinterpret_cast<char const*>(ch)); }
            bool operator<<(signed char * ch)           { return ((*this) << reinterpret_cast<char *>(ch)); }
            bool operator<<(char const* str)            { return shl_char_array(str); }
            bool operator<<(char* str)                  { return shl_char_array(str); }
            bool operator<<(short n)                    { return shl_signed(n); }
            bool operator<<(int n)                      { return shl_signed(n); }
            bool operator<<(long n)                     { return shl_signed(n); }
            bool operator<<(unsigned short n)           { start = lcast_put_unsigned<Traits>(n, finish); return true; }
            bool operator<<(unsigned int n)             { start = lcast_put_unsigned<Traits>(n, finish); return true; }
            bool operator<<(unsigned long n)            { start = lcast_put_unsigned<Traits>(n, finish); return true; }

#if defined(BOOST_HAS_LONG_LONG)
            bool operator<<(boost::ulong_long_type n)   { start = lcast_put_unsigned<Traits>(n, finish); return true; }
            bool operator<<(boost::long_long_type n)    { return shl_signed(n); }
#elif defined(BOOST_HAS_MS_INT64)
            bool operator<<(unsigned __int64 n)         { start = lcast_put_unsigned<Traits>(n, finish); return true; }
            bool operator<<(         __int64 n)         { return shl_signed(n); }
#endif
            bool operator<<(float val)                  { return shl_real_type(val, start, finish); }
            bool operator<<(double val)                 { return shl_real_type(val, start, finish); }
            bool operator<<(long double val)            {
#ifndef __MINGW32__
                return shl_real_type(val, start, finish);
#else
                return shl_real_type(static_cast<double>(val), start, finish);
#endif
            }

            template<class InStreamable>
            bool operator<<(const InStreamable& input)  { return shl_input_streamable(input); }

/************************************ HELPER FUNCTIONS FOR OPERATORS >> ( ... ) ********************************/
        private:

            template <typename Type>
            bool shr_unsigned(Type& output)
            {
                if (start == finish) return false;
                CharT const minus = lcast_char_constants<CharT>::minus;
                CharT const plus = lcast_char_constants<CharT>::plus;
                bool has_minus = false;

                /* We won`t use `start' any more, so no need in decrementing it after */
                if ( Traits::eq(minus,*start) )
                {
                    ++start;
                    has_minus = true;
                } else if ( Traits::eq( plus, *start ) )
                {
                    ++start;
                }

                bool const succeed = lcast_ret_unsigned<Traits>(output, start, finish);
#if (defined _MSC_VER)
# pragma warning( push )
// C4146: unary minus operator applied to unsigned type, result still unsigned
# pragma warning( disable : 4146 )
#elif defined( __BORLANDC__ )
# pragma option push -w-8041
#endif
                if (has_minus) output = static_cast<Type>(-output);
#if (defined _MSC_VER)
# pragma warning( pop )
#elif defined( __BORLANDC__ )
# pragma option pop
#endif
                return succeed;
            }

            template <typename Type>
            bool shr_signed(Type& output)
            {
                if (start == finish) return false;
                CharT const minus = lcast_char_constants<CharT>::minus;
                CharT const plus = lcast_char_constants<CharT>::plus;
                typedef BOOST_DEDUCED_TYPENAME make_unsigned<Type>::type utype;
                utype out_tmp =0;
                bool has_minus = false;

                /* We won`t use `start' any more, so no need in decrementing it after */
                if ( Traits::eq(minus,*start) )
                {
                    ++start;
                    has_minus = true;
                } else if ( Traits::eq(plus, *start) )
                {
                    ++start;
                }

                bool succeed = lcast_ret_unsigned<Traits>(out_tmp, start, finish);
                if (has_minus) {
#if (defined _MSC_VER)
# pragma warning( push )
// C4146: unary minus operator applied to unsigned type, result still unsigned
# pragma warning( disable : 4146 )
#elif defined( __BORLANDC__ )
# pragma option push -w-8041
#endif
                    utype const comp_val = static_cast<utype>(-(std::numeric_limits<Type>::min)());
                    succeed = succeed && out_tmp<=comp_val;
                    output = -out_tmp;
#if (defined _MSC_VER)
# pragma warning( pop )
#elif defined( __BORLANDC__ )
# pragma option pop
#endif
                } else {
                    utype const comp_val = static_cast<utype>((std::numeric_limits<Type>::max)());
                    succeed = succeed && out_tmp<=comp_val;
                    output = out_tmp;
                }
                return succeed;
            }

            template<typename InputStreamable>
            bool shr_using_base_class(InputStreamable& output)
            {
#if (defined _MSC_VER)
# pragma warning( push )
  // conditional expression is constant
# pragma warning( disable : 4127 )
#endif
                if(is_pointer<InputStreamable>::value)
                    return false;

#if defined(BOOST_NO_STRINGSTREAM) || defined(BOOST_NO_STD_LOCALE)
                // If you have compilation error at this point, than your STL library
                // unsupports such conversions. Try updating it.
                BOOST_STATIC_ASSERT((boost::is_same<char, CharT>::value));
#endif

#if defined(BOOST_NO_STRINGSTREAM)
                std::istrstream stream(start, finish - start);
#elif defined(BOOST_NO_STD_LOCALE)
                std::istringstream stream;
#else
                std::basic_istringstream<CharT, Traits> stream;
#endif
                static_cast<unlocked_but_t*>(stream.rdbuf())
                        ->setg(start, start, finish);

                stream.unsetf(std::ios::skipws);
                lcast_set_precision(stream, static_cast<InputStreamable*>(0));
#if (defined _MSC_VER)
# pragma warning( pop )
#endif
                return stream >> output &&
                    stream.get() ==
#if defined(__GNUC__) && (__GNUC__<3) && defined(BOOST_NO_STD_WSTRING)
        // GCC 2.9x lacks std::char_traits<>::eof().
        // We use BOOST_NO_STD_WSTRING to filter out STLport and libstdc++-v3
        // configurations, which do provide std::char_traits<>::eof().

                    EOF;
#else
                Traits::eof();
#endif
            }

            template<class T>
            inline bool shr_xchar(T& output)
            {
                BOOST_STATIC_ASSERT_MSG(( sizeof(CharT) == sizeof(T) ),
                    "boost::lexical_cast does not support conversions from wchar_t to char types."
                    "Use boost::locale instead" );
                bool const ok = (finish - start == 1);
                if(ok) {
                    CharT out;
                    Traits::assign(out, *start);
                    output = static_cast<T>(out);
                }
                return ok;
            }

/************************************ OPERATORS >> ( ... ) ********************************/
            public:
            bool operator>>(unsigned short& output)             { return shr_unsigned(output); }
            bool operator>>(unsigned int& output)               { return shr_unsigned(output); }
            bool operator>>(unsigned long int& output)          { return shr_unsigned(output); }
            bool operator>>(short& output)                      { return shr_signed(output); }
            bool operator>>(int& output)                        { return shr_signed(output); }
            bool operator>>(long int& output)                   { return shr_signed(output); }
#if defined(BOOST_HAS_LONG_LONG)
            bool operator>>(boost::ulong_long_type& output)     { return shr_unsigned(output); }
            bool operator>>(boost::long_long_type& output)      { return shr_signed(output); }
#elif defined(BOOST_HAS_MS_INT64)
            bool operator>>(unsigned __int64& output)           { return shr_unsigned(output); }
            bool operator>>(__int64& output)                    { return shr_signed(output); }
#endif
            bool operator>>(char& output)                       { return shr_xchar(output); }
            bool operator>>(unsigned char& output)              { return shr_xchar(output); }
            bool operator>>(signed char& output)                { return shr_xchar(output); }
#if !defined(BOOST_LCAST_NO_WCHAR_T) && !defined(BOOST_NO_INTRINSIC_WCHAR_T)
            bool operator>>(wchar_t& output)                    { return shr_xchar(output); }
#endif
#if !defined(BOOST_NO_CHAR16_T) && !defined(BOOST_NO_UNICODE_LITERALS)
            bool operator>>(char16_t& output)                   { return shr_xchar(output); }
#endif
#if !defined(BOOST_NO_CHAR32_T) && !defined(BOOST_NO_UNICODE_LITERALS)
            bool operator>>(char32_t& output)                   { return shr_xchar(output); }
#endif
            template<class Alloc>
            bool operator>>(std::basic_string<CharT,Traits,Alloc>& str) { str.assign(start, finish); return true; }

            template<class Alloc>
            bool operator>>(::boost::container::basic_string<CharT,Traits,Alloc>& str) { str.assign(start, finish); return true; }

            /*
             * case "-0" || "0" || "+0" :   output = false; return true;
             * case "1" || "+1":            output = true;  return true;
             * default:                     return false;
             */
            bool operator>>(bool& output)
            {
                CharT const zero = lcast_char_constants<CharT>::zero;
                CharT const plus = lcast_char_constants<CharT>::plus;
                CharT const minus = lcast_char_constants<CharT>::minus;

                switch(finish-start)
                {
                    case 1:
                        output = Traits::eq(start[0],  zero+1);
                        return output || Traits::eq(start[0], zero );
                    case 2:
                        if ( Traits::eq( plus, *start) )
                        {
                            ++start;
                            output = Traits::eq(start[0], zero +1);
                            return output || Traits::eq(start[0], zero );
                        } else
                        {
                            output = false;
                            return Traits::eq( minus, *start)
                                && Traits::eq( zero, start[1]);
                        }
                    default:
                        output = false; // Suppress warning about uninitalized variable
                        return false;
                }
            }

            bool operator>>(float& output) { return lcast_ret_float<Traits>(output,start,finish); }

        private:
            // Not optimised converter
            template <class T>
            bool float_types_converter_internal(T& output, int /*tag*/) {
                if (parse_inf_nan(start, finish, output)) return true;
                bool return_value = shr_using_base_class(output);

                /* Some compilers and libraries successfully
                 * parse 'inf', 'INFINITY', '1.0E', '1.0E-'...
                 * We are trying to provide a unified behaviour,
                 * so we just forbid such conversions (as some
                 * of the most popular compilers/libraries do)
                 * */
                CharT const minus = lcast_char_constants<CharT>::minus;
                CharT const plus = lcast_char_constants<CharT>::plus;
                CharT const capital_e = lcast_char_constants<CharT>::capital_e;
                CharT const lowercase_e = lcast_char_constants<CharT>::lowercase_e;
                if ( return_value &&
                     (
                        *(finish-1) == lowercase_e                   // 1.0e
                        || *(finish-1) == capital_e                  // 1.0E
                        || *(finish-1) == minus                      // 1.0e- or 1.0E-
                        || *(finish-1) == plus                       // 1.0e+ or 1.0E+
                     )
                ) return false;

                return return_value;
            }

            // Optimised converter
            bool float_types_converter_internal(double& output,char /*tag*/) {
                return lcast_ret_float<Traits>(output,start,finish);
            }
        public:

            bool operator>>(double& output)
            {
                /*
                 * Some compilers implement long double as double. In that case these types have
                 * same size, same precision, same max and min values... And it means,
                 * that current implementation of lcast_ret_float cannot be used for type
                 * double, because it will give a big precision loss.
                 * */
                boost::mpl::if_c<
#if defined(BOOST_HAS_LONG_LONG) || defined(BOOST_HAS_MS_INT64)
                    ::boost::type_traits::ice_eq< sizeof(double), sizeof(long double) >::value,
#else
                     0
#endif
                    int,
                    char
                >::type tag = 0;

                return float_types_converter_internal(output, tag);
            }

            bool operator>>(long double& output)
            {
                int tag = 0;
                return float_types_converter_internal(output, tag);
            }

            // Generic istream-based algorithm.
            // lcast_streambuf_for_target<InputStreamable>::value is true.
            template<typename InputStreamable>
            bool operator>>(InputStreamable& output) { return shr_using_base_class(output); }
        };
    }

    namespace detail
    {
        template<class T>
        struct array_to_pointer_decay
        {
            typedef T type;
        };

        template<class T, std::size_t N>
        struct array_to_pointer_decay<T[N]>
        {
            typedef const T * type;
        };

        template<typename T>
        struct is_stdstring
        {
            BOOST_STATIC_CONSTANT(bool, value = false );
        };

        template<typename CharT, typename Traits, typename Alloc>
        struct is_stdstring< std::basic_string<CharT, Traits, Alloc> >
        {
            BOOST_STATIC_CONSTANT(bool, value = true );
        };

        template<typename CharT, typename Traits, typename Alloc>
        struct is_stdstring< ::boost::container::basic_string<CharT, Traits, Alloc> >
        {
            BOOST_STATIC_CONSTANT(bool, value = true );
        };

        template<typename Target, typename Source>
        struct is_arithmetic_and_not_xchars
        {
            BOOST_STATIC_CONSTANT(bool, value =
               (
                   ::boost::type_traits::ice_and<
                           ::boost::is_arithmetic<Source>::value,
                           ::boost::is_arithmetic<Target>::value,
                           ::boost::type_traits::ice_not<
                                detail::is_char_or_wchar<Target>::value
                           >::value,
                           ::boost::type_traits::ice_not<
                                detail::is_char_or_wchar<Source>::value
                           >::value
                   >::value
               )
            );
        };

        /*
         * is_xchar_to_xchar<Target, Source>::value is true, when
         * Target and Souce are the same char types, or when
         * Target and Souce are char types of the same size.
         */
        template<typename Target, typename Source>
        struct is_xchar_to_xchar
        {
            BOOST_STATIC_CONSTANT(bool, value =
                (
                    ::boost::type_traits::ice_or<
                        ::boost::type_traits::ice_and<
                             is_same<Source,Target>::value,
                             is_char_or_wchar<Target>::value
                        >::value,
                        ::boost::type_traits::ice_and<
                             ::boost::type_traits::ice_eq< sizeof(char),sizeof(Target)>::value,
                             ::boost::type_traits::ice_eq< sizeof(char),sizeof(Source)>::value,
                             is_char_or_wchar<Target>::value,
                             is_char_or_wchar<Source>::value
                        >::value
                    >::value
                )
            );
        };


        // this metafunction evaluates to true, if we have optimized comnversion
        // from Float type to Char array.
        // Must be in sync with lexical_stream_limited_src<Char, ...>::shl_real_type(...)
        template <typename Float, typename Char>
        struct is_this_float_conversion_optimized
        {
            typedef ::boost::type_traits::ice_and<
                ::boost::is_float<Float>::value,
#if !defined(BOOST_LCAST_NO_WCHAR_T) && !defined(BOOST_NO_SWPRINTF) && !defined(__MINGW32__)
                ::boost::type_traits::ice_or<
                    ::boost::type_traits::ice_eq<sizeof(Char), sizeof(char) >::value,
                    ::boost::is_same<Char, wchar_t>::value
                >::value
#else
                ::boost::type_traits::ice_eq<sizeof(Char), sizeof(char) >::value
#endif
            > result_type;

            BOOST_STATIC_CONSTANT(bool, value = (result_type::value) );
        };

        template<typename Target, typename Source>
        struct is_char_array_to_stdstring
        {
            BOOST_STATIC_CONSTANT(bool, value = false );
        };

        template<typename CharT, typename Traits, typename Alloc>
        struct is_char_array_to_stdstring< std::basic_string<CharT, Traits, Alloc>, CharT* >
        {
            BOOST_STATIC_CONSTANT(bool, value = true );
        };

        template<typename CharT, typename Traits, typename Alloc>
        struct is_char_array_to_stdstring< std::basic_string<CharT, Traits, Alloc>, const CharT* >
        {
            BOOST_STATIC_CONSTANT(bool, value = true );
        };

        template<typename CharT, typename Traits, typename Alloc>
        struct is_char_array_to_stdstring< ::boost::container::basic_string<CharT, Traits, Alloc>, CharT* >
        {
            BOOST_STATIC_CONSTANT(bool, value = true );
        };

        template<typename CharT, typename Traits, typename Alloc>
        struct is_char_array_to_stdstring< ::boost::container::basic_string<CharT, Traits, Alloc>, const CharT* >
        {
            BOOST_STATIC_CONSTANT(bool, value = true );
        };

#if (defined _MSC_VER)
# pragma warning( push )
# pragma warning( disable : 4701 ) // possible use of ... before initialization
# pragma warning( disable : 4702 ) // unreachable code
# pragma warning( disable : 4267 ) // conversion from 'size_t' to 'unsigned int'
#endif
        template<typename Target, typename Source>
        struct lexical_cast_do_cast
        {
            static inline Target lexical_cast_impl(const Source& arg)
            {
                typedef BOOST_DEDUCED_TYPENAME detail::array_to_pointer_decay<Source>::type src;
                typedef BOOST_DEDUCED_TYPENAME detail::stream_char<Target>::type target_char_t;
                typedef BOOST_DEDUCED_TYPENAME detail::stream_char<src>::type src_char_type;
                typedef BOOST_DEDUCED_TYPENAME detail::widest_char<
                    target_char_t, src_char_type
                >::type char_type;

#if !defined(BOOST_NO_CHAR16_T) && defined(BOOST_NO_UNICODE_LITERALS)
                BOOST_STATIC_ASSERT_MSG(( !::boost::is_same<char16_t, src_char_type>::value
                                          && !::boost::is_same<char16_t, target_char_t>::value),
                    "Your compiler does not have full support for char16_t" );
#endif
#if !defined(BOOST_NO_CHAR32_T) && defined(BOOST_NO_UNICODE_LITERALS)
                BOOST_STATIC_ASSERT_MSG(( !::boost::is_same<char32_t, src_char_type>::value
                                          && !::boost::is_same<char32_t, target_char_t>::value),
                    "Your compiler does not have full support for char32_t" );
#endif

                typedef detail::lcast_src_length<src > lcast_src_length;
                std::size_t const src_len = lcast_src_length::value;
                char_type buf[src_len + 1];
                lcast_src_length::check_coverage();

                typedef BOOST_DEDUCED_TYPENAME ::boost::detail::deduce_char_traits<
                    char_type, Target, Source
                >::type traits;

                typedef ::boost::type_traits::ice_and<
                    ::boost::detail::is_char_or_wchar<src_char_type>::value,                    // source is lexical type
                    ::boost::detail::is_char_or_wchar<target_char_t>::value,                    // target is a lexical type
                    ::boost::is_same<char, src_char_type>::value,                               // source is not a wide character based type
                    ::boost::type_traits::ice_ne<sizeof(char), sizeof(target_char_t) >::value   // target type is based on wide character
                >   is_string_widening_required_t;

                typedef ::boost::type_traits::ice_or<
                    ::boost::is_integral<src>::value,
                    ::boost::detail::is_this_float_conversion_optimized<src, char_type >::value,
                    ::boost::detail::is_char_or_wchar<src_char_type >::value
                >   is_source_input_optimized_t;

                // If we have an optimized conversion for
                // Source, we do not need to construct stringbuf.
                const bool requires_stringbuf = ::boost::type_traits::ice_or<
                        is_string_widening_required_t::value,
                        ::boost::type_traits::ice_not< is_source_input_optimized_t::value >::value
                >::value;

                detail::lexical_stream_limited_src<char_type, traits, requires_stringbuf >
                        interpreter(buf, buf + src_len);

                Target result;
                // Disabling ADL, by directly specifying operators.
                if(!(interpreter.operator <<(arg) && interpreter.operator >>(result)))
                  BOOST_LCAST_THROW_BAD_CAST(Source, Target);
                return result;
            }
        };
#if (defined _MSC_VER)
# pragma warning( pop )
#endif

        template <typename Source>
        struct lexical_cast_copy
        {
            static inline Source lexical_cast_impl(const Source &arg)
            {
                return arg;
            }
        };

        template <class Source, class Target >
        struct detect_precision_loss
        {
         typedef boost::numeric::Trunc<Source> Rounder;
         typedef Source source_type ;

         typedef BOOST_DEDUCED_TYPENAME mpl::if_<
            ::boost::is_arithmetic<Source>, Source, Source const&
          >::type argument_type ;

         static source_type nearbyint ( argument_type s )
         {
            const source_type orig_div_round = s / Rounder::nearbyint(s);
            const source_type eps = std::numeric_limits<source_type>::epsilon();

            if ((orig_div_round > 1 ? orig_div_round - 1 : 1 - orig_div_round) > eps)
                BOOST_LCAST_THROW_BAD_CAST(Source, Target);

            return s ;
         }

         typedef typename Rounder::round_style round_style;
        } ;

        template <class Source, class Target >
        struct nothrow_overflow_handler
        {
          void operator() ( boost::numeric::range_check_result r )
          {
            if (r != boost::numeric::cInRange)
                BOOST_LCAST_THROW_BAD_CAST(Source, Target);
          }
        } ;

        template <typename Target, typename Source>
        struct lexical_cast_dynamic_num_not_ignoring_minus
        {
            static inline Target lexical_cast_impl(const Source &arg)
            {
                return boost::numeric::converter<
                        Target,
                        Source,
                        boost::numeric::conversion_traits<Target,Source>,
                        nothrow_overflow_handler<Source, Target>,
                        detect_precision_loss<Source, Target>
                >::convert(arg);
            }
        };

        template <typename Target, typename Source>
        struct lexical_cast_dynamic_num_ignoring_minus
        {
            static inline Target lexical_cast_impl(const Source &arg)
            {
                typedef boost::numeric::converter<
                        Target,
                        Source,
                        boost::numeric::conversion_traits<Target,Source>,
                        nothrow_overflow_handler<Source, Target>,
                        detect_precision_loss<Source, Target>
                > converter_t;

                return (
                    arg < 0 ? -converter_t::convert(-arg) : converter_t::convert(arg)
                );
            }
        };

        /*
         * lexical_cast_dynamic_num follows the rules:
         * 1) If Source can be converted to Target without precision loss and
         * without overflows, then assign Source to Target and return
         *
         * 2) If Source is less than 0 and Target is an unsigned integer,
         * then negate Source, check the requirements of rule 1) and if
         * successful, assign static_casted Source to Target and return
         *
         * 3) Otherwise throw a bad_lexical_cast exception
         *
         *
         * Rule 2) required because boost::lexical_cast has the behavior of
         * stringstream, which uses the rules of scanf for conversions. And
         * in the C99 standard for unsigned input value minus sign is
         * optional, so if a negative number is read, no errors will arise
         * and the result will be the two's complement.
         */
        template <typename Target, typename Source>
        struct lexical_cast_dynamic_num
        {
            static inline Target lexical_cast_impl(const Source &arg)
            {
                typedef BOOST_DEDUCED_TYPENAME ::boost::mpl::if_c<
                    ::boost::type_traits::ice_and<
                        ::boost::type_traits::ice_or<
                            ::boost::is_signed<Source>::value,
                            ::boost::is_float<Source>::value
                        >::value,
                        ::boost::type_traits::ice_not<
                            ::boost::is_same<Source, bool>::value
                        >::value,
                        ::boost::type_traits::ice_not<
                            ::boost::is_same<Target, bool>::value
                        >::value,
                        ::boost::is_unsigned<Target>::value
                    >::value,
                    lexical_cast_dynamic_num_ignoring_minus<Target, Source>,
                    lexical_cast_dynamic_num_not_ignoring_minus<Target, Source>
                >::type caster_type;

                return caster_type::lexical_cast_impl(arg);
            }
        };
    }

    template <typename Target, typename Source>
    inline Target lexical_cast(const Source &arg)
    {
        typedef BOOST_DEDUCED_TYPENAME ::boost::detail::array_to_pointer_decay<Source>::type src;

        typedef BOOST_DEDUCED_TYPENAME ::boost::type_traits::ice_or<
                ::boost::detail::is_xchar_to_xchar<Target, src >::value,
                ::boost::detail::is_char_array_to_stdstring<Target, src >::value,
                ::boost::type_traits::ice_and<
                     ::boost::is_same<Target, src >::value,
                     ::boost::detail::is_stdstring<Target >::value
                >::value
        > shall_we_copy_t;

        typedef BOOST_DEDUCED_TYPENAME
                ::boost::detail::is_arithmetic_and_not_xchars<Target, src > shall_we_copy_with_dynamic_check_t;

        typedef BOOST_DEDUCED_TYPENAME ::boost::mpl::if_c<
            shall_we_copy_t::value,
            ::boost::detail::lexical_cast_copy<src >,
            BOOST_DEDUCED_TYPENAME ::boost::mpl::if_c<
                 shall_we_copy_with_dynamic_check_t::value,
                 ::boost::detail::lexical_cast_dynamic_num<Target, src >,
                 ::boost::detail::lexical_cast_do_cast<Target, src >
            >::type
        >::type caster_type;

        return caster_type::lexical_cast_impl(arg);
    }

} // namespace boost

#else // #ifndef BOOST_NO_TEMPLATE_PARTIAL_SPECIALIZATION

namespace boost {
    namespace detail
    {

        // selectors for choosing stream character type
        template<typename Type>
        struct stream_char
        {
            typedef char type;
        };

#ifndef BOOST_LCAST_NO_WCHAR_T
#ifndef BOOST_NO_INTRINSIC_WCHAR_T
        template<>
        struct stream_char<wchar_t>
        {
            typedef wchar_t type;
        };
#endif

        template<>
        struct stream_char<wchar_t *>
        {
            typedef wchar_t type;
        };

        template<>
        struct stream_char<const wchar_t *>
        {
            typedef wchar_t type;
        };

        template<>
        struct stream_char<std::wstring>
        {
            typedef wchar_t type;
        };
#endif

        // stream wrapper for handling lexical conversions
        template<typename Target, typename Source, typename Traits>
        class lexical_stream
        {
        private:
            typedef typename widest_char<
                typename stream_char<Target>::type,
                typename stream_char<Source>::type>::type char_type;

            typedef Traits traits_type;

        public:
            lexical_stream(char_type* = 0, char_type* = 0)
            {
                stream.unsetf(std::ios::skipws);
                lcast_set_precision(stream, static_cast<Source*>(0), static_cast<Target*>(0) );
            }
            ~lexical_stream()
            {
                #if defined(BOOST_NO_STRINGSTREAM)
                stream.freeze(false);
                #endif
            }
            bool operator<<(const Source &input)
            {
                return !(stream << input).fail();
            }
            template<typename InputStreamable>
            bool operator>>(InputStreamable &output)
            {
                return !is_pointer<InputStreamable>::value &&
                       stream >> output &&
                       stream.get() ==
#if defined(__GNUC__) && (__GNUC__<3) && defined(BOOST_NO_STD_WSTRING)
// GCC 2.9x lacks std::char_traits<>::eof().
// We use BOOST_NO_STD_WSTRING to filter out STLport and libstdc++-v3
// configurations, which do provide std::char_traits<>::eof().

                           EOF;
#else
                           traits_type::eof();
#endif
            }

            bool operator>>(std::string &output)
            {
                #if defined(BOOST_NO_STRINGSTREAM)
                stream << '\0';
                #endif
                stream.str().swap(output);
                return true;
            }
            #ifndef BOOST_LCAST_NO_WCHAR_T
            bool operator>>(std::wstring &output)
            {
                stream.str().swap(output);
                return true;
            }
            #endif

        private:
            #if defined(BOOST_NO_STRINGSTREAM)
            std::strstream stream;
            #elif defined(BOOST_NO_STD_LOCALE)
            std::stringstream stream;
            #else
            std::basic_stringstream<char_type,traits_type> stream;
            #endif
        };
    }

    // call-by-value fallback version (deprecated)

    template<typename Target, typename Source>
    Target lexical_cast(Source arg)
    {
        typedef typename detail::widest_char<
            BOOST_DEDUCED_TYPENAME detail::stream_char<Target>::type
          , BOOST_DEDUCED_TYPENAME detail::stream_char<Source>::type
        >::type char_type;

        typedef std::char_traits<char_type> traits;
        detail::lexical_stream<Target, Source, traits> interpreter;
        Target result;

        if(!(interpreter << arg && interpreter >> result))
          BOOST_LCAST_THROW_BAD_CAST(Source, Target);
        return result;
    }

} // namespace boost

#endif

// Copyright Kevlin Henney, 2000-2005.
// Copyright Alexander Nasonov, 2006-2010.
// Copyright Antony Polukhin, 2011-2012.
//
// Distributed under the Boost Software License, Version 1.0. (See
// accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt)

#undef BOOST_LCAST_THROW_BAD_CAST
#undef BOOST_LCAST_NO_WCHAR_T

#endif // BOOST_LEXICAL_CAST_INCLUDED

