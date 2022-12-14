scriptencoding utf-8

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
    call WaitForCompletion()
    call feedkeys( "\<ESC>" )
  endfunction

  call FeedAndCheckMain( 'cl.', funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
endfunction

function! Test_Force_Semantic_TopLevel()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp', {} )

  call setpos( '.', [ 0, 17, 5 ] )

  function! Check( id )
    cal WaitForCompletion()
    let items = complete_info( [ 'items' ] )[ 'items' ]
    call assert_equal( 1, len( filter( items, 'v:val.abbr ==# "Foo"' ) ),
          \ 'Foo should be in the suggestions' )

    let items = complete_info( [ 'items' ] )[ 'items' ]
    call assert_equal( 1,
          \ len( filter( items, 'v:val.word ==# "__FUNCTION__"' ) ),
          \ '__FUNCTION__ should be in the suggestions' )

    call feedkeys( "\<ESC>" )
  endfunction

  call FeedAndCheckMain( "i\<C-Space>", funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
endfunction

function! Test_Select_Next_Previous()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp', {} )

  call setpos( '.', [ 0, 11, 6 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check( id )
    call WaitForCompletion()

    call CheckCurrentLine( '  foo.' )
    call CheckCompletionItemsContainsExactly( [ 'c', 'x', 'y' ] )

    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call CheckCurrentLine( '  foo.c' )
    call CheckCompletionItemsContainsExactly( [ 'c', 'x', 'y' ] )

    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call WaitForCompletion()
    call CheckCurrentLine( '  foo.x' )
    call CheckCompletionItemsContainsExactly( [ 'c', 'x', 'y' ] )

    call FeedAndCheckAgain( "\<BS>y", funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call WaitForCompletion()
    call CheckCurrentLine( '  foo.y' )
    call CheckCompletionItemsContainsExactly( [ 'y' ] )
    call feedkeys( "\<ESC>" )
  endfunction

  call FeedAndCheckMain( 'cl.', funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
endfunction

function! Test_Enter_Delete_Chars_Updates_Filter()
  call youcompleteme#test#setup#OpenFile(
        \ 'test/testdata/cpp/completion.cc', {} )

  call setpos( '.', [ 0, 23, 31 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check1( id )
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'colourOfLine', 'lengthOfLine' ] )
    call FeedAndCheckAgain( "\<BS>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [
          \ 'operator=(…)',
          \ 'colourOfLine',
          \ 'lengthOfLine',
          \ 'RED_AND_YELLOW' ] )
    call FeedAndCheckAgain( 'w', funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'RED_AND_YELLOW' ] )
    " now type something that doesnt match
    call FeedAndCheckAgain( 'this_does_not_match', funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call WaitForAssert( { -> assert_false( pumvisible() ) } )
    call CheckCurrentLine(
          \ '  p->line.colourOfLine = Line::owthis_does_not_match' )
    call CheckCompletionItemsContainsExactly( [] )
    call feedkeys( "\<Esc>" )
  endfunction

  call FeedAndCheckMain( 'cl:ol', funcref( 'Check1' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
endfunction

function! SetUp_Test_Compl_No_Filetype()
  call youcompleteme#test#setup#PushGlobal( 'ycm_filetype_whitelist', {
        \ '*': 1,
        \ 'ycm_nofiletype': 1
        \ } )
  call youcompleteme#test#setup#PushGlobal( 'ycm_filetype_blacklist', {} )
endfunction

function! Test_Compl_No_Filetype()
  call assert_false( has_key( g:ycm_filetype_blacklist, 'ycm_nofiletype' ) )
  enew
  call setline( '.', 'hello this is some text ' )

  " Even when fileytpe is set to '', the filetype autocommand is triggered, but
  " apparently, _not_ within this function.
  doautocmd FileType
  call assert_equal( 1, b:ycm_completing )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! Check( id ) closure
    call assert_equal( getline( '2' ), 'hell' )
    call WaitForCompletion()
    let items = complete_info().items
    call map( items, {index, value -> value.word} )
    call assert_equal( [ 'hello' ], items )
    call feedkeys( "\<ESC>" )
  endfunction

  call FeedAndCheckMain( 'ohell', funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  delfunc! Check
endfunction

function! TearDown_Test_Compl_No_Filetype()
  call youcompleteme#test#setup#PopGlobal( 'ycm_filetype_whitelist' )
  call youcompleteme#test#setup#PopGlobal( 'ycm_filetype_blacklist' )
endfunction

function! Test_Compl_No_Filetype_Blacklisted()
  call assert_true( has_key( g:ycm_filetype_blacklist, 'ycm_nofiletype' ) )

  enew
  call setline( '.', 'hello this is some text ' )

  " Even when fileytpe is set to '', the filetype autocommand is triggered, but
  " apparently, _not_ within this function.
  doautocmd FileType
  call assert_false( exists( 'b:ycm_completing' ) )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! Check( id ) closure
    call assert_false( pumvisible() )
    call feedkeys( "\<ESC>" )
  endfunction

  call FeedAndCheckMain( 'ohell', funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  delfunc! Check
endfunction

function! OmniFuncTester( findstart, query )
  if a:findstart
    return s:omnifunc_start_col
  endif
  return s:omnifunc_items
endfunction

function! SetUp_Test_OmniComplete_Filter()
  call youcompleteme#test#setup#PushGlobal( 'ycm_semantic_triggers', {
        \ 'omnifunc_test': [ ':', '.' ]
        \ } )
endfunction

function! Test_OmniComplete_Filter()
  enew
  setf omnifunc_test
  set omnifunc=OmniFuncTester

  let s:omnifunc_start_col = 3
  let s:omnifunc_items = [ 'test', 'testing', 'testy' ]

  function! Check1( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'te:te' )
    call CheckCompletionItemsContainsExactly( [ 'test', 'testy', 'testing' ],
                                            \ 'word' )
    call FeedAndCheckAgain( 'y', funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'te:tey' )
    call CheckCompletionItemsContainsExactly( [ 'testy' ], 'word' )
    call FeedAndCheckAgain( "\<C-n>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'te:testy' )
    call CheckCompletionItemsContainsExactly( [ 'testy' ], 'word' )
    call FeedAndCheckAgain( "\<C-p>", funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'te:tey' )
    call CheckCompletionItemsContainsExactly( [ 'testy' ], 'word' )
    call feedkeys( "\<Esc>" )
  endfunction

  call setline(1, 'te:' )
  call setpos( '.', [ 0, 1, 3 ] )
  call FeedAndCheckMain( 'ate', 'Check1' )
endfunction

function! TearDown_Test_OmniComplete_Filter()
  call youcompleteme#test#setup#PopGlobal( 'ycm_semantic_triggers' )
endfunction

function! Test_OmniComplete_Force()
  enew
  setf omnifunc_test
  set omnifunc=OmniFuncTester

  let s:omnifunc_start_col = 0
  let s:omnifunc_items = [ 'test', 'testing', 'testy' ]

  function! Check1( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'te' )
    call CheckCompletionItemsContainsExactly( [ 'test', 'testy', 'testing' ],
                                            \ 'word' )
    call FeedAndCheckAgain( 'y', funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'tey' )
    call CheckCompletionItemsContainsExactly( [ 'testy' ], 'word' )
    call FeedAndCheckAgain( "\<C-n>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'testy' )
    call CheckCompletionItemsContainsExactly( [ 'testy' ], 'word' )
    call FeedAndCheckAgain( "\<C-p>", funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'tey' )
    call CheckCompletionItemsContainsExactly( [ 'testy' ], 'word' )
    call feedkeys( "\<Esc>" )
  endfunction

  call setline(1, 'te' )
  call setpos( '.', [ 0, 1, 3 ] )
  call FeedAndCheckMain( "a\<C-Space>", 'Check1' )
endfunction

function! Test_Completion_FixIt()
  " There's a bug in clangd where you have to open a file which includes the
  " file you want to auto-include before it will actually auto-include that
  " file, auto_include_workaround #includes auto_include.h, so that clangd knows
  " about it
  call youcompleteme#test#setup#OpenFile(
        \ 'test/testdata/cpp/auto_include_workaround.cc', {} )

  call youcompleteme#test#setup#OpenFile(
        \ 'test/testdata/cpp/auto_include.cc', {} )

  function! Check1( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'do_a' )
    call CheckCompletionItemsContainsExactly( [ 'do_a_thing(Thing thing)',
                                 \ 'do_another_thing()' ] )
    call FeedAndCheckAgain( "\<Tab>" , funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call CheckCurrentLine( 'do_a_thing' )
    call CheckCompletionItemsContainsExactly( [ 'do_a_thing(Thing thing)',
                                 \ 'do_another_thing()' ] )
    call FeedAndCheckAgain( '(' , funcref( 'Check3' ) )
  endfunction


  function! Check3( id )
    call WaitForAssert( {-> assert_false( pumvisible(), 'pumvisible()' ) } )
    call CheckCurrentLine( 'do_a_thing(' )
    call assert_equal( '#include "auto_include.h"', getline( 1 ) )
    call feedkeys( "\<Esc>" )
  endfunction

  call setpos( '.', [ 0, 3, 1 ] )
  call FeedAndCheckMain( "Ado_a\<C-Space>", funcref( 'Check1' ) )
endfunction

function! Test_Select_Next_Previous_InsertModeMapping()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp', {} )

  call setpos( '.', [ 0, 11, 6 ] )

  inoremap <C-n> <Down>

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check( id )
    call WaitForCompletion()

    call CheckCurrentLine( '  foo.' )
    call CheckCompletionItemsContainsExactly( [ 'c', 'x', 'y' ] )

    call FeedAndCheckAgain( "\<C-n>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call CheckCurrentLine( '  foo.c' )
    call CheckCompletionItemsContainsExactly( [ 'c', 'x', 'y' ] )

    call FeedAndCheckAgain( "\<C-n>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call WaitForCompletion()
    call CheckCurrentLine( '  foo.x' )
    call CheckCompletionItemsContainsExactly( [ 'c', 'x', 'y' ] )

    call FeedAndCheckAgain( "\<BS>a", funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call CheckCurrentLine( '  foo.a' )
    call CheckCompletionItemsContainsExactly( [] )
    call FeedAndCheckAgain( "\<C-n>", funcref( 'Check5' ) )
  endfunction

  function! Check5( id )
    " The last ctrl-n moved to the next line
    call CheckCurrentLine( '}' )
    call assert_equal( [ 0, 12, 2, 0 ], getpos( '.' ) )
    call CheckCompletionItemsContainsExactly( [] )
    call feedkeys( "\<Esc>" )
  endfunction


  call FeedAndCheckMain( 'cl.', funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  iunmap <C-n>
endfunction

function! Test_Completion_WorksWithoutMovingCursor()
  call youcompleteme#test#setup#OpenFile(
        \ 'test/testdata/cpp/auto_include_workaround.cc', {} )

  function! Check( id )
    call WaitForCompletion() " We don't care about completion
                             " items, just that we didn't error
                             " while opening the completion pum
                             " without typing anything first.
    call feedkeys( "\<Esc>" )
  endfunction

  call setpos( '.', [ 0, 3, 1 ] )
  call FeedAndCheckMain( "i\<C-Space>", funcref( 'Check' ) )
endfunction

function! SetUp_Test_Manual_Trigger()
  call youcompleteme#test#setup#PushGlobal( 'ycm_auto_trigger', 0 )
endfunction

function! Test_Manual_Trigger()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp', {} )

  call setpos( '.', [ 0, 11, 6 ] )

  imap <C-d> <plug>(YCMComplete)

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check( id )
    call WaitForCompletion()

    call CheckCurrentLine( '  tfthne' )
    call CheckCompletionItemsContainsExactly( [
          \ 'test_function_that_has_no_errors' ], 'word' )

    call FeedAndCheckAgain( "\<BS>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()

    call CheckCurrentLine( '  tfthn' )
    call CheckCompletionItemsContainsExactly( [
          \ 'test_function_that_has_no_errors' ], 'word' )

    call feedkeys( "\<Esc>" )
  endfunction

  call FeedAndCheckMain( "Otfthne\<C-d>", funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  iunmap <C-d>
endfunction

function! TearDown_Test_Manual_Trigger()
  call youcompleteme#test#setup#PopGlobal( 'ycm_auto_trigger' )
endfunction

function! SetUp_Test_Manual_Trigger_CompleteFunc()
  call youcompleteme#test#setup#PushGlobal( 'ycm_auto_trigger', 0 )
endfunction

function! Test_Manual_Trigger_CompleteFunc()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp', {} )

  call setpos( '.', [ 0, 11, 6 ] )
  set completefunc=youcompleteme#CompleteFunc

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check( id )
    call WaitForCompletion()

    call CheckCurrentLine( '  tfthne' )
    call CheckCompletionItemsContainsExactly( [
          \ 'test_function_that_has_no_errors' ], 'word' )

    call FeedAndCheckAgain( "\<BS>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()

    call CheckCurrentLine( '  tfthn' )
    call CheckCompletionItemsContainsExactly( [
          \ 'test_function_that_has_no_errors' ], 'word' )

    call feedkeys( "\<Esc>" )
  endfunction

  call FeedAndCheckMain( "Otfthne\<C-x>\<C-u>", funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  set completefunc=
endfunction

function! TearDown_Test_Manual_Trigger_CompleteFunc()
  call youcompleteme#test#setup#PopGlobal( 'ycm_auto_trigger' )
endfunction
