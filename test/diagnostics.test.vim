function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'
  let g:ycm_always_populate_location_list = 1

  " diagnostics take ages
  let g:ycm_test_min_delay = 7
  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_Changing_Filetype_Refreshes_Diagnostics()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/diagnostics/foo.xml',
        \ { 'native_ft': 0 } )

  call assert_equal( 'xml', &ft )
  call assert_false( pyxeval( 'ycm_state._buffers[' . bufnr( '%' ) . ']._async_diags' ) )
  call assert_equal( [], sign_getplaced() )
  setf typescript
  call assert_equal( 'typescript', &ft )
  call assert_false( pyxeval( 'ycm_state._buffers[' . bufnr( '%' ) . ']._async_diags' ) )
  " Diagnostics are async, so wait for the assert to return 0 for a while.
  call WaitForAssert( {-> assert_equal( 1, len( sign_getplaced() ) ) } )
  call assert_equal( 1, len( sign_getplaced()[ 0 ][ 'signs' ] ) )
  call assert_equal( 'YcmError', sign_getplaced()[ 0 ][ 'signs' ][ 0 ][ 'name' ] )
  call assert_false( empty( getloclist( 0 ) ) )
endfunction

function! Test_MessagePoll_After_LocationList()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/diagnostics/foo.cpp', {} )

  setf cpp
  call assert_equal( 'cpp', &ft )
  call WaitForAssert( {-> assert_equal( 1, len( sign_getplaced() ) ) } )
  call setline( 1, '' )
  " Wait for the parse request to be complete otherwise we won't send another
  " one when the TextChanged event fires
  call WaitFor( {-> pyxeval( 'ycm_state.FileParseRequestReady()' ) } )
  doautocmd TextChanged
  call WaitForAssert( {-> assert_true( empty( sign_getplaced() ) ) } )
  call assert_true( empty( getloclist( 0 ) ) )
endfunction

function! Test_MessagePoll_Multiple_Filetypes()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/java/testdata/simple_eclipse_project' .
        \ '/src/com/test/TestLauncher.java', {} )
  call WaitForAssert( {-> assert_true( len( sign_getplaced( '%' )[ 0 ][ 'signs' ] ) ) } )
  let java_signs = sign_getplaced( '%' )[ 0 ][ 'signs' ]
  silent vsplit testdata/diagnostics/foo.cpp
  " Make sure we've left the java buffer
  call assert_equal( java_signs, sign_getplaced( '#' )[ 0 ][ 'signs' ] )
  " Clangd emits two diagnostics for foo.cpp.
  call WaitForAssert( {-> assert_equal( 2, len( sign_getplaced( '%' )[ 0 ][ 'signs' ] ) ) } )
  let cpp_signs = sign_getplaced( '%' )[ 0 ][ 'signs' ]
  call assert_false( java_signs == cpp_signs )
endfunction
