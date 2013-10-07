from __future__ import with_statement
import math
import time
import sys

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

PRIMES = [
    112272535095293,
    112582705942171,
    112272535095293,
    115280095190773,
    115797848077099,
    117450548693743,
    993960000099397]

def is_prime(n):
    if n % 2 == 0:
        return False

    sqrt_n = int(math.floor(math.sqrt(n)))
    for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            return False
    return True

def sequential():
    return list(map(is_prime, PRIMES))

def with_process_pool_executor():
    with ProcessPoolExecutor(10) as executor:
        return list(executor.map(is_prime, PRIMES))

def with_thread_pool_executor():
    with ThreadPoolExecutor(10) as executor:
        return list(executor.map(is_prime, PRIMES))

def main():
    for name, fn in [('sequential', sequential),
                     ('processes', with_process_pool_executor),
                     ('threads', with_thread_pool_executor)]:
        sys.stdout.write('%s: ' % name.ljust(12))
        start = time.time()
        if fn() != [True] * len(PRIMES):
            sys.stdout.write('failed\n')
        else:
            sys.stdout.write('%.2f seconds\n' % (time.time() - start))

if __name__ == '__main__':
    main()
