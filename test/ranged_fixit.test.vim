function! SetUp()
  let g:ycm_use_clangd = 1
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
        \ '/src/com/test/TestLauncher.java', {} )

  call setpos( '.', [ 0, 34, 50 ] )
  function! Check( id ) closure
    assert_equal( '        System.out.println( "Did something useful: ' .
                  \ '" + w.getWidgetInfo() );', getline( 34 ) )
    call feedkeys( "vib:YcmCompleter FixIt<CR>" )
    call feedkeys( "4", "x" )
    assert_equal( '        String string = "Did something useful: " + ' .
                  \ 'w.getWidgetInfo();', getline( 34 ) )
    assert_equal( '		System.out.println( string );', getline( 35 ) )
  endfunction

  call timer_start( 500, funcref( 'Check' ) )
  %bwipeout
endfunction
