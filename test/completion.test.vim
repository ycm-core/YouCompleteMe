function! SetUp()
  let g:ycm_use_clangd = 1
  let g:ycm_confirm_extra_conf = 0
  let g:ycm_auto_trigger = 1
  let g:ycm_keep_logfiles = 1
  let g:ycm_log_level = 'DEBUG'

  let g:ycm_add_preview_to_completeopt = 1

  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

exe 'source' expand( "<sfile>:p:h" ) .. '/completion.common.vim'

function! Test_Using_Upfront_Resolve()
  let debug_info = split( execute( 'YcmDebugInfo' ), "\n" )
  enew
  setf cpp

  call assert_equal( '', &completefunc )

  for line in debug_info
    if line =~# "^-- Resolve completions: "
      let ver = substitute( line, "^-- Resolve completions: ", "", "" )
      call assert_equal( 'Up front', ver, 'API version' )
      return
    endif
  endfor

  call assert_report( "Didn't find the resolve type in the YcmDebugInfo" )
endfunction
