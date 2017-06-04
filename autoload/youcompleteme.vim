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

" This needs to be called outside of a function
let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
let s:omnifunc_mode = 0

let s:old_cursor_position = []
let s:cursor_moved = 0
let s:previous_allowed_buffer_number = 0
let s:pollers = {
      \   'file_parse_response': {
      \     'id': -1,
      \     'wait_milliseconds': 100
      \   },
      \   'server_ready': {
      \     'id': -1,
      \     'wait_milliseconds': 100
      \   }
      \ }


" When both versions are available, we prefer Python 3 over Python 2:
"  - faster startup (no monkey-patching from python-future);
"  - better Windows support (e.g. temporary paths are not returned in all
"    lowercase);
"  - Python 2 support will eventually be dropped.
function! s:UsingPython3()
  if has('python3')
    return 1
  endif
  return 0
endfunction


let s:using_python3 = s:UsingPython3()
let s:python_until_eof = s:using_python3 ? "python3 << EOF" : "python << EOF"
let s:python_command = s:using_python3 ? "py3 " : "py "


function! s:Pyeval( eval_string )
  if s:using_python3
    return py3eval( a:eval_string )
  endif
  return pyeval( a:eval_string )
endfunction


function! youcompleteme#Enable()
  call s:SetUpBackwardsCompatibility()

  " This can be 0 if YCM libs are old or -1 if an exception occured while
  " executing the function.
  if s:SetUpPython() != 1
    return
  endif

  call s:SetUpCommands()
  call s:SetUpCpoptions()
  call s:SetUpCompleteopt()
  call s:SetUpKeyMappings()

  if g:ycm_show_diagnostics_ui
    call s:TurnOffSyntasticForCFamily()
  endif

  call s:SetUpSigns()
  call s:SetUpSyntaxHighlighting()

  call youcompleteme#EnableCursorMovedAutocommands()
  augroup youcompleteme
    autocmd!
    " Note that these events will NOT trigger for the file vim is started with;
    " so if you do "vim foo.cc", these events will not trigger when that buffer
    " is read. This is because youcompleteme#Enable() is called on VimEnter and
    " that happens *after* FileType has already triggered for the initial file.
    " We don't parse the buffer on the BufRead event since it would only be
    " useful if the buffer filetype is set (we ignore the buffer if there is no
    " filetype) and if so, the FileType event has triggered before and thus the
    " buffer is already parsed.
    autocmd FileType * call s:OnFileTypeSet()
    autocmd BufEnter * call s:OnBufferEnter()
    autocmd BufUnload * call s:OnBufferUnload()
    autocmd InsertLeave * call s:OnInsertLeave()
    autocmd InsertEnter * call s:OnInsertEnter()
    autocmd VimLeave * call s:OnVimLeave()
    autocmd CompleteDone * call s:OnCompleteDone()
  augroup END

  " The FileType event is not triggered for the first loaded file. We wait until
  " the server is ready to manually run the s:OnFileTypeSet function.
  let s:pollers.server_ready.id = timer_start(
        \ s:pollers.server_ready.wait_milliseconds,
        \ function( 's:PollServerReady' ) )
endfunction


function! youcompleteme#EnableCursorMovedAutocommands()
  augroup ycmcompletemecursormove
    autocmd!
    autocmd CursorMoved * call s:OnCursorMovedNormalMode()
    autocmd TextChanged * call s:OnTextChangedNormalMode()
    autocmd TextChangedI * call s:OnTextChangedInsertMode()
  augroup END
endfunction


function! youcompleteme#DisableCursorMovedAutocommands()
  autocmd! ycmcompletemecursormove
endfunction


function! youcompleteme#GetErrorCount()
  return s:Pyeval( 'ycm_state.GetErrorCount()' )
endfunction


function! youcompleteme#GetWarningCount()
  return s:Pyeval( 'ycm_state.GetWarningCount()' )
endfunction


function! s:SetUpPython() abort
  exec s:python_until_eof
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import sys
import traceback
import vim

# Add python sources folder to the system path.
script_folder = vim.eval( 's:script_folder_path' )
sys.path.insert( 0, os.path.join( script_folder, '..', 'python' ) )

from ycm.setup import SetUpSystemPaths, SetUpYCM

# We enclose this code in a try/except block to avoid backtraces in Vim.
try:
  SetUpSystemPaths()

  # Import the modules used in this file.
  from ycm import base, vimsupport

  ycm_state = SetUpYCM()
except Exception as error:
  # We don't use PostVimMessage or EchoText from the vimsupport module because
  # importing this module may fail.
  vim.command( 'redraw | echohl WarningMsg' )
  for line in traceback.format_exc().splitlines():
    vim.command( "echom '{0}'".format( line.replace( "'", "''" ) ) )

  vim.command( "echo 'YouCompleteMe unavailable: {0}'"
               .format( str( error ).replace( "'", "''" ) ) )
  vim.command( 'echohl None' )
  vim.command( 'return 0' )
else:
  vim.command( 'return 1' )
EOF
endfunction


function! s:SetUpKeyMappings()
  " The g:ycm_key_select_completion and g:ycm_key_previous_completion used to
  " exist and are now here purely for the sake of backwards compatibility; we
  " don't want to break users if we can avoid it.

  if exists('g:ycm_key_select_completion') &&
        \ index(g:ycm_key_list_select_completion,
        \       g:ycm_key_select_completion) == -1
    call add(g:ycm_key_list_select_completion, g:ycm_key_select_completion)
  endif

  if exists('g:ycm_key_previous_completion') &&
        \ index(g:ycm_key_list_previous_completion,
        \       g:ycm_key_previous_completion) == -1
    call add(g:ycm_key_list_previous_completion, g:ycm_key_previous_completion)
  endif

  for key in g:ycm_key_list_select_completion
    " With this command, when the completion window is visible, the tab key
    " (default) will select the next candidate in the window. In vim, this also
    " changes the typed-in text to that of the candidate completion.
    exe 'inoremap <expr>' . key .
          \ ' pumvisible() ? "\<C-n>" : "\' . key .'"'
  endfor


  for key in g:ycm_key_list_previous_completion
    " This selects the previous candidate for shift-tab (default)
    exe 'inoremap <expr>' . key .
          \ ' pumvisible() ? "\<C-p>" : "\' . key .'"'
  endfor

  if !empty( g:ycm_key_invoke_completion )
    let invoke_key = g:ycm_key_invoke_completion

    " Inside the console, <C-Space> is passed as <Nul> to Vim
    if invoke_key ==# '<C-Space>'
      imap <Nul> <C-Space>
    endif

    " <c-x><c-o> trigger omni completion, <c-p> deselects the first completion
    " candidate that vim selects by default
    silent! exe 'inoremap <unique> ' . invoke_key .  ' <C-X><C-O><C-P>'
  endif

  if !empty( g:ycm_key_detailed_diagnostics )
    silent! exe 'nnoremap <unique> ' . g:ycm_key_detailed_diagnostics .
          \ ' :YcmShowDetailedDiagnostic<cr>'
  endif
endfunction


function! s:SetUpSigns()
  " We try to ensure backwards compatibility with Syntastic if the user has
  " already defined styling for Syntastic highlight groups.

  if !hlexists( 'YcmErrorSign' )
    if hlexists( 'SyntasticErrorSign')
      highlight link YcmErrorSign SyntasticErrorSign
    else
      highlight link YcmErrorSign error
    endif
  endif

  if !hlexists( 'YcmWarningSign' )
    if hlexists( 'SyntasticWarningSign')
      highlight link YcmWarningSign SyntasticWarningSign
    else
      highlight link YcmWarningSign todo
    endif
  endif

  if !hlexists( 'YcmErrorLine' )
    highlight link YcmErrorLine SyntasticErrorLine
  endif

  if !hlexists( 'YcmWarningLine' )
    highlight link YcmWarningLine SyntasticWarningLine
  endif

  exe 'sign define YcmError text=' . g:ycm_error_symbol .
        \ ' texthl=YcmErrorSign linehl=YcmErrorLine'
  exe 'sign define YcmWarning text=' . g:ycm_warning_symbol .
        \ ' texthl=YcmWarningSign linehl=YcmWarningLine'
endfunction


function! s:SetUpSyntaxHighlighting()
  " We try to ensure backwards compatibility with Syntastic if the user has
  " already defined styling for Syntastic highlight groups.

  if !hlexists( 'YcmErrorSection' )
    if hlexists( 'SyntasticError' )
      highlight link YcmErrorSection SyntasticError
    else
      highlight link YcmErrorSection SpellBad
    endif
  endif

  if !hlexists( 'YcmWarningSection' )
    if hlexists( 'SyntasticWarning' )
      highlight link YcmWarningSection SyntasticWarning
    else
      highlight link YcmWarningSection SpellCap
    endif
  endif
endfunction


function! s:SetUpBackwardsCompatibility()
  let complete_in_comments_and_strings =
        \ get( g:, 'ycm_complete_in_comments_and_strings', 0 )

  if complete_in_comments_and_strings
    let g:ycm_complete_in_strings = 1
    let g:ycm_complete_in_comments = 1
  endif

  " ycm_filetypes_to_completely_ignore is the old name for fileype_blacklist
  if has_key( g:, 'ycm_filetypes_to_completely_ignore' )
    let g:filetype_blacklist =  g:ycm_filetypes_to_completely_ignore
  endif
endfunction


" Needed so that YCM is used instead of Syntastic
function! s:TurnOffSyntasticForCFamily()
  let g:syntastic_cpp_checkers = []
  let g:syntastic_c_checkers = []
  let g:syntastic_objc_checkers = []
  let g:syntastic_objcpp_checkers = []
endfunction


function! s:DisableOnLargeFile( buffer )
  if exists( 'b:ycm_largefile' )
    return b:ycm_largefile
  endif

  let threshold = g:ycm_disable_for_files_larger_than_kb * 1024
  let b:ycm_largefile =
        \ threshold > 0 && getfsize( expand( a:buffer ) ) > threshold
  if b:ycm_largefile
    exec s:python_command "vimsupport.PostVimMessage(" .
          \ "'YouCompleteMe is disabled in this buffer; " .
          \ "the file exceeded the max size (see YCM options).' )"
  endif
  return b:ycm_largefile
endfunction


function! s:AllowedToCompleteInBuffer( buffer )
  let buffer_filetype = getbufvar( a:buffer, '&filetype' )

  if empty( buffer_filetype ) ||
        \ getbufvar( a:buffer, '&buftype' ) ==# 'nofile' ||
        \ buffer_filetype ==# 'qf'
    return 0
  endif

  if s:DisableOnLargeFile( a:buffer )
    return 0
  endif

  let whitelist_allows = has_key( g:ycm_filetype_whitelist, '*' ) ||
        \ has_key( g:ycm_filetype_whitelist, buffer_filetype )
  let blacklist_allows = !has_key( g:ycm_filetype_blacklist, buffer_filetype )

  let allowed = whitelist_allows && blacklist_allows
  if allowed
    let s:previous_allowed_buffer_number = bufnr( a:buffer )
  endif
  return allowed
endfunction


function! s:AllowedToCompleteInCurrentBuffer()
  return s:AllowedToCompleteInBuffer( '%' )
endfunction


function! s:VisitedBufferRequiresReparse()
  if bufnr( '%' ) ==# s:previous_allowed_buffer_number
    return 0
  endif

  return s:AllowedToCompleteInCurrentBuffer()
endfunction


function! s:SetUpCpoptions()
  " Without this flag in cpoptions, critical YCM mappings do not work. There's
  " no way to not have this and have YCM working, so force the flag.
  set cpoptions+=B

  " This prevents the display of "Pattern not found" & similar messages during
  " completion.
  set shortmess+=c
endfunction


function! s:SetUpCompleteopt()
  " Some plugins (I'm looking at you, vim-notes) change completeopt by for
  " instance adding 'longest'. This breaks YCM. So we force our settings.
  " There's no two ways about this: if you want to use YCM then you have to
  " have these completeopt settings, otherwise YCM won't work at all.

  " We need menuone in completeopt, otherwise when there's only one candidate
  " for completion, the menu doesn't show up.
  set completeopt-=menu
  set completeopt+=menuone

  " This is unnecessary with our features. People use this option to insert
  " the common prefix of all the matches and then add more differentiating chars
  " so that they can select a more specific match. With our features, they
  " don't need to insert the prefix; they just type the differentiating chars.
  " Also, having this option set breaks the plugin.
  set completeopt-=longest

  if g:ycm_add_preview_to_completeopt
    set completeopt+=preview
  endif
endfunction


function! s:OnVimLeave()
  exec s:python_command "ycm_state.OnVimLeave()"
endfunction


function! s:OnCompleteDone()
  exec s:python_command "ycm_state.OnCompleteDone()"
endfunction


function! s:OnFileTypeSet()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  call s:SetUpCompleteopt()
  call s:SetCompleteFunc()
  call s:SetOmnicompleteFunc()

  exec s:python_command "ycm_state.OnBufferVisit()"
  call s:OnFileReadyToParse( 1 )
endfunction


function! s:OnBufferEnter()
  if !s:VisitedBufferRequiresReparse()
    return
  endif

  call s:SetUpCompleteopt()
  call s:SetCompleteFunc()
  call s:SetOmnicompleteFunc()

  exec s:python_command "ycm_state.OnBufferVisit()"
  " Last parse may be outdated because of changes from other buffers. Force a
  " new parse.
  call s:OnFileReadyToParse( 1 )
endfunction


function! s:OnBufferUnload()
  " Expanding <abuf> returns the unloaded buffer number as a string but we want
  " it as a true number for the getbufvar function.
  if !s:AllowedToCompleteInBuffer( str2nr( expand( '<abuf>' ) ) )
    return
  endif

  let deleted_buffer_file = expand( '<afile>:p' )
  exec s:python_command "ycm_state.OnBufferUnload(" .
        \ "vim.eval( 'deleted_buffer_file' ) )"
endfunction


function! s:PollServerReady( timer_id )
  if !s:Pyeval( 'ycm_state.IsServerReady()' )
    let s:pollers.server_ready.id = timer_start(
          \ s:pollers.server_ready.wait_milliseconds,
          \ function( 's:PollServerReady' ) )
    return
  endif

  call s:OnFileTypeSet()
endfunction


function! s:OnFileReadyToParse( ... )
  " Accepts an optional parameter that is either 0 or 1. If 1, send a
  " FileReadyToParse event notification, whether the buffer has changed or not;
  " effectively forcing a parse of the buffer. Default is 0.
  let force_parsing = a:0 > 0 && a:1

  " We only want to send a new FileReadyToParse event notification if the buffer
  " has changed since the last time we sent one, or if forced.
  if force_parsing || b:changedtick != get( b:, 'ycm_changedtick', -1 )
    exec s:python_command "ycm_state.OnFileReadyToParse()"

    call timer_stop( s:pollers.file_parse_response.id )
    let s:pollers.file_parse_response.id = timer_start(
          \ s:pollers.file_parse_response.wait_milliseconds,
          \ function( 's:PollFileParseResponse' ) )

    let b:ycm_changedtick = b:changedtick
  endif
endfunction


function! s:PollFileParseResponse( ... )
  if !s:Pyeval( "ycm_state.FileParseRequestReady()" )
    let s:pollers.file_parse_response.id = timer_start(
          \ s:pollers.file_parse_response.wait_milliseconds,
          \ function( 's:PollFileParseResponse' ) )
    return
  endif

  exec s:python_command "ycm_state.HandleFileParseRequest()"
endfunction


function! s:SetCompleteFunc()
  let &completefunc = 'youcompleteme#Complete'
  let &l:completefunc = 'youcompleteme#Complete'
endfunction


function! s:SetOmnicompleteFunc()
  if s:AllowedToCompleteInCurrentFile() && s:Pyeval( 'ycm_state.NativeFiletypeCompletionUsable()' )
    let &omnifunc = 'youcompleteme#OmniComplete'
    let &l:omnifunc = 'youcompleteme#OmniComplete'

  " If we don't have native filetype support but the omnifunc is set to YCM's
  " omnifunc because the previous file the user was editing DID have native
  " support, we remove our omnifunc.
  elseif &omnifunc == 'youcompleteme#OmniComplete'
    let &omnifunc = ''
    let &l:omnifunc = ''
  endif
endfunction


function! s:OnCursorMovedNormalMode()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  exec s:python_command "ycm_state.OnCursorMoved()"
endfunction


function! s:OnTextChangedNormalMode()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  call s:OnFileReadyToParse()
endfunction


function! s:OnTextChangedInsertMode()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  exec s:python_command "ycm_state.OnCursorMoved()"
  call s:UpdateCursorMoved()

  call s:IdentifierFinishedOperations()
  if g:ycm_autoclose_preview_window_after_completion
    call s:ClosePreviewWindowIfNeeded()
  endif

  if g:ycm_auto_trigger || s:omnifunc_mode
    call s:InvokeCompletion()
  endif

  " We have to make sure we correctly leave omnifunc mode even when the user
  " inserts something like a "operator[]" candidate string which fails
  " CurrentIdentifierFinished check.
  if s:omnifunc_mode && !s:Pyeval( 'base.LastEnteredCharIsIdentifierChar()')
    let s:omnifunc_mode = 0
  endif
endfunction


function! s:OnInsertLeave()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  let s:omnifunc_mode = 0
  call s:OnFileReadyToParse()
  exec s:python_command "ycm_state.OnInsertLeave()"
  if g:ycm_autoclose_preview_window_after_completion ||
        \ g:ycm_autoclose_preview_window_after_insertion
    call s:ClosePreviewWindowIfNeeded()
  endif
endfunction


function! s:OnInsertEnter()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  let s:old_cursor_position = []
endfunction


function! s:UpdateCursorMoved()
  let current_position = getpos('.')
  let s:cursor_moved = current_position != s:old_cursor_position
  let s:old_cursor_position = current_position
endfunction


function! s:ClosePreviewWindowIfNeeded()
  let current_buffer_name = bufname('')

  " We don't want to try to close the preview window in special buffers like
  " "[Command Line]"; if we do, Vim goes bonkers. Special buffers always start
  " with '['.
  if current_buffer_name[ 0 ] == '['
    return
  endif

  " This command does the actual closing of the preview window. If no preview
  " window is shown, nothing happens.
  pclose
endfunction


function! s:IdentifierFinishedOperations()
  if !s:Pyeval( 'base.CurrentIdentifierFinished()' )
    return
  endif
  exec s:python_command "ycm_state.OnCurrentIdentifierFinished()"
  let s:omnifunc_mode = 0
endfunction


" Returns 1 when inside comment and 2 when inside string
function! s:InsideCommentOrString()
  " Has to be col('.') -1 because col('.') doesn't exist at this point. We are
  " in insert mode when this func is called.
  let syntax_group = synIDattr(
        \ synIDtrans( synID( line( '.' ), col( '.' ) - 1, 1 ) ), 'name')

  if stridx(syntax_group, 'Comment') > -1
    return 1
  endif

  if stridx(syntax_group, 'String') > -1
    return 2
  endif

  return 0
endfunction


function! s:InsideCommentOrStringAndShouldStop()
  let retval = s:InsideCommentOrString()
  let inside_comment = retval == 1
  let inside_string = retval == 2

  if inside_comment && g:ycm_complete_in_comments ||
        \ inside_string && g:ycm_complete_in_strings
    return 0
  endif

  return retval
endfunction


function! s:OnBlankLine()
  return s:Pyeval( 'not vim.current.line or vim.current.line.isspace()' )
endfunction


function! s:InvokeCompletion()
  if &completefunc != "youcompleteme#Complete"
    return
  endif

  if s:InsideCommentOrStringAndShouldStop() || s:OnBlankLine()
    return
  endif

  " This is tricky. First, having 'refresh' set to 'always' in the dictionary
  " that our completion function returns makes sure that our completion function
  " is called on every keystroke. Second, when the sequence of characters the
  " user typed produces no results in our search an infinite loop can occur. The
  " problem is that our feedkeys call triggers the OnCursorMovedI event which we
  " are tied to. We prevent this infinite loop from starting by making sure that
  " the user has moved the cursor since the last time we provided completion
  " results.
  if !s:cursor_moved
    return
  endif

  " <c-x><c-u> invokes the user's completion function (which we have set to
  " youcompleteme#Complete), and <c-p> tells Vim to select the previous
  " completion candidate. This is necessary because by default, Vim selects the
  " first candidate when completion is invoked, and selecting a candidate
  " automatically replaces the current text with it. Calling <c-p> forces Vim to
  " deselect the first candidate and in turn preserve the user's current text
  " until he explicitly chooses to replace it with a completion.
  call feedkeys( "\<C-X>\<C-U>\<C-P>", 'n' )
endfunction


" This is our main entry point. This is what vim calls to get completions.
function! youcompleteme#Complete( findstart, base )
  " After the user types one character after the call to the omnifunc, the
  " completefunc will be called because of our mapping that calls the
  " completefunc on every keystroke. Therefore we need to delegate the call we
  " 'stole' back to the omnifunc
  if s:omnifunc_mode
    return youcompleteme#OmniComplete( a:findstart, a:base )
  endif

  if a:findstart
    " InvokeCompletion has this check but we also need it here because of random
    " Vim bugs and unfortunate interactions with the autocommands of other
    " plugins
    if !s:cursor_moved
      " for vim, -2 means not found but don't trigger an error message
      " see :h complete-functions
      return -2
    endif

    exec s:python_command "ycm_state.CreateCompletionRequest()"
    return s:Pyeval( 'base.CompletionStartColumn()' )
  else
    return s:Pyeval( 'ycm_state.GetCompletions()' )
  endif
endfunction


function! youcompleteme#OmniComplete( findstart, base )
  if a:findstart
    let s:omnifunc_mode = 1
    exec s:python_command "ycm_state.CreateCompletionRequest(" .
          \ "force_semantic = True )"
    return s:Pyeval( 'base.CompletionStartColumn()' )
  else
    return s:Pyeval( 'ycm_state.GetCompletions()' )
  endif
endfunction


function! youcompleteme#ServerPid()
  return s:Pyeval( 'ycm_state.ServerPid()' )
endfunction


function! s:SetUpCommands()
  command! YcmRestartServer call s:RestartServer()
  command! YcmDebugInfo call s:DebugInfo()
  command! -nargs=* -complete=custom,youcompleteme#LogsComplete
        \ YcmToggleLogs call s:ToggleLogs(<f-args>)
  command! -nargs=* -complete=custom,youcompleteme#SubCommandsComplete
        \ YcmCompleter call s:CompleterCommand(<f-args>)
  command! YcmDiags call s:ShowDiagnostics()
  command! YcmShowDetailedDiagnostic call s:ShowDetailedDiagnostic()
  command! YcmForceCompileAndDiagnostics call s:ForceCompileAndDiagnostics()
endfunction


function! s:RestartServer()
  exec s:python_command "ycm_state.RestartServer()"
  call timer_stop( s:pollers.server_ready.id )
  let s:pollers.server_ready.id = timer_start(
        \ s:pollers.server_ready.wait_milliseconds,
        \ function( 's:PollServerReady' ) )
endfunction


function! s:DebugInfo()
  echom "Printing YouCompleteMe debug information..."
  let debug_info = s:Pyeval( 'ycm_state.DebugInfo()' )
  for line in split( debug_info, "\n" )
    echom '-- ' . line
  endfor
endfunction


function! s:ToggleLogs(...)
  exec s:python_command "ycm_state.ToggleLogs( *vim.eval( 'a:000' ) )"
endfunction


function! youcompleteme#LogsComplete( arglead, cmdline, cursorpos )
  return join( s:Pyeval( 'list( ycm_state.GetLogfiles() )' ), "\n" )
endfunction


function! s:CompleterCommand(...)
  " CompleterCommand will call the OnUserCommand function of a completer.
  " If the first arguments is of the form "ft=..." it can be used to specify the
  " completer to use (for example "ft=cpp").  Else the native filetype completer
  " of the current buffer is used.  If no native filetype completer is found and
  " no completer was specified this throws an error.  You can use
  " "ft=ycm:ident" to select the identifier completer.
  " The remaining arguments will be passed to the completer.
  let arguments = copy(a:000)
  let completer = ''

  if a:0 > 0 && strpart(a:1, 0, 3) == 'ft='
    if a:1 == 'ft=ycm:ident'
      let completer = 'identifier'
    endif
    let arguments = arguments[1:]
  endif

  exec s:python_command "ycm_state.SendCommandRequest(" .
        \ "vim.eval( 'l:arguments' ), vim.eval( 'l:completer' ) )"
endfunction


function! youcompleteme#SubCommandsComplete( arglead, cmdline, cursorpos )
  return join( s:Pyeval( 'ycm_state.GetDefinedSubcommands()' ), "\n" )
endfunction


function! youcompleteme#OpenGoToList()
  exec s:python_command "vimsupport.PostVimMessage(" .
        \ "'WARNING: youcompleteme#OpenGoToList function is deprecated. " .
        \ "Do NOT use it.' )"
  exec s:python_command "vimsupport.OpenQuickFixList( True, True )"
endfunction


function! s:ShowDiagnostics()
  exec s:python_command "ycm_state.ShowDiagnostics()"
endfunction


function! s:ShowDetailedDiagnostic()
  exec s:python_command "ycm_state.ShowDetailedDiagnostic()"
endfunction


function! s:ForceCompileAndDiagnostics()
  exec s:python_command "ycm_state.ForceCompileAndDiagnostics()"
endfunction


" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
