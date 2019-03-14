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
elseif v:version < 704 || (v:version == 704 && !has( 'patch1578' ))
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: requires Vim 7.4.1578+." |
        \ echohl None
  if v:version == 704 && has( 'patch8056' )
    " Very very special case for users of the default Vim on macOS. For some
    " reason, that version of Vim contains a completely arbitrary (presumably
    " custom) patch '8056', which fools users (but not our has( 'patch1578' )
    " check) into thinking they have a sufficiently new Vim. In fact they do
    " not and YCM fails to initialise. So we give them a more specific warning.
    echohl WarningMsg
          \ | echomsg
          \ "Info: You appear to be running the default system Vim on macOS. "
          \ . "It reports as patch 8056, but it is really older than 1578. "
          \ . "Please consider MacVim, homebrew Vim or a self-built Vim that "
          \ . "satisfies the minimum requirement."
          \ | echohl None
  endif
  call s:restore_cpo()
  finish
elseif !has( 'timers' )
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: requires Vim compiled with " .
        \ "the timers feature." |
        \ echohl None
  call s:restore_cpo()
  finish
elseif ( v:version > 800 || ( v:version == 800 && has( 'patch1436' ) ) ) &&
     \ !has( 'python_compiled' ) && !has( 'python3_compiled' )
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: requires Vim compiled with " .
        \ "Python (2.7.1+ or 3.4+) support." |
        \ echohl None
  call s:restore_cpo()
  finish
" These calls try to load the Python 2 and Python 3 libraries when Vim is
" compiled dynamically against them. Since only one can be loaded at a time on
" some platforms, we first check if Python 3 is available.
elseif !has( 'python3' ) && !has( 'python' )
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: unable to load Python." |
        \ echohl None
  call s:restore_cpo()
  finish
elseif &encoding !~? 'utf-\?8'
  echohl WarningMsg |
        \ echomsg "YouCompleteMe unavailable: requires UTF-8 encoding. " .
        \ "Put the line 'set encoding=utf-8' in your vimrc." |
        \ echohl None
  call s:restore_cpo()
  finish
endif

let g:loaded_youcompleteme = 1

"
" List of YCM options.
"
let g:ycm_filetype_whitelist =
      \ get( g:, 'ycm_filetype_whitelist', { "*": 1 } )

let g:ycm_filetype_blacklist =
      \ get( g:, 'ycm_filetype_blacklist', {
      \   'tagbar': 1,
      \   'notes': 1,
      \   'markdown': 1,
      \   'netrw': 1,
      \   'unite': 1,
      \   'text': 1,
      \   'vimwiki': 1,
      \   'pandoc': 1,
      \   'infolog': 1,
      \   'mail': 1
      \ } )

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

let g:ycm_key_list_stop_completion =
      \ get( g:, 'ycm_key_list_stop_completion', ['<C-y>'] )

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

let g:ycm_filter_diagnostics =
      \ get( g:, 'ycm_filter_diagnostics', {} )

let g:ycm_always_populate_location_list =
      \ get( g:, 'ycm_always_populate_location_list',
      \ get( g:, 'syntastic_always_populate_loc_list', 0 ) )

let g:ycm_error_symbol =
      \ get( g:, 'ycm_error_symbol',
      \ get( g:, 'syntastic_error_symbol', '>>' ) )

let g:ycm_warning_symbol =
      \ get( g:, 'ycm_warning_symbol',
      \ get( g:, 'syntastic_warning_symbol', '>>' ) )

let g:ycm_complete_in_comments =
      \ get( g:, 'ycm_complete_in_comments', 0 )

let g:ycm_complete_in_strings =
      \ get( g:, 'ycm_complete_in_strings', 1 )

let g:ycm_collect_identifiers_from_tags_files =
      \ get( g:, 'ycm_collect_identifiers_from_tags_files', 0 )

let g:ycm_seed_identifiers_with_syntax =
      \ get( g:, 'ycm_seed_identifiers_with_syntax', 0 )

let g:ycm_goto_buffer_command =
      \ get( g:, 'ycm_goto_buffer_command', 'same-buffer' )

let g:ycm_disable_for_files_larger_than_kb =
      \ get( g:, 'ycm_disable_for_files_larger_than_kb', 1000 )

"
" List of ycmd options.
"
let g:ycm_filepath_completion_use_working_dir =
      \ get( g:, 'ycm_filepath_completion_use_working_dir', 0 )

let g:ycm_auto_trigger =
      \ get( g:, 'ycm_auto_trigger', 1 )

let g:ycm_min_num_of_chars_for_completion =
      \ get( g:, 'ycm_min_num_of_chars_for_completion', 2 )

let g:ycm_min_identifier_candidate_chars =
      \ get( g:, 'ycm_min_num_identifier_candidate_chars', 0 )

let g:ycm_semantic_triggers =
      \ get( g:, 'ycm_semantic_triggers', {} )

let g:ycm_filetype_specific_completion_to_disable =
      \ get( g:, 'ycm_filetype_specific_completion_to_disable',
      \      { 'gitcommit': 1 } )

let g:ycm_collect_identifiers_from_comments_and_strings =
      \ get( g:, 'ycm_collect_identifiers_from_comments_and_strings', 0 )

let g:ycm_max_num_identifier_candidates =
      \ get( g:, 'ycm_max_num_identifier_candidates', 10 )

let g:ycm_max_num_candidates =
      \ get( g:, 'ycm_max_num_candidates', 50 )

let g:ycm_extra_conf_globlist =
      \ get( g:, 'ycm_extra_conf_globlist', [] )

let g:ycm_global_ycm_extra_conf =
      \ get( g:, 'ycm_global_ycm_extra_conf', '' )

let g:ycm_confirm_extra_conf =
      \ get( g:, 'ycm_confirm_extra_conf', 1 )

let g:ycm_max_diagnostics_to_display =
      \ get( g:, 'ycm_max_diagnostics_to_display', 30 )

let g:ycm_filepath_blacklist =
      \ get( g:, 'ycm_filepath_blacklist', {
      \   'html': 1,
      \   'jsx': 1,
      \   'xml': 1
      \ } )

let g:ycm_auto_start_csharp_server =
      \ get( g:, 'ycm_auto_start_csharp_server', 1 )

let g:ycm_auto_stop_csharp_server =
      \ get( g:, 'ycm_auto_stop_csharp_server', 1 )

let g:ycm_use_ultisnips_completer =
      \ get( g:, 'ycm_use_ultisnips_completer', 1 )

let g:ycm_csharp_server_port =
      \ get( g:, 'ycm_csharp_server_port', 0 )

" These options are not documented.
let g:ycm_gocode_binary_path =
      \ get( g:, 'ycm_gocode_binary_path', '' )

let g:ycm_godef_binary_path =
      \ get( g:, 'ycm_godef_binary_path', '' )

let g:ycm_rust_src_path =
      \ get( g:, 'ycm_rust_src_path', '' )

let g:ycm_racerd_binary_path =
      \ get( g:, 'ycm_racerd_binary_path', '' )

let g:ycm_java_jdtls_use_clean_workspace =
      \ get( g:, 'ycm_java_jdtls_use_clean_workspace', 1 )

let g:ycm_use_clangd =
      \ get( g:, 'ycm_use_clangd', 1 )

let g:ycm_clangd_binary_path =
      \ get( g:, 'ycm_clangd_binary_path', '' )

let g:ycm_clangd_args =
      \ get( g:, 'ycm_clangd_args', [] )

let g:ycm_clangd_uses_ycmd_caching =
      \ get( g:, 'ycm_clangd_uses_ycmd_caching', 1 )

" This option is deprecated.
let g:ycm_python_binary_path =
      \ get( g:, 'ycm_python_binary_path', '' )

if has( 'vim_starting' ) " Loading at startup.
  " We defer loading until after VimEnter to allow the gui to fork (see
  " `:h gui-fork`) and avoid a deadlock situation, as explained here:
  " https://github.com/Valloric/YouCompleteMe/pull/2473#issuecomment-267716136
  augroup youcompletemeStart
    autocmd!
    autocmd VimEnter * call youcompleteme#Enable()
  augroup END
else " Manual loading with :packadd.
  call youcompleteme#Enable()
endif

" This is basic vim plugin boilerplate
call s:restore_cpo()
