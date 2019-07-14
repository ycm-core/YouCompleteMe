
function! youcompleteme#test#setup#SetUp( setup_f ) abort
  if exists ( 'g:loaded_youcompleteme' )
    unlet g:loaded_youcompleteme
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
  pyx <<EOF

if 'ycm_state' in globals():
  ycm_state.OnVimLeave()
  del ycm_state

EOF
endfunction

function! youcompleteme#test#setup#OpenFile( f ) abort
  execute 'edit '
        \ . g:ycm_test_plugin_dir
        \ . '/'
        \ . a:f

  call WaitForAssert( {->
        \ assert_true( pyxeval( 'ycm_state.NativeFiletypeCompletionUsable()' ) )
        \ } )

  " Need to wait for the server to be ready. The best way to do this is to
  " force compile and diagnostics
  YcmForceCompileAndDiagnostics

  " Sometimes, that's just not enough to ensure stuff works
  sleep 1000m

  " FIXME: We need a much more robust way to wait for the server to be ready
endfunction
