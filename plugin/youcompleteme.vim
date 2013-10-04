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

" This is basic vim plugin boilerplate
let s:save_cpo = &cpo
set cpo&vim

if exists( "g:loaded_youcompleteme" )
  finish
elseif v:version < 703 || (v:version == 703 && !has('patch584'))
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

let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )

function! s:HasYcmCore()
  let path_prefix = s:script_folder_path . '/../python/'
  if filereadable(path_prefix . 'ycm_core.so')
    return 1
  elseif filereadable(path_prefix . 'ycm_core.pyd')
    return 1
  elseif filereadable(path_prefix . 'ycm_core.dll')
    return 1
  endif
  return 0
endfunction

let g:ycm_check_if_ycm_core_present =
      \ get( g:, 'ycm_check_if_ycm_core_present', 1 )

if g:ycm_check_if_ycm_core_present && !s:HasYcmCore()
  echohl WarningMsg |
        \ echomsg "ycm_core.[so|pyd|dll] not detected; you need to compile " .
        \ "YCM before using it. Read the docs!" |
        \ echohl None
  finish
endif

let g:loaded_youcompleteme = 1

" NOTE: Most defaults are in default_settings.json. They are loaded into Vim
" global with the 'ycm_' prefix if such a key does not already exist; thus, the
" user can override the defaults.
" The only defaults that are here are the ones that are only relevant to the YCM
" Vim client and not the server.

let g:ycm_register_as_syntastic_checker =
      \ get( g:, 'ycm_register_as_syntastic_checker', 1 )

let g:ycm_allow_changing_updatetime =
      \ get( g:, 'ycm_allow_changing_updatetime', 1 )

let g:ycm_add_preview_to_completeopt =
      \ get( g:, 'ycm_add_preview_to_completeopt', 0 )

let g:ycm_autoclose_preview_window_after_completion =
      \ get( g:, 'ycm_autoclose_preview_window_after_completion', 0 )

let g:ycm_autoclose_preview_window_after_insertion =
      \ get( g:, 'ycm_autoclose_preview_window_after_insertion', 0 )

let g:ycm_key_list_select_completion =
      \ get( g:, 'ycm_key_list_select_completion', ['<TAB>', '<Down>'] )

let g:ycm_key_list_previous_completion =
      \ get( g:, 'ycm_key_list_previous_completion', ['<S-TAB>', '<Up>'] )

let g:ycm_key_invoke_completion =
      \ get( g:, 'ycm_key_invoke_completion', '<C-Space>' )

let g:ycm_key_detailed_diagnostics =
      \ get( g:, 'ycm_key_detailed_diagnostics', '<leader>d' )

let g:ycm_cache_omnifunc =
      \ get( g:, 'ycm_cache_omnifunc', 1 )

" On-demand loading. Let's use the autoload folder and not slow down vim's
" startup procedure.
augroup youcompletemeStart
  autocmd!
  autocmd VimEnter * call youcompleteme#Enable()
augroup END

" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
