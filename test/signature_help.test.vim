function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  call youcompleteme#test#setup#SetUp( v:none )
endfunction

function! ClearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

" This is how we might do screen dump tests
" function! Test_Compl()
"   let setup =<< trim END
"     edit ../third_party/ycmd/ycmd/tests/clangd/testdata/general_fallback/make_drink.cc
"     call setpos( '.', [ 0, 7, 27 ] )
"   END
"   call writefile( setup, 'Xtest_Compl' )
"   let vim = RunVimInTerminal( '-Nu vimrc -S Xtest_Compl', {} )
"
"   function! Test() closure
"     " Wait for Vim to be ready
"     call term_sendkeys( vim, "cl:" )
"     call term_wait( vim )
"     call VerifyScreenDump( vim, "signature_help_Test_Compl_01", {} )
"   endfunction
"
"   call WaitForAssert( {-> Test()} )
"
"   " clean up
"   call StopVimInTerminal(vim)
"   call delete('XtestPopup')
"   %bwipeout!
" endfunction

function! Test_Compl_After_Trigger()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp' )

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
    call assert_true( pumvisible(), 'pumvisible()' )
    call feedkeys( "\<ESC>" )
  endfunction

  call timer_start( 100, funcref( 'Check' ) )
  call feedkeys( 'cl.', 'ntx!' )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunctio

function! Test_Signatures_After_Trigger()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/general_fallback'
        \ . '/make_drink.cc' )

  call setpos( '.', [ 0, 7, 13 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! Check( id ) closure
    redraw
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       'ycm_state.SignatureHelpRequestReady()'
          \     ),
          \     'sign help request reqdy'
          \   )
          \ } )
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       "bool( ycm_state.GetSignatureHelpResponse()[ 'signatures' ] )"
          \     ),
          \     'sign help request reqdy'
          \   )
          \ } )
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       'ycm_state._signature_help_state.popup_win_id is not None'
          \     ),
          \     'popup_win_id'
          \   )
          \ } )

    let popup_win_id = pyxeval( 'ycm_state._signature_help_state.popup_win_id' )
    let pos = win_screenpos( popup_win_id )
    call assert_false( pos == [ 0, 0 ] )

    " Exit insert mode to ensure the test continues
    call feedkeys( "\<ESC>" )
  endfunction

  call assert_false( pyxeval( 'ycm_state.SignatureHelpRequestReady()' ) )
  call timer_start( 500, funcref( 'Check' ) )
  call feedkeys( 'cl(', 'ntx!' )
  call assert_false( pumvisible(), 'pumvisible()' )

  call WaitForAssert( {->
        \   assert_true(
        \     pyxeval(
        \       'ycm_state._signature_help_state.popup_win_id is None'
        \     ),
        \     'popup_win_id'
        \   )
        \ } )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunction

function! Test_Placement_Simple()
  for i in range( 0, 20 )
    call append( line('$'), 'line' . string( i ) )
  endfor

  " Delete the blank line that is always added to a buffer
  0delete

  pythonx from ycm import signature_help as sh
  pythonx _sh_state = sh.SignatureHelpState()
  pythonx sh.UpdateSignatureHelp( _sh_state, {} )
  call assert_true( pyxeval( '_sh_state.popup_win_id is None' ),
        \ 'win id none with emtpy' )

  " When displayed in the middle with plenty of space
  call setpos( '.', [ 0, 10, 3 ] )
  redraw
  call assert_equal( 'line9', getline( '.' ) )
  pythonx _new_sh_state = sh.UpdateSignatureHelp( _sh_state,
        \ { 'activeSignature': 0, 'activeParameter': 0, 'signatures': [
        \   { 'label': 'test function', 'parameters': [] }
        \ ] } )

  call assert_true( pyxeval( '_new_sh_state.popup_win_id is not None' ),
        \ 'win id not none after sig retured' )
  call assert_equal( 9, pyxeval( '_new_sh_state.anchor[ 0 ]' ),
        \ 'anchor line (0 based)' )
  call assert_equal( 2, pyxeval( '_new_sh_state.anchor[ 1 ]' ),
        \ 'anchor col (0 based)' )
  let winid = pyxeval( '_new_sh_state.popup_win_id' )
  let pos = popup_getpos( winid )
  call assert_equal( 9, pos.line, string( pos ) )

  call popup_clear()
  %bwipeout!
endfunction


