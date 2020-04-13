function! SetUp()
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_Ranged_Fixit_Works()
  call youcompleteme#test#setup#OpenFile(
        \ '/third_party/ycmd/ycmd/tests/java/testdata/simple_eclipse_project' .
        \ '/src/com/test/TestLauncher.java', { 'delay': 15 } )

  call setpos( '.', [ 0, 34, 50 ] )
  redraw
  call assert_equal( '        System.out.println( "Did something useful: ' .
                     \ '" + w.getWidgetInfo() );', getline( '.' ) )
  call feedkeys( "vib\<esc>", 'xt' )

  function! SelectEntry( id ) closure
    redraw
    call test_feedinput( "4\<CR>" )
  endfunction

  call timer_start( 5000, funcref( 'SelectEntry' ) )
  '<,'>YcmCompleter FixIt
  redraw

  call assert_match( '        String \(x\|string\) = "Did something useful: "' .
                     \ ' + w.getWidgetInfo();', getline( 34 ) )
  call assert_match( '\t\tSystem.out.println( \(x\|string\) );', getline( 35 ) )
  %bwipeout!
  delfunction SelectEntry
endfunction

function! Test_Unresolved_Fixit_Works()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/cpp/fixit.c', {} )
  call setpos( '.', [ 0, 3, 2 ] )
  call assert_equal( '  printf("%s",1);', getline( '.' ) )
  function! SelectEntry( id ) closure
    redraw
    call test_feedinput( "2\<CR>" )
  endfunction
  call timer_start( 2000, funcref( 'SelectEntry' ) )
  YcmCompleter FixIt
  redraw
  call assert_equal( '  auto dummy = 1;', getline( '.' ) )
  call assert_equal( '  printf("%s", dummy);', getline( 4 ) )
  %bwipeout!
  delfunction SelectEntry
endfunction
