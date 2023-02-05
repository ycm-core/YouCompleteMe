
function! youcompleteme#test#setup#SetUp() abort
  if exists ( 'g:loaded_youcompleteme' )
    unlet g:loaded_youcompleteme
  endif

  if pyxeval( "'ycm_state' in globals()" )
    pyx ycm_state.OnVimLeave()
    pyx del ycm_state
  endif

  exe 'source' getcwd() . '/vimrc'

  " This is a bit of a hack
  runtime! plugin/**/*.vim
  call youcompleteme#Enable()

  call assert_true( pyxeval( 'vimsupport.VimSupportsPopupWindows()' ) )
  call WaitForAssert( {->
        \ assert_true( pyxeval( "'ycm_state' in globals()" ) )
        \ } )
  call WaitForAssert( {->
        \ assert_true( pyxeval( 'ycm_state.CheckIfServerIsReady()' ) )
        \ } )
endfunction

function! youcompleteme#test#setup#CleanUp() abort
endfunction

function! youcompleteme#test#setup#OpenFile( f, kwargs ) abort
  silent execute 'edit '
        \ . g:ycm_test_plugin_dir
        \ . '/'
        \ . a:f

  call youcompleteme#test#setup#WaitForInitialParse( a:kwargs )
endfunction

function! youcompleteme#test#setup#WaitForInitialParse( kwargs ) abort
  let native_ft = get( a:kwargs, 'native_ft', 1 )

  if native_ft
    call WaitForAssert( {->
        \ assert_true( pyxeval( 'ycm_state.NativeFiletypeCompletionUsable()' ) )
        \ } )

    " Need to wait for the server to be ready. The best way to do this is to
    " force compile and diagnostics, though this only works for the c-based
    " completers. For python and others, we actually need to parse the debug
    " info to check the server state.
    YcmForceCompileAndDiagnostics
  endif

  if native_ft || get( a:kwargs, 'force_delay', 0 )
    " Sometimes, that's just not enough to ensure stuff works
    if exists( '$YCM_TEST_DELAY' )
      let default_delay = $YCM_TEST_DELAY
    else
      let default_delay = get( g:, 'ycm_test_delay', 2 )
    endif
    let delay = max( [ get( a:kwargs, 'delay', default_delay ),
                   \   get( g:, 'ycm_test_min_delay', 0 ) ] )
    if delay > 0
      exe 'sleep' delay
    endif
  endif

  " FIXME: We need a much more robust way to wait for the server to be ready
endfunction

let s:g_stack = {}

function! youcompleteme#test#setup#PushGlobal( name, value )
  if !has_key( s:g_stack, a:name )
    let s:g_stack[ a:name ] = []
  endif

  let old_value = get( g:, a:name, v:null )
  call add( s:g_stack[ a:name ], old_value )
  call extend( g:, { a:name: a:value  } )

  return old_value
endfunction

function! youcompleteme#test#setup#PopGlobal( name )
  if !has_key( s:g_stack, a:name ) || len( s:g_stack[ a:name ] ) == 0
    return v:null
  endif

  let old_value = s:g_stack[ a:name ][ -1 ]
  call remove( s:g_stack[ a:name ], -1 )

  if old_value is v:null
    silent! call remove( g:, a:name )
  else
    call extend( g:, { a:name: old_value  } )
  endif

  return old_value
endfunction
