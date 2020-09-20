function! youcompleteme#test#commands#WaitForCommandRequestComplete() abort
  call WaitForAssert( { ->
        \ assert_false( youcompleteme#IsRequestPending( 'command' ) )
        \ } )
endfunction

function! youcompleteme#test#commands#CheckNoCommandRequest() abort
  call WaitForAssert( { ->
        \ assert_false( youcompleteme#IsRequestPending( 'command' ) )
        \ } )

  call WaitForAssert( { ->
        \ assert_equal( v:null,
        \               youcompleteme#Test_GetRequests().command.callback )
        \ } )
endfunction

