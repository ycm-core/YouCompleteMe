/*
* Copyright (c) 2008, Power of Two Games LLC
*               2013, Google Inc.
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*     * Redistributions of source code must retain the above copyright
*       notice, this list of conditions and the following disclaimer.
*     * Redistributions in binary form must reproduce the above copyright
*       notice, this list of conditions and the following disclaimer in the
*       documentation and/or other materials provided with the distribution.
*     * Neither the name of Power of Two Games LLC nor the
*       names of its contributors may be used to endorse or promote products
*       derived from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY POWER OF TWO GAMES LLC ``AS IS'' AND ANY
* EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL POWER OF TWO GAMES LLC BE LIABLE FOR ANY
* DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#ifndef CUSTOM_ASSERT_H
#define CUSTOM_ASSERT_H

namespace assert_ns { namespace Assert
{

enum FailBehavior
{
  Halt,
  Continue,
};

typedef FailBehavior (*Handler)(const char* condition,
                                const char* msg,
                                const char* file,
                                int line);

Handler GetHandler();
void SetHandler(Handler newHandler);

FailBehavior ReportFailure(const char* condition,
                           const char* file,
                           int line,
                           const char* msg, ...);
}}

#if defined(_MSC_VER)
#   define X_HALT() __debugbreak()
#elif defined(__GNUC__) || defined(__clang__)
#   define X_HALT() __builtin_trap()
#else
#    define X_HALT() exit(__LINE__)
#endif

#define X_UNUSED(x) do { (void)sizeof(x); } while(0)

#ifndef NDEBUG
  #define X_ASSERT(cond) \
    do \
    { \
      if (!(cond)) \
      { \
        if (assert_ns::Assert::ReportFailure(#cond, __FILE__, __LINE__, 0) == \
          assert_ns::Assert::Halt) \
          X_HALT(); \
      } \
    } while(0)

  #define X_ASSERT_MSG(cond, msg, ...) \
    do \
    { \
      if (!(cond)) \
      { \
        if (assert_ns::Assert::ReportFailure(#cond, __FILE__, __LINE__, (msg), __VA_ARGS__) == \
          assert_ns::Assert::Halt) \
          X_HALT(); \
      } \
    } while(0)

  #define X_ASSERT_FAIL(msg, ...) \
    do \
    { \
      if (assert_ns::Assert::ReportFailure(0, __FILE__, __LINE__, (msg), __VA_ARGS__) == \
        assert_ns::Assert::Halt) \
      X_HALT(); \
    } while(0)

  #define X_VERIFY(cond) X_ASSERT(cond)
  #define X_VERIFY_MSG(cond, msg, ...) X_ASSERT_MSG(cond, msg, ##__VA_ARGS__)
#else
  #define X_ASSERT(condition) \
    do { X_UNUSED(condition); } while(0)
  #define X_ASSERT_MSG(condition, msg, ...) \
    do { X_UNUSED(condition); X_UNUSED(msg); } while(0)
  #define X_ASSERT_FAIL(msg, ...) \
    do { X_UNUSED(msg); } while(0)
  #define X_VERIFY(cond) (void)(cond)
  #define X_VERIFY_MSG(cond, msg, ...) \
    do { (void)(cond); X_UNUSED(msg); } while(0)
#endif

#define X_STATIC_ASSERT(x) \
  typedef char StaticAssert[(x) ? 1 : -1];

#endif // CUSTOM_ASSERT_H
