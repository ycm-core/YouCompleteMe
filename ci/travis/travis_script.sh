#!/bin/bash

if [ "${YCM_FLAKE8}" = true ]; then
  ./run_tests.py
else
  ./run_tests.py --no-flake8
fi
