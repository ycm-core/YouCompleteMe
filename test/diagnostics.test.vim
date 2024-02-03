function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'
  let g:ycm_always_populate_location_list = 1
  let g:ycm_enable_semantic_highlighting = 1
  let g:ycm_auto_hover = ''

  " diagnostics take ages
  let g:ycm_test_min_delay = 7
  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_Diagnostics_Update_In_Insert_Mode()
  call youcompleteme#test#setup#OpenFile(
    \ '/test/testdata/cpp/new_file.cpp', {} )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! Check( id ) closure
    call WaitForAssert( {-> assert_true( len( sign_getplaced(
                           \ '%',
                           \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )
    call feedkeys( "\<ESC>" )
  endfunction

  call FeedAndCheckMain( 'imain(', funcref( 'Check' ) )
  call test_override( 'ALL', 0 )
endfunction

function! SetUp_Test_Disable_Diagnostics_Update_In_insert_Mode()
  call youcompleteme#test#setup#PushGlobal( 
    \ 'ycm_update_diagnostics_in_insert_mode', 0 )
endfunction

function! Test_Disable_Diagnostics_Update_In_insert_Mode()
  call youcompleteme#test#setup#OpenFile(
    \ '/test/testdata/cpp/new_file.cpp', {} )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! CheckNoDiagUIAfterOpenParenthesis( id ) closure
    call WaitForAssert( {->
      \ assert_true(
        \ py3eval(
           \ 'len( ycm_state.CurrentBuffer()._diag_interface._diagnostics )'
      \ ) ) } )
    call WaitForAssert( {-> assert_false( len( sign_getplaced(
                           \ '%',
                           \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )

    call FeedAndCheckAgain( "   \<BS>\<BS>\<BS>)",
      \ funcref( 'CheckNoDiagUIAfterClosingPatenthesis' ) )
  endfunction

  function! CheckNoDiagUIAfterClosingPatenthesis( id ) closure
    call WaitForAssert( {->
      \ assert_true(
        \ py3eval(
           \ 'len( ycm_state.CurrentBuffer()._diag_interface._diagnostics )'
      \ ) ) } )
    call WaitForAssert( {-> assert_false( len( sign_getplaced(
                           \ '%',
                           \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )

    call feedkeys( "\<ESC>" )
    call FeedAndCheckAgain( "\<ESC>",
      \ funcref( 'CheckDiagUIRefreshedAfterLeavingInsertMode' ) )
  endfunction

  function! CheckDiagUIRefreshedAfterLeavingInsertMode( id ) closure
    call WaitForAssert( {->
      \ assert_true(
        \ py3eval(
           \ 'len( ycm_state.CurrentBuffer()._diag_interface._diagnostics )'
      \ ) ) } )
    call WaitForAssert( {-> assert_true( len( sign_getplaced(
                           \ '%',
                           \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )
    call FeedAndCheckAgain( "A\<CR>", funcref( 'CheckNoPropsAfterNewLine' ) )
  endfunction

  function! CheckNoPropsAfterNewLine( id ) closure
    call WaitForAssert( {->
      \ assert_true(
        \ py3eval(
           \ 'len( ycm_state.CurrentBuffer()._diag_interface._diagnostics )'
      \ ) ) } )
    call WaitForAssert( {-> assert_false( len( prop_list(
                           \ 1, { 'end_lnum': -1,
                                \ 'types': [ 'YcmVirtDiagWarning',
                                           \ 'YcmVirtDiagError',
                                           \ 'YcmVirtDiagPadding' ] } ) ) ) } )
  endfunction

  call FeedAndCheckMain( 'imain(',
      \ funcref( 'CheckNoDiagUIAfterOpenParenthesis' ) )
  call test_override( 'ALL', 0 )
endfunction

function! TearDown_Test_Disable_Diagnostics_Update_In_insert_Mode()
  call youcompleteme#test#setup#PopGlobal(
    \ 'ycm_update_diagnostics_in_insert_mode' )
endfunction

function! Test_Changing_Filetype_Refreshes_Diagnostics()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/diagnostics/foo.xml',
        \ { 'native_ft': 0 } )

  call assert_equal( 'xml', &filetype )
  call assert_false(
    \ pyxeval( 'ycm_state._buffers[' . bufnr( '%' ) . ']._async_diags' ) )
  call assert_true( empty( sign_getplaced(
                        \ '%',
                        \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) )
  setf typescript
  call assert_equal( 'typescript', &filetype )
  call assert_false(
    \ pyxeval( 'ycm_state._buffers[' . bufnr( '%' ) . ']._async_diags' ) )
  " Diagnostics are async, so wait for the assert to return 0 for a while.
  call WaitForAssert( {-> assert_equal( 1, len( sign_getplaced(
                        \ '%',
                        \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )
  call assert_equal( 1, len( sign_getplaced(
                        \ '%',
                        \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) )
  call assert_equal(
    \ 'YcmError',
    \ sign_getplaced(
      \ '%',
      \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ][ 0 ][ 'name' ] )
  call assert_false( empty( getloclist( 0 ) ) )
endfunction

function! Test_MessagePoll_After_LocationList()
  call youcompleteme#test#setup#OpenFile(
    \ '/test/testdata/diagnostics/foo.cpp', {} )

  setf cpp
  call assert_equal( 'cpp', &filetype )
  call WaitForAssert( {-> assert_equal( 2, len( sign_getplaced(
                        \ '%',
                        \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )
  call setline( 1, '' )
  " Wait for the parse request to be complete otherwise we won't send another
  " one when the TextChanged event fires
  call WaitFor( {-> pyxeval( 'ycm_state.FileParseRequestReady()' ) } )
  doautocmd TextChanged
  call WaitForAssert( {-> assert_true( empty( sign_getplaced(
                        \ '%',
                        \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )
  call assert_true( empty( getloclist( 0 ) ) )
endfunction

function! Test_MessagePoll_Multiple_Filetypes()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/java/testdata/simple_eclipse_project' .
        \ '/src/com/test/TestLauncher.java', {} )
  call WaitForAssert( {->
      \ assert_true( len( sign_getplaced(
                            \ '%',
                            \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )
  let java_signs = sign_getplaced(
                     \ '%',
                     \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ]
  silent vsplit testdata/diagnostics/foo.cpp
  " Make sure we've left the java buffer
  call assert_equal( java_signs,
      \ sign_getplaced( '#', { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] )
  " Clangd emits two diagnostics for foo.cpp.
  call WaitForAssert( {->
      \ assert_equal(
          \ 2,
          \ len( sign_getplaced(
              \ '%',
              \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )
  let cpp_signs = sign_getplaced( '%',
      \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ]
  call assert_false( java_signs == cpp_signs )
endfunction

function! Test_BufferWithoutAssociatedFile_HighlightingWorks()
  enew
  call setbufline( '%', 1, 'iiii' )
  setf c
  call WaitForAssert( {->
    \ assert_true( len( sign_getplaced(
                        \ '%',
                        \ { 'group': 'ycm_signs' } )[ 0 ][ 'signs' ] ) ) } )
  let expected_properties = [
    \ { 'id': 4,
    \   'col': 1,
    \   'end': 1,
    \   'type': 'YcmErrorProperty',
    \   'length': 0,
    \   'start': 1 },
    \ { 'id': 3,
    \   'col': 1,
    \   'end': 1,
    \   'type': 'YcmErrorProperty',
    \   'length': 0,
    \   'start': 1 },
    \ { 'id': 2,
    \    'col': 1,
    \    'end': 1,
    \    'type': 'YcmErrorProperty',
    \    'length': 4,
    \    'start': 1 },
    \ { 'id': 1,
    \    'col': 1,
    \    'end': 1,
    \    'type': 'YcmErrorProperty',
    \    'length': 4,
    \    'start': 1 } ]

  call CheckListOfDicts( prop_list( 1 ), expected_properties )
endfunction

function! Test_ThirdPartyDeletesItsTextProperty()
  enew
  call prop_type_add( 'ThirdPartyProperty', { 'highlight': 'Error' } )
  call prop_add( 1, 1, { 'type': 'ThirdPartyProperty', 'bufnr': bufnr('%'), 'id': 42 } )
  call prop_type_delete( 'ThirdPartyProperty' )

  py3 from ycm.vimsupport import GetTextProperties, GetIntValue
  call assert_equal( [], py3eval( 'GetTextProperties( GetIntValue( """bufnr( "%" )""" ) )' ) )
endfunction

function! Test_ShowDetailedDiagnostic_CmdLine()
  call youcompleteme#test#setup#OpenFile(
    \ '/test/testdata/cpp/fixit.cpp', {} )

  call cursor( [ 3, 1 ] )
  redir => output
  YcmShowDetailedDiagnostic
  redir END

  call assert_equal(
        \ "Format specifies type 'char *' but the argument has type 'int' "
        \ . '(fix available) [-Wformat]',
        \ trim( output ) )

  %bwipe!
endfunction

function! Test_ShowDetailedDiagnostic_PopupAtCursor()
  call youcompleteme#test#setup#OpenFile(
    \ '/test/testdata/cpp/fixit.cpp', {} )

  call cursor( [ 3, 1 ] )
  YcmShowDetailedDiagnostic popup

  let id = popup_locate( 4, 16 )
  call assert_notequal(
        \ 0,
        \ id,
        \ "Couldn't find popup! " .. youcompleteme#test#popup#DumpPopups() )

  if exists( '*popup_list' )
    let popups = popup_list()
    call assert_equal( 1, len( popups ) )
  endif

  call youcompleteme#test#popup#CheckPopupPosition( id, {
        \ 'visible': 1,
        \ 'col': 16,
        \ 'line': 4,
        \ } )
  call assert_equal(
        \ [
        \   "Format specifies type 'char *' but the argument has type 'int' "
        \   . '(fix available) [-Wformat]',
        \ ],
        \ getbufline( winbufnr(id), 1, '$' ) )

  " From vim's test_popupwin.vim
  " trigger the check for last_cursormoved by going into insert mode
  call test_override( 'char_avail', 1 )
  call feedkeys( "ji\<Esc>", 'xt' )
  call assert_equal( {}, popup_getpos( id ) )
  call test_override( 'ALL', 0 )

  %bwipe!
endfunction

function! Test_ShowDetailedDiagnostic_Popup_WithCharacters()
  let f = tempname() . '.cc'
  execut 'edit' f
  call setline( 1, [
        \   'struct Foo {};',
        \   'template<char...> Foo operator""_foo() { return {}; }',
        \   'int main() {',
        \       '""_foo',
        \   '}',
        \ ] )
  call youcompleteme#test#setup#WaitForInitialParse( {} )

  call WaitForAssert( {->
    \ assert_true(
      \ py3eval(
         \ 'len( ycm_state.CurrentBuffer()._diag_interface._diagnostics )'
    \ ) ) } )

  call cursor( [ 4, 1 ] )
  YcmShowDetailedDiagnostic popup

  let id = popup_locate( 5, 7 )
  call assert_notequal(
        \ 0,
        \ id,
        \ "Couldn't find popup! " .. youcompleteme#test#popup#DumpPopups() )

  if exists( '*popup_list' )
    let popups = popup_list()
    call assert_equal( 1, len( popups ) )
  endif

  call youcompleteme#test#popup#CheckPopupPosition( id, {
        \ 'visible': 1,
        \ 'col': 7,
        \ 'line': 5,
        \ } )
  call assert_match(
        \ "^No matching literal operator for call to 'operator\"\"_foo'.*",
        \ getbufline( winbufnr(id), 1, '$' )[ 0 ] )

  " From vim's test_popupwin.vim
  " trigger the check for last_cursormoved by going into insert mode
  call test_override( 'char_avail', 1 )
  call feedkeys( "ji\<Esc>", 'xt' )
  call assert_equal( {}, popup_getpos( id ) )
  call test_override( 'ALL', 0 )

  %bwipe!
endfunction

function! Test_ShowDetailedDiagnostic_Popup_MultilineDiagNotFromStartOfLine()
  let f = tempname() . '.cc'
  execut 'edit' f
  call setline( 1, [
        \   'int main () {',
        \   '  int a \',
        \   '=\',
        \   '=',
        \   '3;',
        \   '}',
        \ ] )
  call youcompleteme#test#setup#WaitForInitialParse( {} )

  call WaitForAssert( {->
    \ assert_true(
      \ py3eval(
         \ 'len( ycm_state.CurrentBuffer()._diag_interface._diagnostics )'
    \ ) ) } )

  call test_override( 'char_avail', 1 )

  for cursor_pos in [ [ 2, 9 ], [ 3, 1], [ 4, 1 ] ]
    call cursor( cursor_pos )
    YcmShowDetailedDiagnostic popup

    call assert_equal( len( popup_list() ), 1 )
    let id = popup_list()[ 0 ]
    call assert_notequal( 0, id, "Couldn't find popup!" )
    call assert_equal( [ 3, 10 ], win_screenpos( id ) )

    call youcompleteme#test#popup#CheckPopupPosition( id, {
          \ 'visible': 1,
          \ 'col': 10,
          \ 'line': 3,
          \ } )
    call assert_match(
          \ "^Invalid '==' at end of declaration; did you mean '='?.*",
          \ getbufline( winbufnr(id), 1, '$' )[ 0 ] )
    " From vim's test_popupwin.vim
    " trigger the check for last_cursormoved by going into insert mode
    call feedkeys( "ji\<Esc>", 'xt' )
    call assert_equal( {}, popup_getpos( id ) )
  endfor

  call test_override( 'ALL', 0 )

  %bwipe!
endfunction

function! Test_ShowDetailedDiagnostic_Popup_MultilineDiagFromStartOfLine()
  let f = tempname() . '.cc'
  execut 'edit' f
  call setline( 1, [
        \   'int main () {',
        \   'const int &&',
        \   '        /* */',
        \   '    rd = 1;',
        \   'rd = 4;',
        \   '}',
        \ ] )
  call youcompleteme#test#setup#WaitForInitialParse( {} )

  call WaitForAssert( {->
    \ assert_true(
      \ py3eval(
         \ 'len( ycm_state.CurrentBuffer()._diag_interface._diagnostics )'
    \ ) ) } )

  call test_override( 'char_avail', 1 )

  for cursor_pos in [ [ 2, 1 ], [ 3, 9 ], [ 4, 5 ] ]
    call cursor( cursor_pos )
    YcmShowDetailedDiagnostic popup

    call assert_equal( 1, len( popup_list() ) )
    let id = popup_list()[ 0 ]
    call assert_notequal( 0, id, "Couldn't find popup!" )
    call assert_equal( [ 3, 13 ], win_screenpos( id ) )

    call youcompleteme#test#popup#CheckPopupPosition( id, {
          \ 'visible': 1,
          \ 'col': 13,
          \ 'line': 3,
          \ } )
    call assert_match(
          \ "^Variable 'rd' declared const here.*",
          \ getbufline( winbufnr(id), 1, '$' )[ 0 ] )
    " From vim's test_popupwin.vim
    " trigger the check for last_cursormoved by going into insert mode
    call feedkeys( "ji\<Esc>ki\<Esc>", 'xt' )
    call assert_equal( {}, popup_getpos( id ) )
  endfor

  call test_override( 'ALL', 0 )

  %bwipe!
endfunction

function! Test_ShowDetailedDiagnostic_Popup_MultipleDiagsPerLine_SameMessage()
  let f = tempname() . '.cc'
  execut 'edit' f
  call setline( 1, [ 'void f(){a;a;}', ] )
  call youcompleteme#test#setup#WaitForInitialParse( {} )

  call WaitForAssert( {->
    \ assert_true(
      \ py3eval(
        \ 'len( ycm_state.CurrentBuffer()._diag_interface._diagnostics )'
    \ ) ) } )

  YcmShowDetailedDiagnostic popup
  let popup_list = popup_list()
  call assert_equal( 1, len( popup_list ) )
  call popup_close( popup_list[ 0 ] )
endfunction
