function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'
  nmap <leader>D <Plug>(YCMHover)
  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  let g:ycm_auto_hover='CursorHold'
endfunction

function! Test_Hover_Uses_GetDoc()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )

  call assert_equal( 'python', &syntax )

  " no doc
  call setpos( '.', [ 0, 1, 1 ] )
  doautocmd CursorHold
  call assert_equal( { 'command': 'GetDoc', 'syntax': '' }, b:ycm_hover )

  let loc = screenpos( win_getid(), 2, 1 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )
  let loc = screenpos( win_getid(), 2, 2 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  " some doc - autocommand
  call setpos( '.', [ 0, 12, 3 ] )
  doautocmd CursorHold
  let loc = screenpos( win_getid(), 11, 4 )
  let popup = popup_locate( loc.row, loc.col )
  call assert_notequal( 0, popup )
  call assert_equal( [ 'Test_OneLine()', '', 'This is the one line output.' ],
                   \ getbufline( winbufnr( popup ), 1, '$' ) )
  call assert_equal( '', getbufvar( winbufnr( popup ), '&syntax' ) )
  call popup_clear()

  " some doc - mapping
  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  let popup = popup_locate( loc.row, loc.col )
  call assert_notequal( 0, popup )
  call assert_equal( [ 'Test_OneLine()', '', 'This is the one line output.' ],
                   \ getbufline( winbufnr( popup ), 1, '$' ) )
  call assert_equal( '', getbufvar( winbufnr( popup ), '&syntax' ) )

  call popup_clear()
  %bwipe!
endfunction

function! Test_Hover_Uses_GetHover()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )
  py3 <<EOPYTHON
from unittest import mock
with mock.patch.object( ycm_state,
                        'GetDefinedSubcommands',
                        return_value = [ 'GetHover' ] ):
  vim.command( 'doautocmd CursorHold' )
EOPYTHON

  call assert_equal( { 'command': 'GetHover', 'syntax': 'markdown' },
                   \ b:ycm_hover )

  " Only the generic LSP completer supports the GetHover response, so i guess we
  " test the error condition here...

  " Python desn't support GetHover
  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  cal assert_equal( 0, popup_locate( loc.row, loc.col ) )

  call popup_clear()
  %bwipe!
endfunction

function! Test_Hover_Uses_None()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )
  py3 <<EOPYTHON
from unittest import mock
with mock.patch.object( ycm_state, 'GetDefinedSubcommands', return_value = [] ):
  vim.command( 'doautocmd CursorHold' )
EOPYTHON

  call assert_equal( {}, b:ycm_hover )

  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  cal assert_equal( 0, popup_locate( loc.row, loc.col ) )

  call popup_clear()
  %bwipe!
endfunction

function! Test_Hover_Uses_GetType()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )

  py3 <<EOPYTHON
from unittest import mock
with mock.patch.object( ycm_state,
                        'GetDefinedSubcommands',
                        return_value = [ 'GetType' ] ):
  vim.command( 'doautocmd CursorHold' )
EOPYTHON

  call assert_equal( { 'command': 'GetType', 'syntax': 'python' }, b:ycm_hover )

  let loc = screenpos( win_getid(), 2, 1 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )
  let loc = screenpos( win_getid(), 2, 2 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  " some doc - autocommand
  call setpos( '.', [ 0, 12, 3 ] )
  doautocmd CursorHold
  let loc = screenpos( win_getid(), 11, 4 )
  let popup = popup_locate( loc.row, loc.col )
  call assert_notequal( 0, popup )
  call assert_equal( [ 'def Test_OneLine()' ],
                   \ getbufline( winbufnr( popup ), 1, '$' ) )
  call assert_equal( 'python', getbufvar( winbufnr( popup ), '&syntax' ) )
  call popup_clear()

  " some doc - mapping
  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  let popup = popup_locate( loc.row, loc.col )
  call assert_notequal( 0, popup )
  call assert_equal( [ 'def Test_OneLine()' ],
                   \ getbufline( winbufnr( popup ), 1, '$' ) )
  call assert_equal( 'python', getbufvar( winbufnr( popup ), '&syntax' ) )

  " hide it again
  normal \D
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  " show it again
  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  let popup = popup_locate( loc.row, loc.col )
  call assert_notequal( 0, popup )
  call assert_equal( [ 'def Test_OneLine()' ],
                   \ getbufline( winbufnr( popup ), 1, '$' ) )
  call assert_equal( 'python', getbufvar( winbufnr( popup ), '&syntax' ) )
  call popup_clear()

  %bwipe!
endfunction

function! Test_Hover_NonNative()
  call youcompleteme#test#setup#OpenFile( '_not_a_file', { 'native_ft': 0 } )
  setfiletype NoASupportedFileType
  let messages_before = execute( 'messages' )
  doautocmd CursorHold
  call assert_false( exists( 'b:ycm_hover' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  normal \D
  call assert_false( exists( 'b:ycm_hover' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  call popup_clear()
  %bwipe!
endfunction

function SetUp_Test_Hover_Disabled_NonNative()
  let g:ycm_auto_hover = ''
endfunction

function! Test_Hover_Disabled_NonNative()
  call youcompleteme#test#setup#OpenFile( '_not_a_file', { 'native_ft': 0 } )
  setfiletype NoASupportedFileType
  let messages_before = execute( 'messages' )
  silent doautocmd CursorHold
  call assert_false( exists( 'b:ycm_hover' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  call popup_clear()
  %bwipe!
endfunction

function! SetUp_Test_AutoHover_Disabled()
  let g:ycm_auto_hover = ''
endfunction

function! Test_AutoHover_Disabled()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )

  let messages_before = execute( 'messages' )

  call assert_false( exists( 'b:ycm_hover' ) )

  call setpos( '.', [ 0, 12, 3 ] )
  silent doautocmd CursorHold
  let loc = screenpos( win_getid(), 11, 4 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  " Manual hover is still supported
  normal \D
  let loc = screenpos( win_getid(), 11, 3 )
  let popup = popup_locate( loc.row, loc.col )
  call assert_notequal( 0, popup )
  call assert_equal( [ 'Test_OneLine()', '', 'This is the one line output.' ],
                   \ getbufline( winbufnr( popup ), 1, '$' ) )
  call assert_equal( '', getbufvar( winbufnr( popup ), '&syntax' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  " Manual close hover is still supported
  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  call popup_clear()
  %bwipeout!
endfunction

function! Test_Hover_MoveCursor()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )
  function! CheckPopupVisible()
    let loc = screenpos( win_getid(), 11, 3 )
    let popup = popup_locate( loc.row, loc.col )
    call assert_notequal( 0, popup )
    call assert_equal( [ 'Test_OneLine()', '', 'This is the one line output.' ],
                     \ getbufline( winbufnr( popup ), 1, '$' ) )
    call assert_equal( '', getbufvar( winbufnr( popup ), '&syntax' ) )
  endfunction

  " needed so that the feedkeys calls actually trigger vim to notice the cursor
  " moving. We also need to enter/exit insert mode as Vim only checks for these
  " cursor moved events in very specific times. In particular, _not_ while
  " running a script (like we are here), but it _does_ on enter/exit insert
  " mode.
  call test_override( 'char_avail', 1 )

  call setpos( '.', [ 0, 12, 3 ] )
  doautocmd CursorHold
  redraw
  call CheckPopupVisible()

  call feedkeys( "li\<Esc>", 'xt' )
  redraw
  call CheckPopupVisible()

  " letters within word
  call feedkeys( "4li\<Esc>", 'xt' )
  redraw
  call CheckPopupVisible()

  " word
  call feedkeys( "wi\<Esc>", 'xt' )
  redraw
  let loc = screenpos( win_getid(), 11, 3 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  call feedkeys( "b\\D", 'xt' )
  redraw
  call CheckPopupVisible()

  " line
  call feedkeys( "ji\<Esc>", 'xt' )
  redraw
  let loc = screenpos( win_getid(), 11, 3 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  call test_override( 'ALL', 0 )
  delfunc CheckPopupVisible

  call popup_clear()
  %bwipeout!
endfunction

function! Test_Hover_Dismiss()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )
  function! CheckPopupVisible()
    let loc = screenpos( win_getid(), 11, 3 )
    let popup = popup_locate( loc.row, loc.col )
    call assert_notequal( 0, popup )
    call assert_equal( [ 'Test_OneLine()', '', 'This is the one line output.' ],
                     \ getbufline( winbufnr( popup ), 1, '$' ) )
    call assert_equal( '', getbufvar( winbufnr( popup ), '&syntax' ) )
  endfunction

  " needed so that the feedkeys calls actually trigger vim to notice the cursor
  " moving. We also need to enter/exit insert mode as Vim only checks for these
  " cursor moved events in very specific times. In particular, _not_ while
  " running a script (like we are here), but it _does_ on enter/exit insert
  " mode.
  call test_override( 'char_avail', 1 )

  call setpos( '.', [ 0, 12, 3 ] )
  doautocmd CursorHold
  call CheckPopupVisible()

  " Dismiss
  normal \D
  let loc = screenpos( win_getid(), 11, 3 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  " Make sure it doesn't come back
  doautocmd CursorHold
  let loc = screenpos( win_getid(), 11, 3 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  " Move the cursor (again this is tricky). I couldn't find any tests in vim's
  " own code that trigger CursorMoved, so we just cheat. (for the record, just
  " moving the cursor in the middle of this script does not trigger CursorMoved)
  doautocmd CursorMoved
  doautocmd CursorHold
  call CheckPopupVisible()

  call popup_clear()
  %bwipeout!
endfunction
