function! CheckCompletionItemsContainsExactly( expected_props, ... )
  let prop = 'abbr'
  if a:0 > 0
    let prop = a:1
  endif

  let items = complete_info( [ 'items' ] )[ 'items' ]
  let abbrs = []
  for item in items
    call add( abbrs, get( item, prop ) )
  endfor

  return assert_equal( a:expected_props,
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

function! CheckCompletionItemsHasItems( expected_props, ... )
  let prop = 'abbr'
  if a:0 > 0
    let prop = a:1
  endif

  let items = complete_info( [ 'items' ] )[ 'items' ]
  let abbrs = []
  for item in items
    call add( abbrs, get( item, prop ) )
  endfor

  let result = 0
  for expected in a:expected_props
    if index( abbrs, expected ) < 0
      call assert_report( "Didn't find item with "
                        \ .. prop
                        \ .. '="'
                        \ .. expected
                        \ .. '" in completion list: '
                        \ .. string( abbrs ) )
      let result += 1
    endif
  endfor

  return result
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

