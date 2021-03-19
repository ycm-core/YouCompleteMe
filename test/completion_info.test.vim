function! s:AssertInfoPopupNotVisible()
  call WaitForAssert( {-> assert_true(
        \ popup_findinfo() == 0 ||
        \ !popup_getpos( popup_findinfo() ).visible ) } )
endfunction

function! s:AssertInfoPopupVisible()
  call WaitForAssert( {-> assert_true(
        \ popup_findinfo() != 0 &&
        \ !empty( popup_getpos( popup_findinfo() ) ) &&
        \ popup_getpos( popup_findinfo() ).visible ) } )
endfunction

function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  let g:ycm_add_preview_to_completeopt = 'popup'

  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

exe 'source' expand( "<sfile>:p:h" ) .. '/completion.common.vim'

function! Test_Using_Ondemand_Resolve()
  let debug_info = split( execute( 'YcmDebugInfo' ), "\n" )
  enew
  setf cpp

  call assert_equal( '', &completefunc )

  for line in debug_info
    if line =~# "^-- Resolve completions: "
      let ver = substitute( line, "^-- Resolve completions: ", "", "" )
      call assert_equal( 'On demand', ver, 'API version' )
      return
    endif
  endfor

  call assert_report( "Didn't find the resolve type in the YcmDebugInfo" )

endfunction

function! Test_ResolveCompletion_OnChange()
  call SkipIf( !exists( '*popup_findinfo' ), 'no popup_findinfo' )

  " Only the java completer actually uses the completion resolve
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/java/testdata/simple_eclipse_project' .
        \ '/src/com/test/TestWithDocumentation.java', { 'delay': 15 } )

  call setpos( '.', [ 0, 6, 21 ] )
  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check1( id )
    call WaitForCompletion()
    call s:AssertInfoPopupNotVisible()
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check2', [ 0 ] ) )
  endfunction

  let found_getAString = 0

  function! Check2( counter, id ) closure
    call WaitForCompletion()
    call s:AssertInfoPopupVisible()
    let info_popup_id = popup_findinfo()

    let compl = complete_info()
    let selected = compl.items[ compl.selected ]

    " All items should be resolved
    " NOTE: Even after resolving the item still has this as there's no way to
    " update the user data of the item at this point (need a vim change to do
    " that)
    call assert_true( has_key( json_decode( selected.user_data ),
          \ 'resolve' ) )

    if selected.word ==# 'getAString'
      " It's line 5 because we truncated the signature to fit it in
      call WaitForAssert( { ->
            \ assert_equal( [ 'MethodsWithDocumentation.getAString() : String',
                            \ '',
                            \ 'getAString() : String',
                            \ '',
                            \ 'Single line description.',
                            \ ],
            \               getbufline( winbufnr( info_popup_id ), '1', '5' ) )
            \ } )
      let found_getAString += 1
    endif

    if a:counter < 10
      call FeedAndCheckAgain( "\<Tab>", funcref( 'Check2', [ a:counter + 1 ] ) )
    else
      call feedkeys( "\<Esc>" )
    endif
  endfunction

  call FeedAndCheckMain( 'cw', funcref( 'Check1' ) )

  call assert_false( pumvisible(), 'pumvisible()' )
  call assert_equal( 1, found_getAString )

  call test_override( 'ALL', 0 )
endfunction

function! Test_Resolve_FixIt()
  call SkipIf( !exists( '*popup_findinfo' ), 'no popup_findinfo' )

  " Only the java completer actually uses the completion resolve
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/java/testdata/simple_eclipse_project' .
        \ '/src/com/test/TestWithDocumentation.java', { 'delay': 15 } )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check1( id )
    call WaitForCompletion()
    call CheckCurrentLine( '    Tes' )
    call CheckCompletionItemsHasItems( [ 'Test - com.youcompleteme' ] )
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call CheckCompletionItemsHasItems( [ 'Test - com.youcompleteme' ] )
    call CheckCurrentLine( '    Test' )
    call FeedAndCheckAgain( "\<C-y>", funcref( 'Check3' ) )
  endfunction

  function! Check3( id )
    call WaitForAssert( {-> assert_false( pumvisible(), 'pumvisible()' ) } )
    call CheckCurrentLine( '    Test' )
    call assert_equal( 'import com.youcompleteme.Test;', getline( 3 ) )
    call feedkeys( "\<Esc>" )
  endfunction

  call setpos( '.', [ 0, 7, 1 ] )
  call FeedAndCheckMain( "oTes\<C-space>", funcref( 'Check1' ) )

  call test_override( 'ALL', 0 )
endfunction

function! Test_DontResolveCompletion_AlreadyResolved()
  call SkipIf( !exists( '*popup_findinfo' ), 'no popup_findinfo' )

  " Only the java completer actually uses the completion resolve
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/java/testdata/simple_eclipse_project' .
        \ '/src/com/test/TestWithDocumentation.java', { 'delay': 15 } )

  call setpos( '.', [ 0, 7, 12 ] )
  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check1( id )
    call WaitForCompletion()
    call CheckCompletionItemsContainsExactly( [ 'hashCode' ], 'word' )
    call s:AssertInfoPopupNotVisible()
    call assert_equal( -1, complete_info().selected )

    let compl = complete_info()
    let hashCode = compl.items[ 0 ]
    call assert_equal( 1, len( compl.items ) )
    call assert_equal( 'hashCode', hashCode.word )
    call assert_false( has_key( json_decode( hashCode.user_data ),
          \ 'resolve' ) )

    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call s:AssertInfoPopupVisible()

    let compl = complete_info()
    let selected = compl.items[ 0 ]
    call assert_equal( 1, len( compl.items ) )
    call assert_equal( 'hashCode', selected.word )
    call assert_false( has_key( json_decode( selected.user_data ),
          \ 'resolve' ) )
    call feedkeys( "\<Esc>" )
  endfunction

  call FeedAndCheckMain( 'C', funcref( 'Check1' ) )

  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
endfunction
