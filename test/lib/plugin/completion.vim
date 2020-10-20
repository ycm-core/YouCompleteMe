function! CheckCompletionItems( expected_props, ... )
  let prop = 'abbr'
  if a:0 > 0
    let prop = a:1
  endif

  let items = complete_info( [ 'items' ] )[ 'items' ]
  let abbrs = []
  for item in items
    call add( abbrs, get( item, prop ) )
  endfor

  call assert_equal( a:expected_props,
        \ abbrs,
        \ 'not matched: '
        \ .. string( a:expected_props )
        \ .. ' against '
        \ .. prop
        \ .. ' in '
        \ .. string( items )
        \ .. ' matching '
        \ .. string( abbrs ) )
endfunction

function! FeedAndCheckMain( keys, func )
  call timer_start( 500, a:func )
  call feedkeys( a:keys, 'tx!' )
endfunction

function! FeedAndCheckAgain( keys, func )
  call timer_start( 500, a:func )
  call feedkeys( a:keys )
endfunction

function! WaitForCompletion()
  call WaitForAssert( {->
        \ assert_true( pyxeval( 'ycm_state.GetCurrentCompletionRequest() is not None' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_true( pyxeval( 'ycm_state.CompletionRequestReady()' ) )
        \ } )
  redraw
  call WaitForAssert( {->
        \ assert_true( pumvisible(), 'pumvisible()' )
        \ }, 10000 )
endfunction

