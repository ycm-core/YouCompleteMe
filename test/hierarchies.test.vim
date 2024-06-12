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

  " Check that f's callers are present
  function! Check1( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 4 ) } )
    call WaitForAssert( { -> assert_match( '^+Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Down>\<Tab>", funcref( 'Check2' ) )
  endfunction

  " Check that g's callers are present
  function! Check2( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
    call WaitForAssert( { -> assert_match( '^+Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^    +Function: h.*:8', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 5 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Down>\<Down>\<Tab>", funcref( 'Check8' ) )
  endfunction

  " Check that 1st h's callers are present
  function! Check3( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
    call WaitForAssert( { -> assert_match( '^+Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^    -Function: h.*:8', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 5 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Down>\<Tab>", funcref( 'Check4' ) )
  endfunction

  " Check that 2nd h's callers are present
  function! Check4( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
    call WaitForAssert( { -> assert_match( '^+Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^    -Function: h.*:8', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 5 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Up>\<Up>\<Up>\<Up>\<S-Tab>", funcref( 'Check5' ) )
  endfunction

  " Try to access callees of f
  function! Check5( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
    call WaitForAssert( { -> assert_match( '^-Function: f.*:1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: g.*:4', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^    -Function: h.*:8', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Function: h.*:9', getbufline( winbufnr( popup_list()[ 0 ] ), 5 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Down>\<Down>\<Down>\<Down>\<S-Tab>", funcref( 'Check6' ) )
  endfunction

  " Re-root at h
  function! Check6( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 1 ) } )
    call WaitForAssert( { -> assert_match( '^+Function: h', getbufline( winbufnr( popup_list()[ 0 ] ), 1 ) ) } )
    call FeedAndCheckAgain( "\<S-Tab>\<Tab>", funcref( 'Check7' ) )
  endfunction

  " Expansion after re-rooting works.
  " NOTE: Clangd does not support outgoing calls, hence, we are stuck at just h.
  function! Check7( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 1 ) } )
    call WaitForAssert( { -> assert_match( '^-Function: h', getbufline( winbufnr( popup_list()[ 0 ] ), 1 ) ) } )
    call FeedAndCheckAgain( "\<C-c>", funcref( 'Check8' ) )
  endfunction

  " Make sure it is closed
  function! Check8( id )
    call WaitForAssert( { -> assert_equal( len( popup_list() ), 0 ) } )
  endfunction

  call youcompleteme#hierarchy#StartRequest( 'call' )
  call WaitForAssert( { -> assert_equal( len( popup_list() ), 1 ) } )
  " Check that `+Function f` is at the start of the only line in the popup
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 1 ) } )
  call WaitForAssert( { -> assert_match( '^+Function: f', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
  call FeedAndCheckMain( "\<Tab>", funcref( 'Check1' ) )
endfunction

function! Test_Type_Hierarchy()
  "call youcompleteme#test#setup#OpenFile( '/test/testdata/cpp/hierarchies.cc', {} )
  call cursor( [ 13, 8 ] )

  " Check that B1's subtypes are present
  function! Check1( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 2 ) } )
    call WaitForAssert( { -> assert_match( '^+Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Down>\<Tab>", funcref( 'Check2' ) )
  endfunction

  " Try to access D1's subtypes
  function! Check2( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 2 ) } )
    call WaitForAssert( { -> assert_match( '^+Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Up>\<S-Tab>", funcref( 'Check3' ) )
  endfunction

  " Check that 1st h's callers are present
  function! Check3( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 3 ) } )
    call WaitForAssert( { -> assert_match( '^  +Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^-Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Up>\<S-Tab>", funcref( 'Check4' ) )
  endfunction

  " Check that 2nd h's callers are present
  function! Check4( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 3 ) } )
    call WaitForAssert( { -> assert_match( '^  -Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^-Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Tab>", funcref( 'Check5' ) )
  endfunction

  " Re-root at B0: supertypes->subtypes
  function! Check5( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 5 ) } )
    call WaitForAssert( { -> assert_match( '^+Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Struct: D0.*:15', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Down>\<Down>\<Down>\<S-Tab>", funcref( 'Check6' ) )
  endfunction

  " Re-root at D1: subtypes->supertypes
  function! Check6( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 3 ) } )
    call WaitForAssert( { -> assert_match( '^  +Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  +Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^+Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<Tab>\<Up>\<S-Tab>", funcref( 'Check7' ) )
  endfunction

  " Expansion after re-rooting works.
  function! Check7( id )
    call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 4 ) } )
    call WaitForAssert( { -> assert_match( '^  +Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^    +Struct: B0.*:12', getbufline( winbufnr( popup_list()[ 0 ] ), 2 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^  -Struct: B1.*:13', getbufline( winbufnr( popup_list()[ 0 ] ), 3 )[ 0 ] ) } )
    call WaitForAssert( { -> assert_match( '^-Struct: D1.*:16', getbufline( winbufnr( popup_list()[ 0 ] ), 4 )[ 0 ] ) } )
    call FeedAndCheckAgain( "\<C-c>", funcref( 'Check7' ) )
  endfunction

  " Make sure it is closed
  function! Check8( id )
    call WaitForAssert( { -> assert_equal( len( popup_list() ), 0 ) } )
  endfunction

  call youcompleteme#hierarchy#StartRequest( 'type' )
  call WaitForAssert( { -> assert_equal( len( popup_list() ), 1 ) } )
  " Check that `+Function f` is at the start of the only line in the popup
  call WaitForAssert( { -> assert_equal( len( getbufline( winbufnr( popup_list()[ 0 ] ), 1, '$' ) ), 1 ) } )
  call WaitForAssert( { -> assert_match( '^+Struct: B1', getbufline( winbufnr( popup_list()[ 0 ] ), 1 )[ 0 ] ) } )
  call FeedAndCheckMain( "\<Tab>", funcref( 'Check1' ) )
endfunction
