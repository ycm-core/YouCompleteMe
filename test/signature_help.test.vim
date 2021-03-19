let s:timer_interval = 2000

function! s:WaitForSigHelpAvailable( filetype )
  let tries = 0
  call WaitFor( {-> s:_CheckSignatureHelpAvailable( a:filetype ) } )
  while py3eval(
        \ 'ycm_state._signature_help_available_requests[ '
        \ . 'vim.eval( "a:filetype" ) ].Response() == "PENDING"' ) &&
        \ tries < 10
    " Force sending another request
    py3 ycm_state._signature_help_available_requests[
          \ vim.eval( 'a:filetype' ) ].Start( vim.eval( 'a:filetype' ) )
    call WaitFor( {-> s:_CheckSignatureHelpAvailable( a:filetype ) } )
    let tries += 1
  endwhile
  call ch_log( "Signature help is avaialble now for " . a:filetype )
endfunction

function! s:_ClearSigHelp()
  pythonx _sh_state = sh.UpdateSignatureHelp( _sh_state, {} )
  call assert_true( pyxeval( '_sh_state.popup_win_id is None' ),
        \ 'win id none with emtpy' )
  unlet! s:popup_win_id
endfunction

function! s:_CheckSignatureHelpAvailable( filetype )
  return pyxeval(
        \ 'ycm_state.SignatureHelpAvailableRequestComplete('
        \ . ' vim.eval( "a:filetype" ), False )' )
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

function! s:_CheckSigHelpAtPos( sh, cursor, pos )
  call setpos( '.', [ 0 ] + a:cursor )
  redraw
  pythonx _sh_state = sh.UpdateSignatureHelp( _sh_state,
                                            \ vim.eval( 'a:sh' ) )
  redraw
  let winid = pyxeval( '_sh_state.popup_win_id' )
  call youcompleteme#test#popup#CheckPopupPosition( winid, a:pos )
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
" endfunction

function! Test_Enough_Screen_Space()
  call assert_true( &lines >= 25,
                  \ &lines . " is not enough rows. need 25." )
  call assert_true( &columns >= 80,
                  \ &columns . " is not enough columns. need 80." )
endfunction

function! Test_Signatures_After_Trigger()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/vim/mixed_filetype.vim',
        \ { 'native_ft': 0, 'force_delay': v:true } )

  call WaitFor( {-> s:_CheckSignatureHelpAvailable( 'vim' ) } )
  call s:WaitForSigHelpAvailable( 'python' )

  call setpos( '.', [ 0, 3, 17 ] )

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
          \     'sig help request ready'
          \   )
          \ } )
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       "bool( ycm_state.GetSignatureHelpResponse()[ 'signatures' ] )"
          \     ),
          \     'sig help request has signatures'
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
    call test_override( 'ALL', 0 )
    call feedkeys( "\<ESC>" )
  endfunction

  call assert_false( pyxeval( 'ycm_state.SignatureHelpRequestReady()' ) )
  call timer_start( s:timer_interval, funcref( 'Check' ) )
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
  delfunc! Check
endfunction

function! Test_Signatures_With_PUM_NoSigns()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/general_fallback'
        \ . '/make_drink.cc', {} )

  call s:WaitForSigHelpAvailable( 'cpp' )

  " Make sure that error signs don't shift the window
  setlocal signcolumn=no

  call setpos( '.', [ 0, 7, 13 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check2( id ) closure
    call WaitForAssert( {-> assert_true( pumvisible() ) } )
    call WaitForAssert( {-> assert_notequal( [], complete_info().items ) } )
    call assert_equal( 7, pum_getpos().row )
    redraw

    " NOTE: anchor is 0-based
    call assert_equal( 6,
                     \ pyxeval( 'ycm_state._signature_help_state.anchor[0]' ) )
    call assert_equal( 13,
                     \ pyxeval( 'ycm_state._signature_help_state.anchor[1]' ) )


    " Popup is shifted due to 80 column screen
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 5, 'col': 5 } )

    call test_override( 'ALL', 0 )
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
    " Popup is shifted left due to 80 char screen
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 5, 'col': 5 } )

    call timer_start( s:timer_interval, funcref( 'Check2' ) )
    call feedkeys( ' TypeOfD', 't' )
  endfunction

  call assert_false( pyxeval( 'ycm_state.SignatureHelpRequestReady()' ) )
  call timer_start( s:timer_interval, funcref( 'Check' ) )
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
  delfunc! Check
  delfunc! Check2
endfunction

function! Test_Signatures_With_PUM_Signs()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/general_fallback'
        \ . '/make_drink.cc', {} )

  call s:WaitForSigHelpAvailable( 'cpp' )

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

    " NOTE: anchor is 0-based
    call assert_equal( 6,
                     \ pyxeval( 'ycm_state._signature_help_state.anchor[0]' ) )
    call assert_equal( 13,
                     \ pyxeval( 'ycm_state._signature_help_state.anchor[1]' ) )


    " Sign column is shown, popup shifts to the right 2 screen columns
    " Then shifts back due to 80 character screen width
    " FIXME: This test was supposed to show the shifting right. Write another
    " one which uses a much smaller popup to do that.
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 5, 'col': 5 } )

    call test_override( 'ALL', 0 )
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
    " Popup is shifted left due to 80 char screen
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 5, 'col': 5 } )

    call timer_start( s:timer_interval, funcref( 'Check2' ) )
    call feedkeys( ' TypeOfD', 't' )
  endfunction

  call assert_false( pyxeval( 'ycm_state.SignatureHelpRequestReady()' ) )
  call timer_start( s:timer_interval, funcref( 'Check' ) )
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
        \         { 'label': [ 0, 5 ] }
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
endfunction

function! Test_Signatures_TopLine()
  call youcompleteme#test#setup#OpenFile( 'test/testdata/python/test.py', {} )
  call s:WaitForSigHelpAvailable( 'python' )
  call setpos( '.', [ 0, 1, 24 ] )
  call test_override( 'char_avail', 1 )

  function! Check( id ) closure
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 2, 'col': 23 } )
    call test_override( 'ALL', 0 )
    call feedkeys( "\<ESC>" )
  endfunction

  call timer_start( s:timer_interval, funcref( 'Check' ) )
  call feedkeys( 'cl(', 'ntx!' )

  call test_override( 'ALL', 0 )
  delfun! Check
endfunction

function! Test_Signatures_TopLineWithPUM()
  call youcompleteme#test#setup#OpenFile( 'test/testdata/python/test.py', {} )
  call s:WaitForSigHelpAvailable( 'python' )
  call setpos( '.', [ 0, 1, 24 ] )
  call test_override( 'char_avail', 1 )

  function! CheckSigHelpAndTriggerCompletion( id ) closure
    " Popup placed below the cursor
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 2, 'col': 23 } )

    " Push more characters into the typeahead buffer to trigger insert mode
    " completion.
    "
    " Nte for some reason the first semantic response can take quite some time,
    " and if our timer fires before then, the test just fails. so we take 2
    " seconds here.
    call timer_start( s:timer_interval,
                    \ funcref( 'CheckCompletionVisibleAndSigHelpHidden' ) )
    call feedkeys( " os.", 't' )
  endfunction

  function! CheckCompletionVisibleAndSigHelpHidden( id ) closure
    " Completion popup now visible, overlapping where the sig help popup was
    redraw
    call WaitForAssert( {-> assert_true( pumvisible() ) } )
    call assert_equal( 1, get( pum_getpos(), 'row', -1 ) )
    call assert_equal( 28, get( pum_getpos(), 'col', -1 ) )
    " so we hide the sig help popup.
    call WaitForAssert( {->
          \   assert_true(
          \     pyxeval(
          \       'ycm_state._signature_help_state.popup_win_id is None'
          \     ),
          \     'popup_win_id'
          \   )
          \ } )
    call youcompleteme#test#popup#CheckPopupPosition( s:popup_win_id, {} )

    " We're done in insert mode now.
    call test_override( 'ALL', 0 )
    call feedkeys( "\<ESC>", 't' )
  endfunction

  " Edit the line and trigger signature help
  call timer_start( s:timer_interval,
                  \ funcref( 'CheckSigHelpAndTriggerCompletion' ) )
  call feedkeys( 'C(', 'ntx!' )

  call test_override( 'ALL', 0 )

  delfunc! CheckSigHelpAndTriggerCompletion
  delfunc! CheckCompletionVisibleAndSigHelpHidden
endfunction

function! SetUp_Test_Semantic_Completion_Popup_With_Sig_Help()
  set signcolumn=no
  call youcompleteme#test#setup#PushGlobal( 'ycm_add_preview_to_completeopt',
                                          \ 'popup' )
endfunction

function! Test_Semantic_Completion_Popup_With_Sig_Help()
  call youcompleteme#test#setup#OpenFile(
        \ 'test/testdata/cpp/complete_with_sig_help.cc', {} )
  call s:WaitForSigHelpAvailable( 'cpp' )

  call setpos( '.', [ 0, 10, 1 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check( ... )
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 9, 'col': 6, 'visible': 1 } )

    call FeedAndCheckAgain( '"", t.', funcref( 'Check2' ) )
  endfunction

  function! Check2( ... )
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'that_is_a_thing',
                                              \ 'this_is_a_thing' ] )

    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 9, 'col': 6, 'visible': 1 } )

    call CheckCurrentLine( 'printf("", t.' )
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check3' ) )
  endfunction

  function! Check3( ... )
    " Ensure that we didn't make an error?
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'that_is_a_thing',
                                              \ 'this_is_a_thing' ] )

    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 9, 'col': 6, 'visible': 1 } )

    let compl = complete_info()
    let selected = compl.items[ compl.selected ]
    call assert_equal( 'that_is_a_thing', selected.word )

    call WaitFor( {->
          \ popup_findinfo() > 0 &&
          \ has_key( popup_getpos( popup_findinfo() ), 'visible' ) } )
    let info_popup_id = popup_findinfo()
    call assert_true( popup_getpos( info_popup_id )[ 'visible' ] )

    call CheckCurrentLine( 'printf("", t.that_is_a_thing' )
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check4' ) )

  endfunction

  function! Check4( ... )
    " Ensure that we didn't make an error?
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'that_is_a_thing',
                                              \ 'this_is_a_thing' ] )

    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 9, 'col': 6, 'visible': 1 } )

    let info_popup_id = popup_findinfo()
    let compl = complete_info()
    let selected = compl.items[ compl.selected ]
    call assert_equal( 'this_is_a_thing', selected.word )
    call assert_true( popup_getpos( info_popup_id )[ 'visible' ] )

    call CheckCurrentLine( 'printf("", t.this_is_a_thing' )

    call feedkeys( "\<Esc>" )
  endfunction

  call FeedAndCheckMain( 'iprintf(', funcref( 'Check' ) )

  call test_override( 'ALL', 0 )

  delfunc! Check
  delfunc! Check2
  delfunc! Check3
  delfunc! Check4
endfunction

function! TearDown_Test_Semantic_Completion_Popup_With_Sig_Help()
  set signcolumn&
  call youcompleteme#test#setup#PopGlobal( 'ycm_add_preview_to_completeopt' )
endfunction

function! SetUp_Test_Semantic_Completion_Popup_With_Sig_Help_EmptyBuf()
  set signcolumn=no
  call youcompleteme#test#setup#PushGlobal( 'ycm_filetype_whitelist', {
        \ '*': 1,
        \ 'ycm_nofiletype': 1
        \ } )
  call youcompleteme#test#setup#PushGlobal( 'ycm_filetype_blacklist', {} )
  call youcompleteme#test#setup#PushGlobal( 'ycm_add_preview_to_completeopt',
                                          \ 'popup' )
endfunction

function! Test_Semantic_Completion_Popup_With_Sig_Help_EmptyBuf()
  call youcompleteme#test#setup#OpenFile(
        \ 'test/testdata/cpp/complete_with_sig_help.cc', {} )
  call s:WaitForSigHelpAvailable( 'cpp' )

  call setpos( '.', [ 0, 10, 1 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check( ... )
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 9, 'col': 6, 'visible': 1 } )

    call FeedAndCheckAgain( '"", t.', funcref( 'Check2' ) )
  endfunction

  function! Check2( ... )
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'that_is_a_thing',
                                              \ 'this_is_a_thing' ] )

    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 9, 'col': 6, 'visible': 1 } )

    call CheckCurrentLine( 'printf("", t.' )
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check3' ) )
  endfunction

  function! Check3( ... )
    " Ensure that we didn't make an error?
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'that_is_a_thing',
                                              \ 'this_is_a_thing' ] )

    " XFAIL: Currently the test fails here because the signature help popup
    " disappears when the info_popup is displayed. This seems to be because we
    " end up triggering a FileReadyToParse event inside the info popup (or the
    " signature popup) due to what appears to be a vim bug - the `buftype` of
    " the buffer inside the popup starts off as `popup` but shimers to `""` at
    " some point, making us think it's ok to parse it with ycm_nofiletype is
    " whitelisted.
    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 9, 'col': 6, 'visible': 1 } )

    let compl = complete_info()
    let selected = compl.items[ compl.selected ]
    call assert_equal( 'that_is_a_thing', selected.word )

    call WaitFor( {->
          \ popup_findinfo() > 0 &&
          \ has_key( popup_getpos( popup_findinfo() ), 'visible' ) } )
    let info_popup_id = popup_findinfo()
    call assert_true( popup_getpos( info_popup_id )[ 'visible' ] )

    call CheckCurrentLine( 'printf("", t.that_is_a_thing' )
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check4' ) )

  endfunction

  function! Check4( ... )
    " Ensure that we didn't make an error?
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'that_is_a_thing',
                                              \ 'this_is_a_thing' ] )

    call youcompleteme#test#popup#CheckPopupPosition(
          \ s:_GetSigHelpWinID(),
          \ { 'line': 9, 'col': 6, 'visible': 1 } )

    let info_popup_id = popup_findinfo()
    let compl = complete_info()
    let selected = compl.items[ compl.selected ]
    call assert_equal( 'this_is_a_thing', selected.word )
    call assert_true( popup_getpos( info_popup_id )[ 'visible' ] )

    call CheckCurrentLine( 'printf("", t.this_is_a_thing' )

    call feedkeys( "\<Esc>" )
  endfunction

  call FeedAndCheckMain( 'iprintf(', funcref( 'Check' ) )

  call test_override( 'ALL', 0 )

  delfunc! Check
  delfunc! Check2
  delfunc! Check3
  delfunc! Check4

  throw 'SKIPPED: XFAIL: This test is expected to fail due to '
        \ .. 'https://github.com/ycm-core/YouCompleteMe/issues/3781'

endfunction

function! TearDown_Test_Semantic_Completion_Popup_With_Sig_Help_EmptyBuf()
  set signcolumn&
  call youcompleteme#test#setup#PopGlobal( 'ycm_filetype_whitelist' )
  call youcompleteme#test#setup#PopGlobal( 'ycm_filetype_blacklist' )
  call youcompleteme#test#setup#PopGlobal( 'ycm_add_preview_to_completeopt' )
endfunction
