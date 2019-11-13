function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_Compl_After_Trigger()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp', {} )

  call setpos( '.', [ 0, 11, 6 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! Check( id ) closure
    call WaitForAssert( {->
          \ assert_true( pyxeval( 'ycm_state.GetCurrentCompletionRequest() is not None' ) )
          \ } )
    call WaitForAssert( {->
          \ assert_true( pyxeval( 'ycm_state.CompletionRequestReady()' ) )
          \ } )
    redraw
    call WaitForAssert( {->
          \ assert_true( pumvisible(), 'pumvisible()' )
          \ }, 10000 )
    call feedkeys( "\<ESC>" )
  endfunction

  call timer_start( 500, funcref( 'Check' ) )
  call feedkeys( 'cl.', 'ntx!' )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunctio
