function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'
  nnoremap <leader>D <Plug>(YCMHover)
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
  call assert_equal( 'GetDoc', b:ycm_hover_command )

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
  call assert_equal( 'python', getbufvar( winbufnr( popup ), '&syntax' ) )

  " some doc - mapping
  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  let popup = popup_locate( loc.row, loc.col )
  call assert_notequal( 0, popup )
  call assert_equal( [ 'Test_OneLine()', '', 'This is the one line output.' ],
                   \ getbufline( winbufnr( popup ), 1, '$' ) )
  call assert_equal( 'python', getbufvar( winbufnr( popup ), '&syntax' ) )

  call popup_clear()
  %bwipe!
endfunction

function! Test_Hover_Uses_GetHover()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )
  doautocmd CursorHold
  let b:ycm_hover_command = 'GetHover'

  " Only the generic LSP completer supports the GetHover response, so i guess we
  " test the error condition here...

  " Python desn't support GetHover
  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  cal assert_equal( 0, popup_locate( loc.row, loc.col ) )

  %bwipe!
endfunction

function! Test_Hover_Uses_GetType()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )
  doautocmd CursorHold
  let b:ycm_hover_command = 'GetType'

  doautocmd CursorHold

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

  " some doc - mapping
  call setpos( '.', [ 0, 12, 3 ] )
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
  call assert_false( exists( 'b:ycm_hover_command' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  normal \D
  call assert_false( exists( 'b:ycm_hover_command' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

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
  call assert_false( exists( 'b:ycm_hover_command' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  %bwipe!
endfunction

function! SetUp_Test_Hover_Disabled()
  let g:ycm_auto_hover = ''
endfunction

function! Test_Hover_Disabled()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py',
                                        \ { 'delay': 2 } )

  let messages_before = execute( 'messages' )

  call assert_false( exists( 'b:ycm_hover_command' ) )

  call setpos( '.', [ 0, 12, 3 ] )
  silent doautocmd CursorHold
  let loc = screenpos( win_getid(), 11, 4 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  normal \D
  let loc = screenpos( win_getid(), 11, 4 )
  call assert_equal( 0, popup_locate( loc.row, loc.col ) )

  call assert_equal( messages_before, execute( 'messages' ) )

  %bwipeout!
endfunction
