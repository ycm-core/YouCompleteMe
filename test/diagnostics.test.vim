function! SetUp()
  let g:ycm_log_level = 'DEBUG'
  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_Changing_Filetype_Refreshes_Diagnostics()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/diagnostics/foo.xml', 0 )

  " Required to trigger TextChangedI
  " https://github.com/vim/vim/issues/4665#event-2480928194
  call test_override( 'char_avail', 1 )

  " Must do the checks in a timer callback because we need to stay in insert
  " mode until done.
  function! Check( id ) closure
    call WaitForAssert( {-> assert_true( pyxeval( 'ycm_state._buffers[ 1 ]._async_diags' ) ) } )
    call WaitForAssert( {-> assert_equal( 'xml', eval( '&ft' ) ) } )
    call WaitForAssert( {-> assert_equal( [], sign_getplaced() ) } )
    setf typescript
    call WaitForAssert( {-> assert_equal( 'typescript', eval( '&ft' ) ) } )
    call WaitForAssert( {-> assert_false( pyxeval( 'ycm_state._buffers[ 1 ]._async_diags' ) ) } )
    call WaitForAssert( {-> assert_equal( 1, len( sign_getplaced() ) ) }, 10000 )
    call WaitForAssert( {-> assert_equal( 1, len( sign_getplaced()[ 0 ][ 'signs' ] ) ) } )
    call WaitForAssert( {-> assert_equal( 1, sign_getplaced()[ 0 ][ 'bufnr' ] ) } )
    call WaitForAssert( {->
          \ assert_equal( 'YcmError',
          \                sign_getplaced()[ 0 ][ 'signs' ][ 0 ][ 'name' ] )
          \ } )
  endfunction

  call timer_start( 500, funcref( 'Check' ) )

  call test_override( 'ALL', 0 )
  %bwipeout!
endfunctio
