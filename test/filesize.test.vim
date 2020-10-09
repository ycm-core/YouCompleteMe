function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_always_populate_location_list = 1
  let g:ycm_filetype_blacklist = {
        \ 'ycm_nofiletype': 1
        \ }

  " diagnostics take ages
  let g:ycm_test_min_delay = 7 
  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_Open_Unsupported_Filetype_Messages()
  messages clear
  enew

  let X = join( map( range( 0, 1000 * 1024 + 1 ), {->'X'} ), '' )
  call append( line( '$' ), X )

  w! Xtest

  let l:stderr = substitute( execute( 'messages' ), '\n', '\t', 'g' )
  call assert_notmatch( 'the file exceeded the max size', stderr )

  %bwipeout!
  call delete( 'Xtest' )
endfunction

function! Test_Open_Supported_Filetype_Messages()
  enew

  let X = join( map( range( 0, 1000 * 1024 + 1 ), {->'X'} ), '' )
  call append( line( '$' ), X )

  w! Xtest
  messages clear
  setf cpp

  let l:stderr = substitute( execute( 'messages' ), '\n', '\t', 'g' )
  call assert_match( 'the file exceeded the max size', stderr )
  call assert_equal( 1, b:ycm_largefile )

  %bwipeout!
  call delete( 'Xtest' )
endfunction
