function! s:_ClearSigHelp()
  pythonx _sh_state = sh.UpdateSignatureHelp( _sh_state, {} )
  call assert_true( pyxeval( '_sh_state.popup_win_id is None' ),
        \ 'win id none with emtpy' )
endfunction

function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  call youcompleteme#test#setup#SetUp()
  pythonx from ycm import signature_help as sh
  pythonx _sh_state = sh.SignatureHelpState()
endfunction

function! TearDown()
  call s:_ClearSigHelp()
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
          \     'sig help request reqdy'
          \   )
          \ } )
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       "bool( ycm_state.GetSignatureHelpResponse()[ 'signatures' ] )"
          \     ),
          \     'sig help request reqdy'
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

function! s:_CheckPopupPosition( winid, pos )
  let actual_pos = popup_getpos( a:winid )
  let ret = 0
  for c in [ 'line', 'col', 'width', 'height' ]
    if has_key( a:pos, c )
      let ret += assert_equal( a:pos[ c ], actual_pos[ c ], c )
    endif
  endfor
  return ret
endfunction

function! s:_CheckSigHelpAtPos( sh, cursor, pos )
  call setpos( '.', [ 0 ] + a:cursor )
  redraw
  pythonx _sh_state = sh.UpdateSignatureHelp( _sh_state,
                                            \ vim.eval( 'a:sh' ) )
  redraw
  let winid = pyxeval( '_sh_state.popup_win_id' )
  call s:_CheckPopupPosition( winid, a:pos )
endfunction

function! Test_Placement_Simple()
  call assert_true( &lines >= 25, "Enough rows" )
  call assert_true( &columns >= 25, "Enough columns" )

  let X = join( map( range( 0, &columns - 1 ), {->'X'} ), '' )

  for i in range( 0, &lines )
    call append( line('$'), X )
  endfor

  " Delete the blank line that is always added to a buffer
  0delete

  call s:_ClearSigHelp()

  let v_sh = {
        \   'activeSignature': 0,
        \   'activeParameter': 0,
        \   'signatures': [
        \     { 'label': 'test function', 'parameters': [] }
        \   ]
        \ }

  " When displayed in the middle with plenty of space
  call s:_CheckSigHelpAtPos( v_sh, [ 10, 3 ], {
        \ 'line': 9,
        \ 'col': 1
        \ } )
  " Confirm that anchoring works (i.e. it doesn't move!)
  call s:_CheckSigHelpAtPos( v_sh, [ 20, 10 ], {
        \ 'line': 9,
        \ 'col': 1
        \ } )
  call s:_ClearSigHelp()

  " Window slides from left of screen
  call s:_CheckSigHelpAtPos( v_sh, [ 10, 2 ], {
        \ 'line': 9,
        \ 'col': 1,
        \ } )
  call s:_ClearSigHelp()

  " Window slides from left of screen
  call s:_CheckSigHelpAtPos( v_sh, [ 10, 1 ], {
        \ 'line': 9,
        \ 'col': 1,
        \ } )
  call s:_ClearSigHelp()

  " Cursor at top-left of window
  call s:_CheckSigHelpAtPos( v_sh, [ 1, 1 ], {
        \ 'line': 2,
        \ 'col': 1,
        \ } )
  call s:_ClearSigHelp()

  " Cursor at top-right of window
  call s:_CheckSigHelpAtPos( v_sh, [ 1, &columns ], {
        \ 'line': 2,
        \ 'col': &columns - len( "test function" ),
        \ } )
  call s:_ClearSigHelp()

  " Bottom-left of window
  call s:_CheckSigHelpAtPos( v_sh, [ &lines + 1, 1 ], {
        \ 'line': &lines - 2,
        \ 'col': 1,
        \ } )
  call s:_ClearSigHelp()

  " Bottom-right of window
  call s:_CheckSigHelpAtPos( v_sh, [ &lines + 1, &columns ], {
        \ 'line': &lines - 2,
        \ 'col': &columns - len( "test function" ),
        \ } )
  call s:_ClearSigHelp()

  call popup_clear()
  %bwipeout!
endfunction

function! Test_Placement_MultiLine()
  call assert_true( &lines >= 25, "Enough rows" )
  call assert_true( &columns >= 25, "Enough columns" )

  let X = join( map( range( 0, &columns - 1 ), {->'X'} ), '' )

  for i in range( 0, &lines )
    call append( line('$'), X )
  endfor

  " Delete the blank line that is always added to a buffer
  0delete

  call s:_ClearSigHelp()

  let v_sh = {
        \   'activeSignature': 0,
        \   'activeParameter': 0,
        \   'signatures': [
        \     { 'label': 'test function', 'parameters': [] },
        \     { 'label': 'toast function', 'parameters': [
        \         { 'label': 'toast!' }
        \     ] },
        \   ]
        \ }

  " When displayed in the middle with plenty of space
  call s:_CheckSigHelpAtPos( v_sh, [ 10, 3 ], {
        \ 'line': 8,
        \ 'col': 1
        \ } )
  " Confirm that anchoring works (i.e. it doesn't move!)
  call s:_CheckSigHelpAtPos( v_sh, [ 20, 10 ], {
        \ 'line': 8,
        \ 'col': 1
        \ } )
  call s:_ClearSigHelp()

  " Window slides from left of screen
  call s:_CheckSigHelpAtPos( v_sh, [ 10, 2 ], {
        \ 'line': 8,
        \ 'col': 1,
        \ } )
  call s:_ClearSigHelp()

  " Window slides from left of screen
  call s:_CheckSigHelpAtPos( v_sh, [ 10, 1 ], {
        \ 'line': 8,
        \ 'col': 1,
        \ } )
  call s:_ClearSigHelp()

  " Cursor at top-left of window
  call s:_CheckSigHelpAtPos( v_sh, [ 1, 1 ], {
        \ 'line': 2,
        \ 'col': 1,
        \ } )
  call s:_ClearSigHelp()

  " Cursor at top-right of window
  call s:_CheckSigHelpAtPos( v_sh, [ 1, &columns ], {
        \ 'line': 2,
        \ 'col': &columns - len( "toast function" ),
        \ } )
  call s:_ClearSigHelp()

  " Bottom-left of window
  call s:_CheckSigHelpAtPos( v_sh, [ &lines + 1, 1 ], {
        \ 'line': &lines - 3,
        \ 'col': 1,
        \ } )
  call s:_ClearSigHelp()

  " Bottom-right of window
  call s:_CheckSigHelpAtPos( v_sh, [ &lines + 1, &columns ], {
        \ 'line': &lines - 3,
        \ 'col': &columns - len( "toast function" ),
        \ } )
  call s:_ClearSigHelp()

  call popup_clear()
  %bwipeout!
endfunction
