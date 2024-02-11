" Copyright (C) 2021 YouCompleteMe contributors
"
" This file is part of YouCompleteMe.
"
" YouCompleteMe is free software: you can redistribute it and/or modify
" it under the terms of the GNU General Public License as published by
" the Free Software Foundation, either version 3 of the License, or
" (at your option) any later version.
"
" YouCompleteMe is distributed in the hope that it will be useful,
" but WITHOUT ANY WARRANTY; without even the implied warranty of
" MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
" GNU General Public License for more details.
"
" You should have received a copy of the GNU General Public License
" along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

" This is basic vim plugin boilerplate
let s:save_cpo = &cpoptions
set cpoptions&vim

scriptencoding utf-8

let s:popup_id = -1
let s:lines_and_handles = v:none
let s:select = -1
let s:kind = ''

function! youcompleteme#hierarchy#StartRequest( kind )
  py3 ycm_state.ResetCurrentHierarchy()
  if a:kind == 'call'
    let lines_and_handles = py3eval(
      \ 'ycm_state.InitializeCurrentHierarchy( ycm_state.SendCommandRequest( ' .
      \ '[ "CallHierarchy" ], "", False, 0, 0 ), ' .
      \ 'vim.eval( "a:kind" ) )' )
  else
    let lines_and_handles = py3eval( 
      \ 'ycm_state.InitializeCurrentHierarchy( ycm_state.SendCommandRequest( ' .
      \ '[ "TypeHierarchy" ], "", False, 0, 0 ), ' .
      \ 'vim.eval( "a:kind" ) )' )
  endif
  if len( lines_and_handles )
    let s:lines_and_handles = lines_and_handles
    let s:kind = a:kind
    let s:select = 1
    call s:SetupMenu()
  endif
endfunction

function! s:MenuFilter( winid, key )
  if a:key == "\<S-Tab>"
    if s:lines_and_handles[ s:select - 1 ][ 1 ] <= 0 " TODO: switching root not impl
      call popup_close( s:popup_id, [ s:select - 1, 'resolve_up' ] )
    endif
    return 1
  endif
  if a:key == "\<Tab>"
    if s:lines_and_handles[ s:select - 1 ][ 1 ] >= 0 " TODO: switching root not impl
      call popup_close( s:popup_id, [ s:select - 1, 'resolve_down' ] )
    endif
    return 1
  endif
  if a:key == "\<Esc>"
    call popup_close( s:popup_id, [ s:select - 1, 'cancel' ] )
    return 1
  endif
  if a:key == "\<CR>"
    call popup_close( s:popup_id, [ s:select - 1, 'jump' ] )
    return 1
  endif
  if a:key == "\<Up>"
    let s:select -= 1
    if s:select < 1
      let s:select = 1
    endif
    call win_execute( s:popup_id,
                    \ 'call cursor( [' . string( s:select ) . ', 1 ] )' )
    return 1
  endif
  if a:key == "\<Down>"
    let s:select += 1
    if s:select > len( s:lines_and_handles )
      let s:select = len( s:lines_and_handles )
    endif
    call win_execute( s:popup_id,
                    \ 'call cursor( [' . string( s:select ) . ', 1 ] )' )
    return 1
  endif
  return 0
endfunction

function! s:MenuCallback( winid, result )
  let operation = a:result[ 1 ]
  let selection = a:result[ 0 ]
  if operation == 'resolve_down'
    call s:ResolveItem( selection, 'down' )
  elseif operation == 'resolve_up'
    call s:ResolveItem( selection, 'up' )
  else
    if operation == 'jump'
      let handle = s:lines_and_handles[ selection ][ 1 ]
      py3 ycm_state.JumpToHierarchyItem( vimsupport.GetIntValue( "handle" ) )
    endif
    py3 ycm_state.ResetCurrentHierarchy()
    let s:kind = ''
    let s:select = 1
  endif
endfunction

function! s:SetupMenu()
  let menu_lines = []
  for line_and_item in s:lines_and_handles
    call add( menu_lines, line_and_item[ 0 ] )
  endfor
  let s:popup_id = popup_menu( menu_lines, #{
    \ filter: funcref( 's:MenuFilter' ),
    \ callback: funcref( 's:MenuCallback' ) } )
  call win_execute( s:popup_id,
                  \ 'call cursor( [' . string( s:select ) . ', 1 ] )' )
endfunction

function! s:ResolveItem( choice, direction )
  let handle = s:lines_and_handles[ a:choice ][ 1 ]
  if py3eval(
      \ 'ycm_state.ShouldResolveItem( vimsupport.GetIntValue( "handle" ), vim.eval( "a:direction" ) )' )
    let lines_and_handles_with_offset = py3eval(
        \ 'ycm_state.UpdateCurrentHierarchy( ' .
        \ 'vimsupport.GetIntValue( "handle" ), ' .
        \ 'vim.eval( "a:direction" ) )' )
    let s:select += lines_and_handles_with_offset[ 1 ]
    let s:lines_and_handles = lines_and_handles_with_offset[ 0 ]
  endif
  call s:SetupMenu()
endfunction