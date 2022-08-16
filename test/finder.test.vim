function! SetUp()
  let g:ycm_use_clangd = 1
  call youcompleteme#test#setup#SetUp()
  nmap <leader><leader>w <Plug>(YCMFindSymbolInWorkspace)
  nmap <leader><leader>d <Plug>(YCMFindSymbolInDocument)
endfunction

function! TearDown()
endfunction

function! Test_WorkspaceSymbol_Basic()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  let popup_id = -1

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    " TODO: Wait for the popup to be displayed, and check the contents
    call FeedAndCheckAgain( 'thisisathing', funcref( 'SelectItem' ) )
  endfunction

  function SelectItem( ... )
    let id = youcompleteme#finder#GetState().id

    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thisisathing ',
          \ popup_getoptions( id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', id ) ) } )

    call feedkeys( "\<CR>" )
  endfunction

  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInWorkspace)
  call FeedAndCheckMain( '\\w', funcref( 'PutQuery' ) )

  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( b, bufnr() )
  call assert_equal( [ 0, 5, 7, 0 ], getpos( '.' ) )

  delfunct PutQuery
  delfunct SelectItem
  silent %bwipe!
endfunction

function! Test_DocumentSymbols_Basic()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  let popup_id = -1

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    " TODO: Wait for the popup to be displayed, and check the contents
    call FeedAndCheckAgain( 'thisisathing', funcref( 'SelectItem' ) )
  endfunction

  function SelectItem( ... )
    let id = youcompleteme#finder#GetState().id

    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thisisathing ',
          \ popup_getoptions( id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', id ) ) } )

    call feedkeys( "\<CR>" )
  endfunction

  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInDocument)
  call FeedAndCheckMain( '\\d', funcref( 'PutQuery' ) )

  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( b, bufnr() )
  " NOTE: cland returns the position of the decl here not the identifier. This
  " is why it's position 3 not 7 as in the Test_WorkspaceSymbol_Basic
  call assert_equal( [ 0, 5, 3, 0 ], getpos( '.' ) )

  delfunct PutQuery
  delfunct SelectItem
  silent %bwipe!
endfunction

function! Test_Cancel_DocumentSymbol()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  " Jump to a different position so that we can ensure we return to the same
  " place
  normal! G
  let p = getpos( '.' )

  let popup_id = -1

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    call FeedAndCheckAgain( 'thisisathing', funcref( 'SelectItem' ) )
  endfunction

  function SelectItem( ... )
    let id = youcompleteme#finder#GetState().id

    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thisisathing ',
          \ popup_getoptions( id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', id ) ) } )

    " Cancel - this should stopinsert
    call feedkeys( "\<C-c>" )
  endfunction

  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInDocument)
  call FeedAndCheckMain( '\\d', funcref( 'PutQuery' ) )

  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( b, bufnr() )

  " Retuned to just where we started
  call assert_equal( p, getpos( '.' ) )

  delfunct PutQuery
  delfunct SelectItem
  silent %bwipe!
endfunction

function! Test_EmptySearch()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  let popup_id = -1

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    " TODO: Wait for the popup to be displayed, and check the contents
    call FeedAndCheckAgain( 'nothingshouldmatchthis',
                          \ funcref( 'SelectNothing' ) )
  endfunction

  function SelectNothing( ... )
    let id = youcompleteme#finder#GetState().id

    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: nothingshouldmatchthis ',
          \ popup_getoptions( id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', id ) ) } )

    call assert_equal( 'No results', getbufline( winbufnr( id ), '$' )[ 0 ] )
    call FeedAndCheckAgain( "\<CR>notarealthing",
                          \ funcref( 'ChangeSearch' ) )
  endfunction

  function ChangeSearch( ... )
    let id = youcompleteme#finder#GetState().id

    " Hitting enter with nothing to select clears the prompt, because prompt
    " buffer
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: notarealthing ',
          \ popup_getoptions( id ).title  ) },
          \ 10000 )
    call assert_equal( 'No results', getbufline( winbufnr( id ), '$' )[ 0 ] )

    call assert_equal( -1, youcompleteme#finder#GetState().selected )

    call FeedAndCheckAgain( "\<C-u>tiat", funcref( 'TestUpDownSelect' ) )
  endfunction

  let popup_id = -1
  function TestUpDownSelect( ... ) closure
    let popup_id = youcompleteme#finder#GetState().id

    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: tiat ',
          \ popup_getoptions( popup_id ).title  ) },
          \ 10000 )
    call WaitForAssert( { -> assert_equal( 2, line( '$', popup_id ) ) } )

    " FIXME: Doing all these tests with only 2 entries means that it's not
    " really checking the behaviour completely accurately, we should at least
    " use 3, but that would require crafting a new test file, which is nonzero
    " effort. Well, it's probably as much effort as writing this comment...

    " Check down movement
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<C-j>", 'xt' )
    call assert_equal( 1, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<Down>", 'xt' )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<Tab>", 'xt' )
    call assert_equal( 1, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<C-n>", 'xt' )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    " Check up movement and wrapping
    call feedkeys( "\<C-k>", 'xt' )
    call assert_equal( 1, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<Up>", 'xt' )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<S-Tab>", 'xt' )
    call assert_equal( 1, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<C-p>", 'xt' )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<Tab>", 'xt' )
    call assert_equal( 1, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<Home>", 'xt' )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<End>", 'xt' )
    call assert_equal( 1, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<End>", 'xt' )
    call assert_equal( 1, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<PageUp>", 'xt' )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<PageDown>", 'xt' )
    call assert_equal( 1, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<CR>" )
  endfunction

  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInWorkspace)
  call FeedAndCheckMain( '\\w', funcref( 'PutQuery' ) )

  call WaitForAssert( { -> assert_equal( {}, popup_getpos( popup_id ) ) } )
  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( b, bufnr() )
  call assert_equal( [ 0, 5, 28, 0 ], getpos( '.' ) )

  " We pop up a notification with some text in it
  if exists( '*popup_list' )
    call assert_equal( 1, len( popup_list() ) )
  endif

  " Old vim doesn't have popup_list, so hit-test the top-right corner which is
  " where we pup the popu
  let notification_id = popup_locate( 1, &columns - 1 )
  call assert_equal( [ 'Added 2 entries to quickfix list.' ],
                   \ getbufline( winbufnr( notification_id ), 1, '$' ) )
  " Wait for the notification to clear
  call WaitForAssert(
        \ { -> assert_equal( {}, popup_getpos( notification_id ) ) },
        \ 10000 )

  delfunct PutQuery
  delfunct SelectNothing
  delfunct ChangeSearch
  delfunct TestUpDownSelect
  silent %bwipe!
endfunction

function! Test_LeaveWindow_CancelSearch()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  " Jump to a different position so that we can ensure we return to the same
  " place
  normal! G
  let p = getpos( '.' )

  let popup_id = -1

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    call feedkeys( "\<C-w>w" )
  endfunction

  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInWorkspace)
  call FeedAndCheckMain( '\\w', funcref( 'PutQuery' ) )

  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( b, bufnr() )

  " Retuned to just where we started
  call assert_equal( p, getpos( '.' ) )

  " No notifiaction
  if exists( '*popup_list' )
    call assert_equal( 0, len( popup_list() ) )
  endif

  delfunct PutQuery
  silent %bwipe!
endfunction


function! SetUp_Test_NoFileType_NoCompletionIn_PromptBuffer()
  call youcompleteme#test#setup#PushGlobal( 'ycm_filetype_whitelist', {
        \ '*': 1,
        \ 'ycm_nofiletype': 1
        \ } )
endfunction

function! TearDown_Test_NoFileType_NoCompletionIn_PromptBuffer()
  call youcompleteme#test#setup#PopGlobal( 'ycm_filetype_whitelist' )
endfunction

function! Test_NoFileType_NoCompletionIn_PromptBuffer()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )

  call test_override( 'char_avail', 1 )

  new
  call feedkeys(
        \ 'iThis is some text and so is thisisathing this_is_a_thing',
        \ 'xt' )
  wincmd w

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  let popup_id = -1

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    " TODO: Wait for the popup to be displayed, and check the contents
    call FeedAndCheckAgain( 'thisisathing', funcref( 'CheckNoPopup' ) )
  endfunction

  function! CheckNoPopup( ... )
    let id = youcompleteme#finder#GetState().id

    call WaitForAssert( { ->
            \ assert_equal( ' [X] Search for symbol: thisisathing ',
            \ popup_getoptions( id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', id ) ) } )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    " Check there is no PUM - we disable completion in the prompt buffer
    call assert_false( pumvisible() )

    call feedkeys( "\<CR>" )
  endfunction

  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInWorkspace)
  call FeedAndCheckMain( '\\w', funcref( 'PutQuery' ) )

  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( b, bufnr() )
  call assert_equal( [ 0, 5, 7, 0 ], getpos( '.' ) )

  call test_override( 'ALL', 0 )
  silent %bwipe!
  delfunct! PutQuery
  delfunct! CheckNoPopup
endfunction

function! Test_MultipleFileTypes()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )
  split
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )
  wincmd w

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    let popup_id = youcompleteme#finder#GetState().id
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thiswillnotmatchanything ',
          \ popup_getoptions( popup_id ).title  ) },
          \ 10000 )


    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    let id = youcompleteme#finder#GetState().id
    call assert_equal( 'No results', getbufline( winbufnr( id ), '$' )[ 0 ] )
    call FeedAndCheckAgain( "\<C-u>thisisathing", funcref( 'CheckCpp' ) )
  endfunction

  function! CheckCpp( ... )
    let popup_id = youcompleteme#finder#GetState().id

    " Python can be _really_ slow
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thisisathing ',
          \ popup_getoptions( popup_id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', popup_id ) ) } )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call FeedAndCheckAgain(
          \ "\<C-u>Really_Long_Method",
          \ funcref( 'CheckPython' ) )
  endfunction

  function! CheckPython( ... )
    let popup_id = youcompleteme#finder#GetState().id

    " Python can be _really_ slow
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: Really_Long_Method ',
          \ popup_getoptions( popup_id ).title ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 2, line( '$', popup_id ) ) },
                      \ 10000 )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'def Really_Long_Method',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].description )

    " Toggle single-filetype mode
    call FeedAndCheckAgain( "\<C-f>", funcref( 'CheckCppAgain' ) )
  endfunction

  function! CheckCppAgain( ... )
    let popup_id = youcompleteme#finder#GetState().id

    " Python can be _really_ slow
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: Really_Long_Method ',
          \ popup_getoptions( popup_id ).title ) },
          \ 10000 )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    let id = youcompleteme#finder#GetState().id
    call assert_equal( 'No results', getbufline( winbufnr( id ), '$' )[ 0 ] )

    " And back to multiple filetypes
    call FeedAndCheckAgain( "\<C-f>", funcref( 'CheckPythonAgain' ) )
  endfunction

  function! CheckPythonAgain( ... )
    let popup_id = youcompleteme#finder#GetState().id

    " Python can be _really_ slow
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: Really_Long_Method ',
          \ popup_getoptions( popup_id ).title ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 2, line( '$', popup_id ) ) },
                      \ 10000 )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'def Really_Long_Method',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].description )

    call feedkeys( "\<C-c>" )
  endfunction


  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInWorkspace)
  call FeedAndCheckMain( '\\wthiswillnotmatchanything', funcref( 'PutQuery' ) )

  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( b, bufnr() )
endfunction

function! Test_MultipleFileTypes_CurrentNotSemantic()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )
  split
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )
  split
  " Current buffer is a ycm_nofiletype, which ycm is blacklisted in
  " but otherwise we behave the same as before with the exception that we open
  " the python file in the current window

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    let popup_id = youcompleteme#finder#GetState().id
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thiswillnotmatchanything ',
          \ popup_getoptions( popup_id ).title  ) },
          \ 10000 )


    let id = youcompleteme#finder#GetState().id
    call assert_equal( 'No results', getbufline( winbufnr( id ), '$' )[ 0 ] )
    call FeedAndCheckAgain( "\<C-u>thisisathing", funcref( 'CheckCpp' ) )
  endfunction

  function! CheckCpp( ... )
    let popup_id = youcompleteme#finder#GetState().id

    " Python can be _really_ slow
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thisisathing ',
          \ popup_getoptions( popup_id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', popup_id ) ) } )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call FeedAndCheckAgain(
          \ "\<C-u>Really_Long_Method",
          \ funcref( 'CheckPython' ) )
  endfunction

  function! CheckPython( ... )
    let popup_id = youcompleteme#finder#GetState().id

    " Python can be _really_ slow
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: Really_Long_Method ',
          \ popup_getoptions( popup_id ).title ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 2, line( '$', popup_id ) ) },
                      \ 10000 )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'def Really_Long_Method',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].description )

    call feedkeys( "\<CR>")
  endfunction


  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInWorkspace)
  call FeedAndCheckMain( '\\wthiswillnotmatchanything', funcref( 'PutQuery' ) )

  " We pop up a notification with some text in it
  if exists( '*popup_list' )
    call assert_equal( 1, len( popup_list() ) )
  endif

  " Old vim doesn't have popup_list, so hit-test the top-right corner which is
  " where we pup the popu
  let notification_id = popup_locate( 1, &columns - 1 )
  call assert_equal( [ 'Added 2 entries to quickfix list.' ],
                   \ getbufline( winbufnr( notification_id ), 1, '$' ) )
  " Wait for the notification to clear
  call WaitForAssert(
        \ { -> assert_equal( {}, popup_getpos( notification_id ) ) },
        \ 10000 )

  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( bufnr( 'doc.py' ), bufnr() )
  call assert_equal( [ 0, 16, 5, 0 ], getpos( '.' ) )
endfunction

function! Test_WorkspaceSymbol_NormalModeChange()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/cpp/complete_with_sig_help.cc', {} )

  let original_win = winnr()
  let b = bufnr()
  let l = winlayout()

  let popup_id = -1

  function! PutQuery( ... )
    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call WaitForAssert( { -> assert_true(
          \ youcompleteme#finder#GetState().id != -1 ) } )

    let popup_id = youcompleteme#finder#GetState().id
    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thiswillnotmatchanything ',
          \ popup_getoptions( popup_id ).title  ) },
          \ 10000 )

    let id = youcompleteme#finder#GetState().id
    call assert_equal( 'No results', getbufline( winbufnr( id ), '$' )[ 0 ] )
    call FeedAndCheckAgain( "\<C-u>thisisathing", funcref( 'ChangeQuery' ) )
  endfunction

  function ChangeQuery( ... )
    let id = youcompleteme#finder#GetState().id

    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thisisathing ',
          \ popup_getoptions( id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', id ) ) } )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'this_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    " Wait for the current buffer to be a prompt buffer
    call WaitForAssert( { -> assert_equal( 'prompt', &buftype ) } )
    call WaitForAssert( { -> assert_equal( 'i', mode() ) } )

    call FeedAndCheckAgain( "\<Esc>bcwthatisathing",
                          \ funcref( 'SelectNewItem' ) )
  endfunction

  function SelectNewItem( ... )
    let id = youcompleteme#finder#GetState().id

    call WaitForAssert( { ->
          \ assert_equal( ' [X] Search for symbol: thatisathing ',
          \ popup_getoptions( id ).title  ) },
          \ 10000 )

    call WaitForAssert( { -> assert_equal( 1, line( '$', id ) ) } )
    call assert_equal( 0, youcompleteme#finder#GetState().selected )
    call assert_equal( 'that_is_a_thing',
          \ youcompleteme#finder#GetState().results[
          \   youcompleteme#finder#GetState().selected ].extra_data.name )

    call feedkeys( "\<CR>" )
  endfunction

  " <Leader> is \ - this calls <Plug>(YCMFindSymbolInWorkspace)
  call FeedAndCheckMain( '\\wthiswillnotmatchanything', funcref( 'PutQuery' ) )

  call WaitForAssert( { -> assert_equal( l, winlayout() ) } )
  call WaitForAssert( { -> assert_equal( original_win, winnr() ) } )
  call assert_equal( b, bufnr() )
  call assert_equal( [ 0, 5, 28, 0 ], getpos( '.' ) )

  delfunct PutQuery
  delfunct SelectNewItem
  delfunct ChangeQuery
  silent %bwipe!
endfunction
