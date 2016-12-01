" Copyright (C) 2011, 2012  Google Inc.
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

function! s:restore_cpo()
  let &cpo = s:save_cpo
  unlet s:save_cpo
endfunction

if exists( "g:loaded_youcompleteme" )
  call s:restore_cpo()
  finish
elseif v:version < 704 || (v:version == 704 && !has('patch143'))
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: requires Vim 7.4.143+" |
        \ echohl None
  call s:restore_cpo()
  finish
elseif !has( 'python' ) && !has( 'python3' )
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: requires Vim compiled with " .
        \ "Python (2.6+ or 3.3+) support" |
        \ echohl None
  call s:restore_cpo()
  finish
endif

let g:loaded_youcompleteme = 1

" NOTE: Most defaults are in third_party/ycmd/ycmd/default_settings.json. They
" are loaded into Vim globals with the 'ycm_' prefix if such a key does not
" already exist; thus, the user can override the defaults.
" The only defaults that are here are the ones that are only relevant to the YCM
" Vim client and not the ycmd server.

let g:ycm_allow_changing_updatetime =
      \ get( g:, 'ycm_allow_changing_updatetime', 1 )

let g:ycm_open_loclist_on_ycm_diags =
      \ get( g:, 'ycm_open_loclist_on_ycm_diags', 1 )

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

let g:ycm_log_level =
      \ get( g:, 'ycm_log_level',
      \ get( g:, 'ycm_server_log_level', 'info' ) )

let g:ycm_keep_logfiles =
      \ get( g:, 'ycm_keep_logfiles',
      \ get( g:, 'ycm_server_keep_logfiles', 0 ) )

let g:ycm_extra_conf_vim_data =
      \ get( g:, 'ycm_extra_conf_vim_data', [] )

let g:ycm_server_python_interpreter =
      \ get( g:, 'ycm_server_python_interpreter',
      \ get( g:, 'ycm_path_to_python_interpreter', '' ) )

let g:ycm_show_diagnostics_ui =
      \ get( g:, 'ycm_show_diagnostics_ui', 1 )

let g:ycm_enable_diagnostic_signs =
      \ get( g:, 'ycm_enable_diagnostic_signs',
      \ get( g:, 'syntastic_enable_signs', 1 ) )

let g:ycm_enable_diagnostic_highlighting =
      \ get( g:, 'ycm_enable_diagnostic_highlighting',
      \ get( g:, 'syntastic_enable_highlighting', 1 ) )

let g:ycm_echo_current_diagnostic =
      \ get( g:, 'ycm_echo_current_diagnostic',
      \ get( g:, 'syntastic_echo_current_error', 1 ) )

let g:ycm_always_populate_location_list =
      \ get( g:, 'ycm_always_populate_location_list',
      \ get( g:, 'syntastic_always_populate_loc_list', 0 ) )

let g:ycm_error_symbol =
      \ get( g:, 'ycm_error_symbol',
      \ get( g:, 'syntastic_error_symbol', '>>' ) )

let g:ycm_warning_symbol =
      \ get( g:, 'ycm_warning_symbol',
      \ get( g:, 'syntastic_warning_symbol', '>>' ) )

let g:ycm_goto_buffer_command =
      \ get( g:, 'ycm_goto_buffer_command', 'same-buffer' )

let g:ycm_disable_for_files_larger_than_kb =
      \ get( g:, 'ycm_disable_for_files_larger_than_kb', 1000 )

let g:ycm_start_autocmd =
      \ get( g:, 'ycm_start_autocmd', 'VimEnter' )

" On-demand loading. Let's use the autoload folder and not slow down vim's
" startup procedure.
if has( 'vim_starting' ) " loading at startup
  augroup youcompletemeStart
    autocmd!
    execute 'autocmd ' . g:ycm_start_autocmd . ' * call youcompleteme#Enable()'
  augroup END
else " manual loading with :packadd
  call youcompleteme#Enable()
endif

" This is basic vim plugin boilerplate
call s:restore_cpo()
