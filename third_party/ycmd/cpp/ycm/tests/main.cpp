#include "gtest/gtest.h"
#include "gmock/gmock.h"
#include <boost/python.hpp>

int main( int argc, char **argv ) {
  Py_Initialize();
  // Necessary because of usage of the ReleaseGil class
  PyEval_InitThreads();

  testing::InitGoogleMock( &argc, argv );
  return RUN_ALL_TESTS();
}

