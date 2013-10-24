# Copyright 2009 Brian Quinlan. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Execute computations asynchronously using threads or processes."""

import warnings

from concurrent.futures import (FIRST_COMPLETED,
                                FIRST_EXCEPTION,
                                ALL_COMPLETED,
                                CancelledError,
                                TimeoutError,
                                Future,
                                Executor,
                                wait,
                                as_completed,
                                ProcessPoolExecutor,
                                ThreadPoolExecutor)

__author__ = 'Brian Quinlan (brian@sweetapp.com)'

warnings.warn('The futures package has been deprecated. '
              'Use the concurrent.futures package instead.',
              DeprecationWarning)
