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
  silent exe 'YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount + 1, len( getbufinfo() ) )
  let win = getbufinfo( keys( log_files )[ 0 ] )[ 0 ].windows[ 0 ]
  call assert_equal( &previewheight, winheight( win_id2win( win ) ) )

  " default - hide
  silent exe 'YcmToggleLogs' keys( log_files )[ 0 ]
  " buffer is wiped out
  call assert_equal( bcount, len( getbufinfo() ) )
  call assert_equal( [], getbufinfo( keys( log_files )[ 0 ] ) )

  " show - 10 lines
  silent exe '10YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount + 1, len( getbufinfo() ) )
  let win = getbufinfo( keys( log_files )[ 0 ] )[ 0 ].windows[ 0 ]
  call assert_equal( 10, winheight( win_id2win( win ) ) )

  " hide
  silent exe '10YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount, len( getbufinfo() ) )
  call assert_equal( [], getbufinfo( keys( log_files )[ 0 ] ) )

  " show - 15 cols
  silent exe 'vertical 15YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount + 1, len( getbufinfo() ) )
  let win = getbufinfo( keys( log_files )[ 0 ] )[ 0 ].windows[ 0 ]
  call assert_equal( 15, winwidth( win_id2win( win ) ) )

  " hide
  silent exe 'YcmToggleLogs' keys( log_files )[ 0 ]
  call assert_equal( bcount, len( getbufinfo() ) )
  call assert_equal( [], getbufinfo( keys( log_files )[ 0 ] ) )


endfunction

function! Test_GetCommandResponse()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/python/doc.py', {} )

  " detailed_info
  call setpos( '.', [ 0, 12, 3 ] )
  call assert_equal( "Test_OneLine()\n\nThis is the one line output.",
                   \ youcompleteme#GetCommandResponse( 'GetDoc' ) )

  call setpos( '.', [ 0, 13, 7 ] )
  call assert_equal( "Test_MultiLine()\n\nThis is the one line output.\n"
                   \ . "This is second line.",
                   \ youcompleteme#GetCommandResponse( 'GetDoc' ) )

  " display message
  call setpos( '.', [ 0, 12, 10 ] )
  call assert_equal( 'def Test_OneLine()',
                   \ youcompleteme#GetCommandResponse( 'GetType' ) )

  " Location
  call setpos( '.', [ 0, 12, 10 ] )
  call assert_equal( '',
                   \ youcompleteme#GetCommandResponse( 'GoTo' ) )

  " Error
  call setpos( '.', [ 0, 12, 10 ] )
  call assert_equal( '',
                   \ youcompleteme#GetCommandResponse( 'NotACommand', 'arg' ) )

  " Specify completer
  call setpos( '.', [ 0, 13, 7 ] )
  call assert_equal( "Test_MultiLine()\n\nThis is the one line output.\n"
                   \ . "This is second line.",
                   \ youcompleteme#GetCommandResponse( 'ft=python', 'GetDoc' ) )

  " on a command, no error
  call setpos( '.', [ 0, 1, 3 ] )
  call assert_equal( '', youcompleteme#GetCommandResponse( 'GetDoc' ) )

endfunction


function! Test_GetCommandResponse_FixIt()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/cpp/fixit.c', {} )

  " fixit returns empty
  call setpos( '.', [ 0, 3, 4 ] )
  call assert_equal( '',
                   \ youcompleteme#GetCommandResponse( 'FixIt' ) )

endfunction

function! Test_GetDefinedSubcommands_Native()
  call youcompleteme#test#setup#OpenFile( '/test/testdata/cpp/fixit.c', {} )
  call assert_equal( 1, count( youcompleteme#GetDefinedSubcommands(),
                             \ 'GetDoc' ) )
endfunction

function! Test_GetDefinedSubcommands_NoNative()
  enew
  setf not_a_filetype
  call assert_equal( [], youcompleteme#GetDefinedSubcommands() )

  " The above call prints ValueError: No semantic completer ...."
  messages clear
endfunction
