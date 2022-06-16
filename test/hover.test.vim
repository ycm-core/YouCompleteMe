function! s:WaitForCommandRequestComplete()
  return youcompleteme#test#commands#WaitForCommandRequestComplete()
endfunction

function! s:CheckNoCommandRequest()
  return youcompleteme#test#commands#CheckNoCommandRequest()
endfunction

function! s:CheckPopupVisible( row, col, text, syntax )
  " Takes a buffer position, converts it to a screen position and checks the
  " popup found at that location
  redraw
  let loc = screenpos( win_getid(), a:row, a:col )
  return s:CheckPopupVisibleScreenPos( loc, a:text, a:syntax )
endfunction

function! s:CheckPopupVisibleScreenPos( loc, text, syntax )
  " Takes a position dict like the one returned by screenpos() and verifies it
  " has 'text' (a list of lines) and 'syntax' the &syntax setting
  " popup found at that location
  redraw
  call s:WaitForCommandRequestComplete()
  call WaitForAssert( { ->
        \   assert_notequal( 0,
        \                    popup_locate( a:loc.row, a:loc.col ),
        \                    'Locate popup at ('
        \                    . a:loc.row
        \                    . ','
        \                    . a:loc.col
        \                    . ')' )
       \ } )
  let popup = popup_locate( a:loc.row, a:loc.col )
  if a:text isnot v:none
    call assert_equal( a:text,
                     \ getbufline( winbufnr( popup ), 1, '$' ) )
  endif
  call assert_equal( a:syntax, getbufvar( winbufnr( popup ), '&syntax' ) )
endfunction

function! s:CheckPopupNotVisible( row, col, with_request=v:true )
  " Takes a buffer position and ensures there is no popup visible at that
  " position. Like CheckPopupVisible, the position must be valid (i.e. there
  " must be buffer text at that position). Otherwise, you need to pass the
  " _screen_ position to CheckPopupNotVisibleScreenPos
  redraw
  let loc = screenpos( win_getid(), a:row, a:col )
  return s:CheckPopupNotVisibleScreenPos( loc, a:with_request )
endfunction

function! s:CheckPopupNotVisibleScreenPos( loc, with_request=v:true )
  " Takes a position dict like the one returned by screenpos() and verifies it
  " does not have a popup drawn on it.
  redraw
  if a:with_request
    call s:WaitForCommandRequestComplete()
  else
    call s:CheckNoCommandRequest()
  endif
  call WaitForAssert( { ->
        \   assert_equal( 0,
        \                 popup_locate( a:loc.row, a:loc.col ) )
        \ } )
endfunction

let s:python_oneline = {
      \ 'GetDoc': [ 'Test_OneLine()', '', 'This is the one line output.' ],
      \ 'GetType': [ 'def Test_OneLine()' ],
      \ }
let s:cpp_lifetime = {
      \ 'GetDoc': [ 'field lifetime',
      \             '',
      \             'Type: char',
      \             'Offset: 16 bytes',
      \             'Size: 1 byte (+7 padding)',
      \             'nobody will live > 128 years',
      \             '',
      \             '// In PointInTime',
      \             'public: char lifetime' ],
      \ 'GetType': [ 'public: char lifetime; // In PointInTime' ],
      \ }

function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'
  set signcolumn=no
  nmap <leader>D <Plug>(YCMHover)
  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  let g:ycm_auto_hover='CursorHold'

  call assert_equal( -1, youcompleteme#Test_GetPollers().command.id )
endfunction

function! Test_Hover_Uses_GetDoc()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )

  call assert_equal( 'python', &syntax )

  " no doc
  call setpos( '.', [ 0, 1, 1 ] )
  doautocmd CursorHold
  call assert_equal( { 'command': 'GetDoc', 'syntax': '' }, b:ycm_hover )

  call s:CheckPopupNotVisible( 2, 1 )
  call s:CheckPopupNotVisible( 2, 2 )

  " some doc - autocommand
  call setpos( '.', [ 0, 12, 3 ] )
  doautocmd CursorHold
  call s:CheckPopupVisible( 11, 4, s:python_oneline.GetDoc, '' )
  call popup_clear()

  " some doc - mapping
  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  call s:CheckPopupVisible( 11, 4, s:python_oneline.GetDoc, '' )
  call popup_clear()
endfunction

function! Test_Hover_Uses_GetHover()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )
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
  call s:CheckPopupNotVisible( 11, 4 )
  call popup_clear()

endfunction

function! Test_Hover_Uses_None()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )
  py3 <<EOPYTHON
from unittest import mock
with mock.patch.object( ycm_state, 'GetDefinedSubcommands', return_value = [] ):
  vim.command( 'doautocmd CursorHold' )
EOPYTHON

  call assert_equal( {}, b:ycm_hover )

  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  call s:CheckPopupNotVisible( 11, 4, v:false )

  call popup_clear()
endfunction

function! Test_Hover_Uses_GetType()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )

  py3 <<EOPYTHON
from unittest import mock
with mock.patch.object( ycm_state,
                        'GetDefinedSubcommands',
                        return_value = [ 'GetType' ] ):
  vim.command( 'doautocmd CursorHold' )
EOPYTHON

  call assert_equal( { 'command': 'GetType', 'syntax': 'python' }, b:ycm_hover )

  call s:CheckPopupNotVisible( 2, 1, v:none )
  call s:CheckPopupNotVisible( 2, 2, v:none )

  " some doc - autocommand
  call setpos( '.', [ 0, 12, 3 ] )
  doautocmd CursorHold
  call s:CheckPopupVisible( 11, 4, s:python_oneline.GetType, 'python' )
  call popup_clear()

  " some doc - mapping
  call setpos( '.', [ 0, 12, 3 ] )
  normal \D
  call s:CheckPopupVisible( 11, 4, s:python_oneline.GetType, 'python' )

  " hide it again
  normal \D
  call s:CheckPopupNotVisible( 11, 4 )

  " show it again
  normal \D
  call s:CheckPopupVisible( 11, 4, s:python_oneline.GetType, 'python' )
  call popup_clear()

endfunction

function! Test_Hover_NonNative()
  call youcompleteme#test#setup#OpenFile( '_not_a_file', { 'native_ft': 0 } )
  setfiletype NoASupportedFileType
  let messages_before = execute( 'messages' )
  doautocmd CursorHold
  call s:CheckNoCommandRequest()
  call assert_false( exists( 'b:ycm_hover' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  normal \D
  call s:CheckNoCommandRequest()
  call assert_false( exists( 'b:ycm_hover' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  call popup_clear()
endfunction

function SetUp_Test_Hover_Disabled_NonNative()
  let g:ycm_auto_hover = ''
endfunction

function! Test_Hover_Disabled_NonNative()
  call youcompleteme#test#setup#OpenFile( '_not_a_file', { 'native_ft': 0 } )
  setfiletype NoASupportedFileType
  let messages_before = execute( 'messages' )
  silent! doautocmd CursorHold
  call s:CheckNoCommandRequest()
  call assert_false( exists( 'b:ycm_hover' ) )
  call assert_equal( messages_before, execute( 'messages' ) )

  call popup_clear()
endfunction

function! SetUp_Test_AutoHover_Disabled()
  let g:ycm_auto_hover = ''
endfunction

function! Test_AutoHover_Disabled()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )

  let messages_before = execute( 'messages' )

  call assert_false( exists( 'b:ycm_hover' ) )

  call setpos( '.', [ 0, 12, 3 ] )
  silent! doautocmd CursorHold
  call s:CheckPopupNotVisible( 11, 4, v:false )
  call assert_equal( messages_before, execute( 'messages' ) )

  " Manual hover is still supported
  normal \D
  call assert_true( exists( 'b:ycm_hover' ) )
  call s:CheckPopupVisible( 11, 4, s:python_oneline.GetDoc, '' )
  call assert_equal( messages_before, execute( 'messages' ) )

  " Manual close hover is still supported
  normal \D
  call s:CheckPopupNotVisible( 11, 4, v:false )
  call assert_equal( messages_before, execute( 'messages' ) )

  call popup_clear()
endfunction

function! Test_Hover_MoveCursor()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )
  " needed so that the feedkeys calls actually trigger vim to notice the cursor
  " moving. We also need to enter/exit insert mode as Vim only checks for these
  " cursor moved events in very specific times. In particular, _not_ while
  " running a script (like we are here), but it _does_ on enter/exit insert
  " mode.
  call test_override( 'char_avail', 1 )

  call setpos( '.', [ 0, 12, 3 ] )
  doautocmd CursorHold
  call s:CheckPopupVisible( 11, 3, s:python_oneline.GetDoc, '' )

  call feedkeys( "li\<Esc>", 'xt' )
  call s:CheckPopupVisible( 11, 3, s:python_oneline.GetDoc, '' )

  " letters within word
  call feedkeys( "4li\<Esc>", 'xt' )
  call s:CheckPopupVisible( 11, 3, s:python_oneline.GetDoc, '' )

  " word
  call feedkeys( "wi\<Esc>", 'xt' )
  call s:CheckPopupNotVisible( 11, 3 )

  call feedkeys( "b\\D", 'xt' )
  call s:CheckPopupVisible( 11, 3, s:python_oneline.GetDoc, '' )

  call test_override( 'ALL', 0 )

  call popup_clear()
endfunction

function! Test_Hover_Dismiss()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )
  " needed so that the feedkeys calls actually trigger vim to notice the cursor
  " moving. We also need to enter/exit insert mode as Vim only checks for these
  " cursor moved events in very specific times. In particular, _not_ while
  " running a script (like we are here), but it _does_ on enter/exit insert
  " mode.
  call test_override( 'char_avail', 1 )

  call setpos( '.', [ 0, 12, 3 ] )
  doautocmd CursorHold
  call s:CheckPopupVisible( 11, 3, s:python_oneline.GetDoc, '' )

  " Dismiss
  normal \D
  call s:CheckPopupNotVisible( 11, 3, v:false )

  " Make sure it doesn't come back
  silent! doautocmd CursorHold
  call s:CheckPopupNotVisible( 11, 3, v:false )

  " Move the cursor (again this is tricky). I couldn't find any tests in vim's
  " own code that trigger CursorMoved, so we just cheat. (for the record, just
  " moving the cursor in the middle of this script does not trigger CursorMoved)
  doautocmd CursorMoved
  doautocmd CursorHold
  call s:CheckPopupVisible( 11, 3, s:python_oneline.GetDoc, '' )

  call popup_clear()
endfunction

function! SetUp_Test_Hover_Custom_Syntax()
  augroup MyYCMCustom
    autocmd!
    autocmd FileType cpp let b:ycm_hover = {
      \ 'command': 'GetDoc',
      \ 'syntax': 'cpp',
      \ }
  augroup END
endfunction

function! Test_Hover_Custom_Syntax()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/cpp/completion.cc',
                                        \ {} )
  call assert_equal( 'cpp', &filetype )
  call assert_equal( { 'command': 'GetDoc', 'syntax': 'cpp' }, b:ycm_hover )

  call setpos( '.', [ 0, 6, 8 ] )
  doautocmd CursorHold
  call assert_equal( { 'command': 'GetDoc', 'syntax': 'cpp' }, b:ycm_hover )
  call s:CheckPopupVisibleScreenPos( { 'row': 7, 'col': 9 },
                                   \ s:cpp_lifetime.GetDoc,
                                   \ 'cpp' )

  normal \D
  call s:CheckPopupNotVisibleScreenPos( { 'row': 7, 'col': 9 }, v:false )

  call popup_clear()
endfunction

function! TearDown_Test_Hover_Custom_Syntax()
  silent! au! MyYCMCustom
endfunction

function! SetUp_Test_Hover_Custom_Command()
  augroup MyYCMCustom
    autocmd!
    autocmd FileType cpp let b:ycm_hover = {
      \ 'command': 'GetType',
      \ 'syntax': 'cpp',
      \ }
  augroup END
endfunction

function! Test_Hover_Custom_Command()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/cpp/completion.cc',
                                        \ {} )
  call assert_equal( 'cpp', &filetype )
  call assert_equal( { 'command': 'GetType', 'syntax': 'cpp' }, b:ycm_hover )

  call setpos( '.', [ 0, 6, 8 ] )
  doautocmd CursorHold
  call assert_equal( { 'command': 'GetType', 'syntax': 'cpp' }, b:ycm_hover )

  call s:CheckPopupVisible( 5, 9, s:cpp_lifetime.GetType, 'cpp' )

  call popup_clear()
endfunction

function! TearDown_Test_Hover_Custom_Command()
  silent! au! MyYCMCustom
endfunction

function! Test_Long_Single_Line()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )
  call cursor( [ 37, 3 ] )
  normal \D

  " The popup should cover at least the whole of the line above, and not the
  " current line
  call s:CheckPopupVisible( 36, 1, v:none, '' )
  call s:CheckPopupVisible( 36, &columns, v:none, '' )

  call s:CheckPopupNotVisible( 37, 1, v:false )
  call s:CheckPopupNotVisible( 37, &columns, v:false )

  " Also wrap is ON so it should cover at least 2 lines + 2 for the header/empty
  " line
  call s:CheckPopupVisible( 35, 1, v:none, '' )
  call s:CheckPopupVisible( 35, &columns, v:none, '' )
  call s:CheckPopupVisible( 33, 1, v:none, '' )
  call s:CheckPopupVisible( 33, &columns, v:none, '' )

  call popup_clear()
endfunction

function! Test_Long_Wrapped()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )
  call cursor( [ 38, 22 ] )
  normal \D

  " The popup should cover at least the whole of the line above, and not the
  " current line. In this case, it's because the popup was shifted.
  call s:CheckPopupVisible( 37, 1, v:none, '' )
  call s:CheckPopupVisible( 37, &columns, v:none, '' )

  call s:CheckPopupNotVisible( 38, 1, v:false )
  call s:CheckPopupNotVisible( 38, &columns, v:false )

  " Also, wrap is off, so it should be _exactly_ 9 lines + 2 for the signature
  " and the empty line
  call s:CheckPopupVisible( 27, 1, v:none, '' )
  call s:CheckPopupVisible( 27, &columns, v:none, '' )

  call s:CheckPopupNotVisible( 26, 1, v:false )
  call s:CheckPopupNotVisible( 26, &columns, v:false )

  call popup_clear()
endfunction
