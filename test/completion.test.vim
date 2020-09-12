function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  " Use the default, which _should_ be the new API
  unlet! g:ycm_use_completion_api

  let g:ycm_add_preview_to_completeopt = 1

  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

exe 'source' expand( "<sfile>:p:h" ) .. '/completion.common.vim'

function! Test_Using_New_API()
  let debug_info = split( execute( 'YcmDebugInfo' ), "\n" )
  enew
  setf cpp

  call assert_equal( '', &completefunc )

  for line in debug_info
    if line =~# "^-- Completion API: "
      let ver = substitute( line, "^-- Completion API: ", "", "" )
      call assert_equal( '1', ver, 'API version' )
      return
    endif
  endfor

  call assert_report( "Didn't find the API version in the YcmDebugInfo" )

  %bwipeout!
endfunction
