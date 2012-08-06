" Copyright (C) 2011, 2012  Strahinja Val Markovic  <val@markovic.io>
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

if exists( "g:loaded_youcompleteme" )
  finish
elseif v:version < 703 || !has( 'patch584' )
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: requires Vim 7.3.584+" |
        \ echohl None
  finish
elseif !has( 'python' )
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: requires python 2.x" |
        \ echohl None
  finish
endif

let g:loaded_youcompleteme = 1

let g:ycm_min_num_of_chars_for_completion  =
      \ get( g:, 'ycm_min_num_of_chars_for_completion', 2 )

let g:ycm_filetypes_to_ignore =
      \ get( g:, 'ycm_filetypes_to_ignore', { 'notes' : 1 } )

" TODO: make this more granular
let g:ycm_filetype_completion_enabled =
      \ get( g:, 'ycm_filetype_completion_enabled', 1 )

let g:ycm_allow_changing_updatetime =
      \ get( g:, 'ycm_allow_changing_updatetime', 1 )

let g:ycm_add_preview_to_completeopt =
      \ get( g:, 'ycm_add_preview_to_completeopt', 1 )


" This is basic vim plugin boilerplate
let s:save_cpo = &cpo
set cpo&vim

" On-demand loading. Let's use the autoload folder and not slow down vim's
" startup procedure.
augroup youcompletemeStart
  autocmd!
  autocmd VimEnter * call youcompleteme#Enable()
augroup END

" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
