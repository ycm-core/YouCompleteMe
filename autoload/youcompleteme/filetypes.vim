" Copyright (C) 2011-2018 YouCompleteMe contributors
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


function! s:HasAnyKey( dict, keys ) abort
  for key in a:keys
    if has_key( a:dict, key )
      return 1
    endif
  endfor
  return 0
endfunction

function! youcompleteme#filetypes#AllowedForFiletype( filetype ) abort
  let whitelist_allows = type( g:ycm_filetype_whitelist ) != v:t_dict ||
        \ has_key( g:ycm_filetype_whitelist, '*' ) ||
        \ s:HasAnyKey( g:ycm_filetype_whitelist, split( a:filetype, '\.' ) )
  let blacklist_allows = type( g:ycm_filetype_blacklist ) != v:t_dict ||
        \ !s:HasAnyKey( g:ycm_filetype_blacklist, split( a:filetype, '\.' ) )

  return whitelist_allows && blacklist_allows
endfunction
