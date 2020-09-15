function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  " Use the default, which _should_ be the new API
  unlet! g:ycm_use_completion_api

  let g:ycm_add_preview_to_completeopt = 'popup'

  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

exe 'source' expand( "<sfile>:p:h" ) .. '/completion.common.vim'

function! Test_ResolveCompletion_OnChange()
  " Only the java completer actually uses the completion resolve
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/java/testdata/simple_eclipse_project' .
        \ '/src/com/test/MethodsWithDocumentation.java', { 'delay': 15 } )

  call setpos( '.', [ 0, 33, 20 ] )
  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check1( id )
    call WaitForCompletion()
    call assert_equal( 0, popup_findinfo() )
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check2', [ 0 ] ) )
  endfunction

  let found_getAString = 0

  function! Check2( counter, id ) closure
    call WaitForCompletion()
    let info_popup_id = popup_findinfo()
    call assert_notequal( 0, info_popup_id )
    call WaitForAssert( { ->
          \ assert_true( popup_getpos( info_popup_id ).visible )
          \ } )

    let compl = complete_info()
    let selected = compl.items[ compl.selected ]

    if selected.word ==# 'getAString'
      redraw!
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

  call FeedAndCheckMain( 'C.', funcref( 'Check1' ) )

  call assert_false( pumvisible(), 'pumvisible()' )
  call assert_equal( 1, found_getAString )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunction

function! Test_DontResolveCompletion_AlreadyResolved()
  " Only the java completer actually uses the completion resolve
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/java/testdata/simple_eclipse_project' .
        \ '/src/com/test/MethodsWithDocumentation.java', { 'delay': 15 } )

  call setpos( '.', [ 0, 34, 12 ] )
  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  function! Check1( id )
    call WaitForCompletion()
    call CheckCompletionItems( [ 'hashCode' ], 'word' )
    call assert_equal( -1, complete_info().selected )
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check2' ) )
  endfunction

  function! Check2( id )
    call WaitForCompletion()
    call WaitForAssert( { ->
          \ assert_notequal( 0, popup_findinfo() )
          \ } )
    call WaitForAssert( { ->
          \ assert_true( popup_getpos( popup_findinfo() ).visible )
          \ } )

    let compl = complete_info()
    let selected = compl.items[ 0 ]
    call assert_equal( 1, len( compl.items ) )
    call assert_equal( 'hashCode', selected.word )

    " It's line 5 because we truncated the signature to fit it in
    let doc_line = getbufline( winbufnr( popup_findinfo() ), '3' )[ 0 ]
    call assert_match( '^Returns a hash code value', doc_line )

    call feedkeys( "\<Esc>" )
  endfunction

  call FeedAndCheckMain( 'C', funcref( 'Check1' ) )

  call assert_false( pumvisible(), 'pumvisible()' )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunction
