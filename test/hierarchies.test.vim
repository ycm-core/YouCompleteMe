function! SetUp()
  let g:ycm_auto_hover = 1
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_Call_Hierarchy()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/cpp/hierarchies.cc', {} )
  call cursor( [ 1, 5 ] )

  call youcompleteme#hierarchy#StartRequest( 'call' )
  call WaitForAssert( { -> assert_equal( len( popup_list() ), 1 ) } )
  " Check that `+Function f` is at the start of the only line in the popup.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 1 ) } )
  call assert_match( '^+Function: f', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )

  call feedkeys( "\<Tab>", "xt" )
  " Check that f's callers are present.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 4 ) } )
  call assert_match( '^+Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  +Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  +Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )
  call assert_match( '^  +Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] )

  call feedkeys( "\<Down>\<Tab>", "xt" )
  " Check that g's callers are present.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
  call assert_match( '^+Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )
  call assert_match( '^    +Function: h.*:8', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] )
  call assert_match( '^  +Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 5 )[ 0 ] )

  " silent, because h has no incoming calls.
  silent call feedkeys( "\<Down>\<Down>\<Tab>", "xt" )
  " Check that 1st h's callers are present.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
  call assert_match( '^+Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )
  call assert_match( '^    -Function: h.*:8', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] )
  call assert_match( '^  +Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 5 )[ 0 ] )

  " silent, because h has no incoming calls.
  silent call feedkeys( "\<Down>\<Tab>", "xt" )
  " Check that 2nd h's callers are present.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
  call assert_match( '^+Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )
  call assert_match( '^    -Function: h.*:8', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] )
  call assert_match( '^  -Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 5 )[ 0 ] )

  " silent, because clangd does not support outgoing calls.
  silent call feedkeys( "\<Up>\<Up>\<Up>\<Up>\<S-Tab>", "xt" )
  " Try to access callees of f.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
  call assert_match( '^-Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )
  call assert_match( '^    -Function: h.*:8', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] )
  call assert_match( '^  -Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 5 )[ 0 ] )

  " silent, because clangd does not support outgoing calls.
  silent call feedkeys( "\<Down>\<Down>\<Down>\<Down>\<S-Tab>", "xt" )
  " Re-root at h.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 1 ) } )
  call assert_match( '^+Function: h', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[0] )

  " silent, because clangd does not support outgoing calls.
  silent call feedkeys( "\<S-Tab>\<Tab>", "xt" )
  " Expansion after re-rooting works.
  " NOTE: Clangd does not support outgoing calls, hence, we are stuck at just h.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 1 ) } )
  call assert_match( '^-Function: h', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )

  call feedkeys( "\<C-c>", "xt" )
  " Make sure it is closed.
  call WaitForAssert( { -> assert_equal( len( popup_list() ), 0 ) } )

  %bwipe!
endfunction

function! Test_Type_Hierarchy()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/cpp/hierarchies.cc', {} )
  call cursor( [ 13, 8 ] )

  call youcompleteme#hierarchy#StartRequest( 'type' )
  call WaitForAssert( { -> assert_equal( len( popup_list() ), 1 ) } )
  " Check that `+Struct: B1` is at the start of the only line in the popup.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 1 ) } )
  call assert_match( '^+Struct: B1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )

  call feedkeys( "\<Tab>", "xt" )
  " Check that B1's subtypes are present.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 2 ) } )
  call assert_match( '^+Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  +Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )

  " silent, because D1 has no subtypes.
  silent call feedkeys( "\<Down>\<Tab>", "xt" )
  " Try to access D1's subtypes.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 2 ) } )
  call assert_match( '^+Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  -Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )

  call feedkeys( "\<Up>\<S-Tab>", "xt" )
  " Check that B1's supertypes are present.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 3 ) } )
  call assert_match( '^  +Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^-Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  -Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )

  " silent, because there are no supertypes of B0.
  silent call feedkeys( "\<Up>\<S-Tab>", "xt" )
  " Try to access B0's supertypes.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 3 ) } )
  call assert_match( '^  -Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^-Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  -Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )

  call feedkeys( "\<Tab>", "xt" )
  " Re-root at B0: supertypes->subtypes.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 4 ) } )
  call assert_match( '^+Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  +Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  +Struct: D0.*:15', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )
  call assert_match( '^  +Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] )

  call feedkeys( "\<Down>\<Down>\<Down>\<S-Tab>", "xt" )
  " Re-root at D1: subtypes->supertypes.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 3 ) } )
  call assert_match( '^  +Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^  +Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^+Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )

  " silent, because there are no subtypes of D1.
  silent call feedkeys( "\<Tab>\<Up>\<S-Tab>", "xt" )
  " Expansion after re-rooting works.
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 4 ) } )
  call assert_match( '^  +Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] )
  call assert_match( '^    +Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] )
  call assert_match( '^  -Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] )
  call assert_match( '^-Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] )

  call feedkeys( "\<C-c>", "xt" )
  " Make sure it is closed.
  call WaitForAssert( { -> assert_equal( len( popup_list() ), 0 ) } )

  %bwipe!
endfunction
