function! s:_ClearSigHelp()
  pythonx _sh_state = sh.UpdateSignatureHelp( _sh_state, {} )
  call assert_true( pyxeval( '_sh_state.popup_win_id is None' ),
        \ 'win id none with emtpy' )
  unlet! s:popup_win_id
endfunction

function s:_GetSigHelpWinID()
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
        \       'ycm_state._signature_help_state.popup_win_id is not None'
        \     ),
        \     'popup_win_id'
        \   )
        \ } )
  let s:popup_win_id = pyxeval( 'ycm_state._signature_help_state.popup_win_id' )
  return s:popup_win_id
endfunction

function! s:_CheckPopupPosition( winid, pos )
  redraw
  let actual_pos = popup_getpos( a:winid )
  let ret = 0
  if a:pos->empty()
    return assert_true( actual_pos->empty(), 'popup pos empty' )
  endif
  for c in keys( a:pos )
    if !has_key( actual_pos, c )
      let ret += 1
      call assert_report( 'popup with ID '
                        \ . string( a:winid )
                        \ . ' has no '
                        \ . c
                        \ . ' in: '
                        \ . string( actual_pos ) )
    else
      let ret += assert_equal( a:pos[ c ],
                             \ actual_pos[ c ],
                             \ c . ' in: ' . string( actual_pos ) )
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
  sleep 250m
  let winid = pyxeval( '_sh_state.popup_win_id' )
  call s:_CheckPopupPosition( winid, a:pos )
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
  " mode until done. Use a func because it's big enough (a lambda is a little
  " neater in many contexts).
  function! Check( id ) closure
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
  delfunc! Check
endfunction

function! Test_Signatures_With_PUM_NoSigns()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/general_fallback'
        \ . '/make_drink.cc' )

  " Make sure that error signs don't shift the window
  setlocal signcolumn=no

  call setpos( '.', [ 0, 7, 13 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function Check2( id ) closure
    call WaitForAssert( {-> assert_true( pumvisible() ) } )
    call WaitForAssert( {-> assert_notequal( [], complete_info().items ) } )
    call assert_equal( 7, pum_getpos().row )
    redraw
    sleep 250m

    " NOTE: anchor is 0-based
    call assert_equal( 6,
                     \ pyxeval( 'ycm_state._signature_help_state.anchor[0]' ) )
    call assert_equal( 13,
                     \ pyxeval( 'ycm_state._signature_help_state.anchor[1]' ) )


    call s:_CheckPopupPosition( s:_GetSigHelpWinID(),
                              \ { 'line': 5, 'col': 12 } )

    call feedkeys( "\<ESC>", 't' )
  endfunction

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! Check( id ) closure
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       'ycm_state._signature_help_state.popup_win_id is not None'
          \     ),
          \     'popup_win_id'
          \   )
          \ } )
    call s:_CheckPopupPosition( s:_GetSigHelpWinID(),
                              \ { 'line': 5, 'col': 12 } )

    call timer_start( 500, funcref( 'Check2' ) )
    call feedkeys( ' TypeOfD', 't' )
  endfunction

  call assert_false( pyxeval( 'ycm_state.SignatureHelpRequestReady()' ) )
  call timer_start( 500, funcref( 'Check' ) )
  call feedkeys( 'C(', 'ntx!' )

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
  delfunc! Check
  delfunc! Check2
endfunction

function! Test_Signatures_With_PUM_Signs()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/general_fallback'
        \ . '/make_drink.cc' )

  " Make sure that sign causes the popup to shift
  setlocal signcolumn=auto

  call setpos( '.', [ 0, 7, 13 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function Check2( id ) closure
    call WaitForAssert( {-> assert_true( pumvisible() ) } )
    call WaitForAssert( {-> assert_notequal( [], complete_info().items ) } )
    call assert_equal( 7, pum_getpos().row )
    redraw
    sleep 250m

    " NOTE: anchor is 0-based
    call assert_equal( 6,
                     \ pyxeval( 'ycm_state._signature_help_state.anchor[0]' ) )
    call assert_equal( 13,
                     \ pyxeval( 'ycm_state._signature_help_state.anchor[1]' ) )


    " Sign column is shown, popup shifts to the right 2 screen columns
    call s:_CheckPopupPosition( s:_GetSigHelpWinID(),
                              \ { 'line': 5, 'col': 14 } )

    call feedkeys( "\<ESC>", 't' )
  endfunction

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! Check( id ) closure
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       'ycm_state._signature_help_state.popup_win_id is not None'
          \     ),
          \     'popup_win_id'
          \   )
          \ } )
    call s:_CheckPopupPosition( s:_GetSigHelpWinID(),
                              \ { 'line': 5, 'col': 12 } )

    call timer_start( 500, funcref( 'Check2' ) )
    call feedkeys( ' TypeOfD', 't' )
  endfunction

  call assert_false( pyxeval( 'ycm_state.SignatureHelpRequestReady()' ) )
  call timer_start( 500, funcref( 'Check' ) )
  call feedkeys( 'C(', 'ntx!' )

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
  delfunc! Check
  delfunc! Check2
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
        \ 'col': &columns - len( "test function" ) - 1,
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
        \ 'col': &columns - len( "test function" ) - 1,
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
        \ 'col': &columns - len( "toast function" ) - 1,
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
        \ 'col': &columns - len( "toast function" ) - 1,
        \ } )
  call s:_ClearSigHelp()

  call popup_clear()
  %bwipeout!
endfunction

function! Test_Signatures_TopLine()
  call youcompleteme#test#setup#OpenFile( 'test/testdata/python/test.py' )
  call setpos( '.', [ 0, 1, 24 ] )
  call test_override( 'char_avail', 1 )

  function! Check( id ) closure
    call s:_CheckPopupPosition( s:_GetSigHelpWinID(), { 'line': 2, 'col': 23 } )
    call feedkeys( "\<ESC>" )
  endfunction

  call timer_start( 500, funcref( 'Check' ) )
  call feedkeys( 'cl(', 'ntx!' )

  call test_override( 'ALL', 0 )
  %bwipeout!
  delfun! Check
endfunction

function! Test_Signatures_TopLineWithPUM()
  call youcompleteme#test#setup#OpenFile( 'test/testdata/python/test.py' )
  call setpos( '.', [ 0, 1, 24 ] )
  call test_override( 'char_avail', 1 )

  function! CheckSigHelpAndTriggerCompletion( id ) closure
    " Popup placed below the cursor
    call s:_CheckPopupPosition( s:_GetSigHelpWinID(), { 'line': 2, 'col': 23 } )

    " Push more characters into the typeahead buffer to trigger insert mode
    " completion.
    call timer_start( 500, funcref( 'CheckCompletionVisibleAndSigHelpHidden' ) )
    call feedkeys( " os.", 't' )
  endfunction

  function! CheckCompletionVisibleAndSigHelpHidden( id ) closure
    " Completion popup now visible, overlapping where the sig help popup was
    call WaitForAssert( {-> assert_true( pumvisible() ) } )
    call assert_equal( 1, pum_getpos().row )
    call assert_equal( 28, pum_getpos().col )
    " so we hide the sig help popup.
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       'ycm_state._signature_help_state.popup_win_id is None'
          \     ),
          \     'popup_win_id'
          \   )
          \ } )
    call s:_CheckPopupPosition( s:popup_win_id, {} )

    " We're done in in sert mode now.
    call feedkeys( "\<ESC>", 't' )
  endfunction
  " Edit the line and trigger signature help
  call timer_start( 500, funcref( 'CheckSigHelpAndTriggerCompletion' ) )
  call feedkeys( 'C(', 'ntx!' )

  call test_override( 'ALL', 0 )
  %bwipeout!

  delfunc! CheckSigHelpAndTriggerCompletion
  delfunc! CheckCompletionVisibleAndSigHelpHidden
endfunction

