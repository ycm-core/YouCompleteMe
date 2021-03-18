function! youcompleteme#test#commands#WaitForCommandRequestComplete() abort
  call WaitForAssert( { ->
        \ assert_true( py3eval(
        \     'ycm_state.GetCommandRequest() is not None and '
        \   . 'ycm_state.GetCommandRequest().Done()' ) )
        \ } )

  call WaitForAssert( { ->
        \ assert_equal( -1,
        \               youcompleteme#Test_GetPollers().command.id )
        \ } )
endfunction

function! youcompleteme#test#commands#CheckNoCommandRequest() abort
  call WaitForAssert( { ->
        \ assert_true( py3eval(
        \     'ycm_state.GetCommandRequest() is None or '
        \   . 'ycm_state.GetCommandRequest().Done()' ) )
        \ } )

  call WaitForAssert( { ->
        \ assert_equal( -1,
        \               youcompleteme#Test_GetPollers().command.id )
        \ } )
endfunction

