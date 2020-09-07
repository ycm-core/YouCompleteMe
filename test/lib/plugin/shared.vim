
" Functions shared by several tests.

" Only load this script once.
if exists('*WaitFor')
  finish
endif

" Run skip the current test if some expression returns true
func SkipIf( expr, msg )
  if type(a:expr) == v:t_func
    let skip = a:expr()
  else
    let skip = eval(a:expr)
  endif

  if skip
    throw 'SKIPPED: ' . a:msg
  endif
endfunction

" Wait for up to five seconds for "expr" to become true.  "expr" can be a
" stringified expression to evaluate, or a funcref without arguments.
" Using a lambda works best.  Example:
"	call WaitFor({-> status == "ok"})
"
" A second argument can be used to specify a different timeout in msec.
"
" When successful the time slept is returned.
" When running into the timeout an exception is thrown, thus the function does
" not return.
func WaitFor(expr, ...)
  let timeout = get(a:000, 0, 5000)
  let slept = s:WaitForCommon(a:expr, v:null, timeout)
  if slept < 0
    throw 'WaitFor() timed out after ' . timeout . ' msec'
  endif
  return slept
endfunc

" Wait for up to five seconds for "assert" to return zero.  "assert" must be a
" (lambda) function containing one assert function.  Example:
"	call WaitForAssert({-> assert_equal("dead", job_status(job)})
"
" A second argument can be used to specify a different timeout in msec.
"
" Return zero for success, one for failure (like the assert function).
func WaitForAssert(assert, ...)
  let timeout = get(a:000, 0, 5000)
  if s:WaitForCommon(v:null, a:assert, timeout) < 0
    return 1
  endif
  return 0
endfunc

" Common implementation of WaitFor() and WaitForAssert().
" Either "expr" or "assert" is not v:null
" Return the waiting time for success, -1 for failure.
func s:WaitForCommon(expr, assert, timeout)
  " using reltime() is more accurate, but not always available
  let slept = 0
  if has('reltime')
    let start = reltime()
  endif

  while 1
    if type(a:expr) == v:t_func
      let success = a:expr()
    elseif type(a:assert) == v:t_func
      let success = a:assert() == 0
    else
      let success = eval(a:expr)
    endif
    if success
      return slept
    endif

    if slept >= a:timeout
      break
    endif
    if type(a:assert) == v:t_func
      " Remove the error added by the assert function.
      call remove(v:errors, -1)
    endif

    sleep 10m
    if has('reltime')
      let slept = float2nr(reltimefloat(reltime(start)) * 1000)
    else
      let slept += 10
    endif
  endwhile

  return -1  " timed out
endfunc
