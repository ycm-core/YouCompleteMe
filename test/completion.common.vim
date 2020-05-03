function! s:CheckCompletionItems( expected_props, ... )
  let prop = 'abbr'
  if a:0 > 0
    let prop = a:1
  endif

  let items = complete_info( [ 'items' ] )[ 'items' ]
  let abbrs = []
  for item in items
    call add( abbrs, get( item, prop ) )
  endfor

  call assert_equal( a:expected_props,
        \ abbrs,
        \ 'not matched: '
        \ .. string( a:expected_props )
        \ .. ' against '
        \ .. prop
        \ .. ' in '
        \ .. string( items )
        \ .. ' matching '
        \ .. string( abbrs ) )
endfunction

function! s:FeedAndCheckMain( keys, func )
  call timer_start( 500, a:func )
  call feedkeys( a:keys, 'tx!' )
endfunction

function! s:FeedAndCheckAgain( keys, func )
  call timer_start( 500, a:func )
  call feedkeys( a:keys )
endfunction

function! s:WaitForCompletion()
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
endfunction

function! s:CheckCurrentLine( expected_value )
  return assert_equal( a:expected_value, getline( '.' ) )
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
    call s:WaitForCompletion()
    call feedkeys( "\<ESC>" )
  endfunction

  call s:FeedAndCheckMain( 'cl.', funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunctio

function! Test_Force_Semantic_TopLevel()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp', {} )

  call setpos( '.', [ 0, 17, 5 ] )

  function! Check( id )
    cal s:WaitForCompletion()
    let items = complete_info( [ 'items' ] )[ 'items' ]
    call assert_equal( 1, len( filter( items, 'v:val.abbr ==# "Foo"' ) ),
          \ 'Foo should be in the suggestions' )

    let items = complete_info( [ 'items' ] )[ 'items' ]
    call assert_equal( 1,
          \ len( filter( items, 'v:val.word ==# "__FUNCTION__"' ) ),
          \ '__FUNCTION__ should be in the suggestions' )

    call feedkeys( "\<ESC>" )
  endfunction

  call s:FeedAndCheckMain( "i\<C-Space>", funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunction

function! Test_Select_Next_Previous()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/clangd/testdata/basic.cpp', {} )

  call setpos( '.', [ 0, 11, 6 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check( id )
    call s:WaitForCompletion()

    call s:CheckCurrentLine( '  foo.' )
    call s:CheckCompletionItems( [ 'c', 'x', 'y' ] )

    call s:FeedAndCheckAgain( "\<Tab>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( '  foo.c' )
    call s:CheckCompletionItems( [ 'c', 'x', 'y' ] )

    call s:FeedAndCheckAgain( "\<Tab>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( '  foo.x' )
    call s:CheckCompletionItems( [ 'c', 'x', 'y' ] )

    call s:FeedAndCheckAgain( "\<BS>y", funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( '  foo.y' )
    call s:CheckCompletionItems( [ 'y' ] )
    call feedkeys( "\<ESC>" )
  endfunction

  call s:FeedAndCheckMain( 'cl.', funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunction

function! Test_Enter_Delete_Chars_Updates_Filter()
  call youcompleteme#test#setup#OpenFile(
        \ 'test/testdata/cpp/completion.cc', {} )

  call setpos( '.', [ 0, 23, 31 ] )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check1( id )
    call s:WaitForCompletion()
    call s:CheckCompletionItems( [ 'colourOfLine', 'lengthOfLine' ] )
    call s:FeedAndCheckAgain( "\<BS>", funcref( "Check2" ) )
  endfunction

  function! Check2( id )
    call s:WaitForCompletion()
    call s:CheckCompletionItems( [
          \ 'operator=(…)',
          \ 'colourOfLine',
          \ 'lengthOfLine',
          \ 'RED_AND_YELLOW' ] )
    call s:FeedAndCheckAgain( 'w', funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call s:WaitForCompletion()
    call s:CheckCompletionItems( [ 'RED_AND_YELLOW' ] )
    " now type something that doesnt match
    call s:FeedAndCheckAgain( 'this_does_not_match', funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call WaitForAssert( { -> assert_false( pumvisible() ) } )
    call s:CheckCurrentLine(
          \ '  p->line.colourOfLine = Line::owthis_does_not_match' )
    call s:CheckCompletionItems( [] )
    call feedkeys( "\<Esc>" )
  endfunction

  call s:FeedAndCheckMain( 'cl:ol', funcref( 'Check1' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunction

function! OmniFuncTester( findstart, query )
  if a:findstart
    return s:omnifunc_start_col
  endif
  return s:omnifunc_items
endfunction

function! SetUp_Test_OmniComplete_Filter()
  let g:ycm_semantic_triggers = {
        \ 'omnifunc_test': [ ':', '.' ]
        \ }
endfunction

function! Test_OmniComplete_Filter()
  enew
  setf omnifunc_test
  set omnifunc=OmniFuncTester

  let s:omnifunc_start_col = 3
  let s:omnifunc_items = [ 'test', 'testing', 'testy' ]

  function! Check1( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'te:te' )
    call s:CheckCompletionItems( [ 'test', 'testy', 'testing' ], 'word' )
    call s:FeedAndCheckAgain( 'y', funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'te:tey' )
    call s:CheckCompletionItems( [ 'testy' ], 'word' )
    call s:FeedAndCheckAgain( "\<C-n>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'te:testy' )
    call s:CheckCompletionItems( [ 'testy' ], 'word' )
    call s:FeedAndCheckAgain( "\<C-p>", funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'te:tey' )
    call s:CheckCompletionItems( [ 'testy' ], 'word' )
    call feedkeys( "\<Esc>" )
  endfunction

  call setline(1, 'te:' )
  call setpos( '.', [ 0, 1, 3 ] )
  call s:FeedAndCheckMain( 'ate', 'Check1' )

  %bwipeout!
endfunction

function! TearDown_Test_OmniComplete_Filter()
  unlet g:ycm_semantic_triggers
endfunction

function! Test_OmniComplete_Force()
  enew
  setf omnifunc_test
  set omnifunc=OmniFuncTester

  let s:omnifunc_start_col = 0
  let s:omnifunc_items = [ 'test', 'testing', 'testy' ]

  function! Check1( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'te' )
    call s:CheckCompletionItems( [ 'test', 'testy', 'testing' ], 'word' )
    call s:FeedAndCheckAgain( 'y', funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'tey' )
    call s:CheckCompletionItems( [ 'testy' ], 'word' )
    call s:FeedAndCheckAgain( "\<C-n>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'testy' )
    call s:CheckCompletionItems( [ 'testy' ], 'word' )
    call s:FeedAndCheckAgain( "\<C-p>", funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'tey' )
    call s:CheckCompletionItems( [ 'testy' ], 'word' )
    call feedkeys( "\<Esc>" )
  endfunction

  call setline(1, 'te' )
  call setpos( '.', [ 0, 1, 3 ] )
  call s:FeedAndCheckMain( "a\<C-Space>", 'Check1' )
  %bwipeout!
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

  function Check1( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'do_a' )
    call s:CheckCompletionItems( [ 'do_a_thing(Thing thing)',
                                 \ 'do_another_thing()' ] )
    call s:FeedAndCheckAgain( "\<Tab>" , funcref( 'Check2' ) )
  endfunction

  function Check2( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( 'do_a_thing' )
    call s:CheckCompletionItems( [ 'do_a_thing(Thing thing)',
                                 \ 'do_another_thing()' ] )
    call s:FeedAndCheckAgain( '(' , funcref( 'Check3' ) )
  endfunction


  function Check3( id )
    call WaitForAssert( {-> assert_false( pumvisible(), 'pumvisible()' ) } )
    call s:CheckCurrentLine( 'do_a_thing(' )
    call assert_equal( '#include "auto_include.h"', getline( 1 ) )
    call feedkeys( "\<Esc>" )
  endfunction


  call setpos( '.', [ 0, 3, 1 ] )
  call s:FeedAndCheckMain( "Ado_a\<C-Space>", funcref( 'Check1' ) )

  %bwipeout!
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
    call s:WaitForCompletion()

    call s:CheckCurrentLine( '  foo.' )
    call s:CheckCompletionItems( [ 'c', 'x', 'y' ] )

    call s:FeedAndCheckAgain( "\<C-n>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( '  foo.c' )
    call s:CheckCompletionItems( [ 'c', 'x', 'y' ] )

    call s:FeedAndCheckAgain( "\<C-n>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call s:WaitForCompletion()
    call s:CheckCurrentLine( '  foo.x' )
    call s:CheckCompletionItems( [ 'c', 'x', 'y' ] )

    call s:FeedAndCheckAgain( "\<BS>a", funcref( 'Check4' ) )
  endfunction

  function! Check4( id )
    call s:CheckCurrentLine( '  foo.a' )
    call s:CheckCompletionItems( [] )
    call s:FeedAndCheckAgain( "\<C-n>", funcref( 'Check5' ) )
  endfunction

  function! Check5( id )
    " The last ctrl-n moved to the next line
    call s:CheckCurrentLine( '}' )
    call assert_equal( [ 0, 12, 2, 0 ], getpos( '.' ) )
    call s:CheckCompletionItems( [] )
    call feedkeys( "\<Esc>" )
  endfunction


  call s:FeedAndCheckMain( 'cl.', funcref( 'Check' ) )
  " Checks run in insert mode, then exit insert mode.
  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  iunmap <C-n>
  %bwipeout!
endfunction
