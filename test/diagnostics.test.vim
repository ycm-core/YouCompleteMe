function! SetUp()
  let g:ycm_log_level = 'DEBUG'
  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_Changing_Filetype_Refreshes_Diagnostics()
  call youcompleteme#test#setup#OpenFile(
        \ '/test/testdata/diagnostics/foo.xml',
        \ { 'native_ft': 0 } )

  function! Check( id ) closure
    assert_true( pyxeval( 'ycm_state._buffers[ 1 ]._async_diags' ) )
    assert_equal( 'xml', '&ft' )
    assert_equal( [], sign_getplaced() )
    setf typescript
    assert_equal( 'typescript', '&ft' )
    assert_false( pyxeval( 'ycm_state._buffers[ 1 ]._async_diags' ) )
    " Diagnostics are async, so wait for the assert to return 0 for a while.
    call WaitForAssert( {-> assert_equal( 1, len( sign_getplaced() ) ) }, 10000 )
    assert_equal( 1, len( sign_getplaced()[ 0 ][ 'signs' ] ) )
    assert_equal( 1, sign_getplaced()[ 0 ][ 'bufnr' ] )
    assert_equal( 'YcmError', sign_getplaced()[ 0 ][ 'signs' ][ 0 ][ 'name' ] )
  endfunction

  call timer_start( 500, funcref( 'Check' ) )
  %bwipeout!
endfunctio
