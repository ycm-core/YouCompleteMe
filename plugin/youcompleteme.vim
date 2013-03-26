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

let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )

function! s:HasYcmCore()
  let path_prefix = s:script_folder_path . '/../python/'
  if filereadable(path_prefix . 'ycm_core.so')
    return 1
  elseif filereadable(path_prefix . 'ycm_core.pyd')
    return 1
  endif
  return 0
endfunction

if !s:HasYcmCore()
  echohl WarningMsg |
        \ echomsg "ycm_core.[so|pyd] not detected; you need to compile YCM " .
        \ "before using it. Read the docs!" |
        \ echohl None
  finish
endif

let g:loaded_youcompleteme = 1

let g:ycm_min_num_of_chars_for_completion  =
      \ get( g:, 'ycm_min_num_of_chars_for_completion', 2 )

let g:ycm_filetype_whitelist =
      \ get( g:, 'ycm_filetype_whitelist', {
      \   '*' : 1,
      \ } )

" The fallback to g:ycm_filetypes_to_completely_ignore is here because of
" backwards compatibility with previous versions of YCM.
let g:ycm_filetype_blacklist =
      \ get( g:, 'ycm_filetype_blacklist',
      \   get( g:, 'ycm_filetypes_to_completely_ignore', {
      \     'notes' : 1,
      \     'markdown' : 1,
      \     'text' : 1,
      \ } ) )

let g:ycm_filetype_specific_completion_to_disable =
      \ get( g:, 'ycm_filetype_specific_completion_to_disable', {} )

let g:ycm_register_as_syntastic_checker =
      \ get( g:, 'ycm_register_as_syntastic_checker', 1 )

let g:ycm_allow_changing_updatetime =
      \ get( g:, 'ycm_allow_changing_updatetime', 1 )

let g:ycm_add_preview_to_completeopt =
      \ get( g:, 'ycm_add_preview_to_completeopt', 0 )

let g:ycm_complete_in_comments_and_strings =
      \ get( g:, 'ycm_complete_in_comments_and_strings', 0 )

let g:ycm_collect_identifiers_from_comments_and_strings =
      \ get( g:, 'ycm_collect_identifiers_from_comments_and_strings', 0 )

let g:ycm_autoclose_preview_window_after_completion =
      \ get( g:, 'ycm_autoclose_preview_window_after_completion', 0 )

let g:ycm_autoclose_preview_window_after_insertion =
      \ get( g:, 'ycm_autoclose_preview_window_after_insertion', 0 )

let g:ycm_max_diagnostics_to_display =
      \ get( g:, 'ycm_max_diagnostics_to_display', 30 )

let g:ycm_key_list_select_completion =
      \ get( g:, 'ycm_key_list_select_completion', ['<TAB>', '<Down>'] )

let g:ycm_key_list_previous_completion =
      \ get( g:, 'ycm_key_list_previous_completion', ['<S-TAB>', '<Up>'] )

let g:ycm_key_invoke_completion =
      \ get( g:, 'ycm_key_invoke_completion', '<C-Space>' )

let g:ycm_key_detailed_diagnostics =
      \ get( g:, 'ycm_key_detailed_diagnostics', '<leader>d' )

let g:ycm_global_ycm_extra_conf =
      \ get( g:, 'ycm_global_ycm_extra_conf', '' )

let g:ycm_confirm_extra_conf =
      \ get( g:, 'ycm_confirm_extra_conf', 1 )

let g:ycm_extra_conf_globlist =
      \ get( g:, 'ycm_extra_conf_globlist', [] )

let g:ycm_semantic_triggers =
      \ get( g:, 'ycm_semantic_triggers', {
      \   'c' : ['->', '.'],
      \   'objc' : ['->', '.'],
      \   'cpp,objcpp' : ['->', '.', '::'],
      \   'perl' : ['->'],
      \   'php' : ['->', '::'],
      \   'cs,java,javascript,d,vim,ruby,python,perl6,scala,vb,elixir,go' : ['.'],
      \   'lua' : ['.', ':'],
      \   'erlang' : [':'],
      \ } )

" On-demand loading. Let's use the autoload folder and not slow down vim's
" startup procedure.
augroup youcompletemeStart
  autocmd!
  autocmd VimEnter * call youcompleteme#Enable()
augroup END

" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
