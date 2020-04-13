function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'
  call youcompleteme#test#setup#SetUp()
endfunction

function! Test_ToggleLogs()
  let log_files = pyxeval( 'ycm_state.GetLogfiles()' )
  let bcount = len( getbufinfo() )

  " default - show
  exe 'YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount + 1, len( getbufinfo() ) )
  let win = getbufinfo( keys( log_files )[ 0 ] )[ 0 ].windows[ 0 ]
  call assert_equal( &previewheight, winheight( win_id2win( win ) ) )

  " default - hide
  exe 'YcmToggleLogs' keys( log_files )[ 0 ]
  " buffer is wiped out
  call assert_equal( bcount, len( getbufinfo() ) )
  call assert_equal( [], getbufinfo( keys( log_files )[ 0 ] ) )

  " show - 10 lines
  exe '10YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount + 1, len( getbufinfo() ) )
  let win = getbufinfo( keys( log_files )[ 0 ] )[ 0 ].windows[ 0 ]
  call assert_equal( 10, winheight( win_id2win( win ) ) )

  " hide
  exe '10YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount, len( getbufinfo() ) )
  call assert_equal( [], getbufinfo( keys( log_files )[ 0 ] ) )

  " show - 15 cols
  exe 'vertical 15YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount + 1, len( getbufinfo() ) )
  let win = getbufinfo( keys( log_files )[ 0 ] )[ 0 ].windows[ 0 ]
  call assert_equal( 15, winwidth( win_id2win( win ) ) )

  " hide
  exe 'YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount, len( getbufinfo() ) )
  call assert_equal( [], getbufinfo( keys( log_files )[ 0 ] ) )

  %bwipeout!
endfunction
