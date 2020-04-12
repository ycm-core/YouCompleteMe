function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  let g:ycm_use_completion_api = 0

  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

exe 'source' expand( "<sfile>:p:h" ) .. '/completion.common.vim'

function! Test_Using_Old_API()
  let debug_info = split( execute( 'YcmDebugInfo' ), "\n" )

  enew
  setf cpp

  call assert_equal( 'youcompleteme#CompleteFunc', &completefunc )

  for line in debug_info
    if line =~# "^-- Completion API: "
      let ver = substitute( line, "^-- Completion API: ", "", "" )
      call assert_equal( '0', ver, 'API version' )
      return
    endif
  endfor

  call assert_report( "Didn't find the API version in the YcmDebugInfo" )

  %bwipeout!
endfunction
