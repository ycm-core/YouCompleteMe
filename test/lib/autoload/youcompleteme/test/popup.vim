function! youcompleteme#test#popup#CheckPopupPosition( winid, pos )
  redraw
  let actual_pos = popup_getpos( a:winid )
  let ret = 0
  if a:pos->empty()
    return assert_true( actual_pos->empty(), 'popup pos empty' )
  endif
  for c in keys( a:pos )
    if !has_key( actual_pos, c )
      let ret += 1
      call assert_report( 'popup with ID '
                        \ . string( a:winid )
                        \ . ' has no '
                        \ . c
                        \ . ' in: '
                        \ . string( actual_pos ) )
    else
      let ret += assert_equal( a:pos[ c ],
                             \ actual_pos[ c ],
                             \ c . ' in: ' . string( actual_pos ) )
    endif
  endfor
  return ret
endfunction


function! youcompleteme#test#popup#ScreenPos( winid, row, col )
  " Returns the screen position of the row/col in win with id winid. This
  " differs from screenpos() only in that the position need not be valid, that
  " is there need not be a text character in the referenced cell. This is useful
  " when finding where a popup _should_ be in screen position relative to actual
  " text position
  "
  " It also probably doesn't work properly for multi-byte characters and tabs
  " and things. And only returns the 'row' and 'col' items of the dict.
  "
  " So it's not that much like 'screenpos()' really.
  "
  let [ w_row, w_col ] = win_screenpos( a:winid )
  return { 'row': w_row + a:row, 'col':  w_col + a:col }
endfunction
