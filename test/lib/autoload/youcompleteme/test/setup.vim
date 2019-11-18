
function! youcompleteme#test#setup#SetUp() abort
  if exists ( 'g:loaded_youcompleteme' )
    unlet g:loaded_youcompleteme
  endif

  if pyxeval( "'ycm_state' in globals()" )
    pyx ycm_state.OnVimLeave()
    pyx del ycm_state
  endif

  source $PWD/vimrc

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
  execute 'edit '
        \ . g:ycm_test_plugin_dir
        \ . '/'
        \ . a:f

  if get( a:kwargs, 'native_ft', 1 )
    call WaitForAssert( {->
  	\ assert_true( pyxeval( 'ycm_state.NativeFiletypeCompletionUsable()' ) )
  	\ } )
  
    " Need to wait for the server to be ready. The best way to do this is to
    " force compile and diagnostics, though this only works for the c-based
    " completers. For python and others, we actually need to parse the debug info
    " to check the server state.
    YcmForceCompileAndDiagnostics
  endif

  " Sometimes, that's just not enough to ensure stuff works
  sleep 7

  " FIXME: We need a much more robust way to wait for the server to be ready
endfunction
