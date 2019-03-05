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

" This is basic vim plugin boilerplate
let s:save_cpo = &cpo
set cpo&vim

" This needs to be called outside of a function
let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
let s:force_semantic = 0
let s:completion_stopped = 0
" These two variables are initialized in youcompleteme#Enable.
let s:default_completion = {}
let s:completion = {}
let s:previous_allowed_buffer_number = 0
let s:pollers = {
      \   'completion': {
      \     'id': -1,
      \     'wait_milliseconds': 10
      \   },
      \   'file_parse_response': {
      \     'id': -1,
      \     'wait_milliseconds': 100
      \   },
      \   'server_ready': {
      \     'id': -1,
      \     'wait_milliseconds': 100
      \   },
      \   'receive_messages': {
      \     'id': -1,
      \     'wait_milliseconds': 100
      \   }
      \ }
let s:buftype_blacklist = {
      \   'help': 1,
      \   'terminal': 1,
      \   'quickfix': 1
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


function! s:StartMessagePoll()
  if s:pollers.receive_messages.id < 0
    let s:pollers.receive_messages.id = timer_start(
          \ s:pollers.receive_messages.wait_milliseconds,
          \ function( 's:ReceiveMessages' ) )
  endif
endfunction


function! s:ReceiveMessages( timer_id )
  let poll_again = s:Pyeval( 'ycm_state.OnPeriodicTick()' )

  if poll_again
    let s:pollers.receive_messages.id = timer_start(
          \ s:pollers.receive_messages.wait_milliseconds,
          \ function( 's:ReceiveMessages' ) )
  else
    " Don't poll again until we open another buffer
    let s:pollers.receive_messages.id = -1
  endif
endfunction


function! s:SetUpOptions()
  call s:SetUpCommands()
  call s:SetUpCpoptions()
  call s:SetUpCompleteopt()
  call s:SetUpKeyMappings()

  if g:ycm_show_diagnostics_ui
    call s:TurnOffSyntasticForCFamily()
  endif

  call s:SetUpSigns()
  call s:SetUpSyntaxHighlighting()
endfunction


function! youcompleteme#Enable()
  call s:SetUpBackwardsCompatibility()

  if !s:SetUpPython()
    return
  endif

  call s:SetUpOptions()

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
    autocmd BufEnter,CmdwinEnter * call s:OnBufferEnter()
    autocmd BufUnload * call s:OnBufferUnload()
    autocmd InsertLeave * call s:OnInsertLeave()
    autocmd VimLeave * call s:OnVimLeave()
    autocmd CompleteDone * call s:OnCompleteDone()
    autocmd BufEnter,WinEnter * call s:UpdateMatches()
  augroup END

  " The FileType event is not triggered for the first loaded file. We wait until
  " the server is ready to manually run the s:OnFileTypeSet function.
  let s:pollers.server_ready.id = timer_start(
        \ s:pollers.server_ready.wait_milliseconds,
        \ function( 's:PollServerReady' ) )

  let s:default_completion = s:Pyeval( 'vimsupport.NO_COMPLETIONS' )
  let s:completion = s:default_completion
endfunction


function! youcompleteme#EnableCursorMovedAutocommands()
  augroup ycmcompletemecursormove
    autocmd!
    autocmd CursorMoved * call s:OnCursorMovedNormalMode()
    autocmd TextChanged * call s:OnTextChangedNormalMode()
    autocmd TextChangedI * call s:OnTextChangedInsertMode()
    " The TextChangedI event is not triggered when inserting a character while
    " the completion menu is open. We handle this by closing the completion menu
    " just before inserting a character.
    autocmd InsertCharPre * call s:OnInsertChar()
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

import os.path as p
import re
import sys
import traceback
import vim

root_folder = p.normpath( p.join( vim.eval( 's:script_folder_path' ), '..' ) )
third_party_folder = p.join( root_folder, 'third_party' )
python_stdlib_zip_regex = re.compile( 'python[23][0-9]\\.zip' )


def IsStandardLibraryFolder( path ):
  return ( ( p.isfile( path )
             and python_stdlib_zip_regex.match( p.basename( path ) ) )
           or p.isfile( p.join( path, 'os.py' ) ) )


def IsVirtualEnvLibraryFolder( path ):
  return p.isfile( p.join( path, 'orig-prefix.txt' ) )


def GetStandardLibraryIndexInSysPath():
  for index, path in enumerate( sys.path ):
    if ( IsStandardLibraryFolder( path ) and
         not IsVirtualEnvLibraryFolder( path ) ):
      return index
  raise RuntimeError( 'Could not find standard library path in Python path.' )


# Add dependencies to Python path.
dependencies = [ p.join( root_folder, 'python' ),
                 p.join( third_party_folder, 'requests-futures' ),
                 p.join( third_party_folder, 'ycmd' ),
                 p.join( third_party_folder, 'requests_deps', 'idna' ),
                 p.join( third_party_folder, 'requests_deps', 'chardet' ),
                 p.join( third_party_folder,
                         'requests_deps',
                         'urllib3',
                         'src' ),
                 p.join( third_party_folder, 'requests_deps', 'certifi' ),
                 p.join( third_party_folder, 'requests_deps', 'requests' ) ]

# The concurrent.futures module is part of the standard library on Python 3.
if sys.version_info[ 0 ] == 2:
  dependencies.append( p.join( third_party_folder, 'pythonfutures' ) )

sys.path[ 0:0 ] = dependencies

# We enclose this code in a try/except block to avoid backtraces in Vim.
try:
  # The python-future module must be inserted after the standard library path.
  sys.path.insert( GetStandardLibraryIndexInSysPath() + 1,
                   p.join( third_party_folder, 'python-future', 'src' ) )

  # Import the modules used in this file.
  from ycm import base, vimsupport, youcompleteme

  ycm_state = youcompleteme.YouCompleteMe()
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

  for key in g:ycm_key_list_stop_completion
    " When selecting a candidate and closing the completion menu with the <C-y>
    " key, the menu will automatically be reopened because of the TextChangedI
    " event. We define a command to prevent that.
    exe 'inoremap <expr>' . key . ' <SID>StopCompletion( "\' . key . '" )'
  endfor

  if !empty( g:ycm_key_invoke_completion )
    let invoke_key = g:ycm_key_invoke_completion

    " Inside the console, <C-Space> is passed as <Nul> to Vim
    if invoke_key ==# '<C-Space>'
      imap <Nul> <C-Space>
    endif

    silent! exe 'inoremap <unique> <silent> ' . invoke_key .
          \ ' <C-R>=<SID>InvokeSemanticCompletion()<CR>'
  endif

  if !empty( g:ycm_key_detailed_diagnostics )
    silent! exe 'nnoremap <unique> ' . g:ycm_key_detailed_diagnostics .
          \ ' :YcmShowDetailedDiagnostic<CR>'
  endif

  " The TextChangedI event is not triggered when deleting a character while the
  " completion menu is open. We handle this by closing the completion menu on
  " the keys that delete a character in insert mode.
  for key in [ "<BS>", "<C-h>" ]
    silent! exe 'inoremap <unique> <expr> ' . key .
          \ ' <SID>OnDeleteChar( "\' . key . '" )'
  endfor
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
  let g:syntastic_cuda_checkers = []
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
  let buftype = getbufvar( a:buffer, '&buftype' )

  if has_key( s:buftype_blacklist, buftype )
    return 0
  endif

  let filetype = getbufvar( a:buffer, '&filetype' )

  if empty( filetype ) || s:DisableOnLargeFile( a:buffer )
    return 0
  endif

  let whitelist_allows = type( g:ycm_filetype_whitelist ) != type( {} ) ||
        \ has_key( g:ycm_filetype_whitelist, '*' ) ||
        \ has_key( g:ycm_filetype_whitelist, filetype )
  let blacklist_allows = type( g:ycm_filetype_blacklist ) != type( {} ) ||
        \ !has_key( g:ycm_filetype_blacklist, filetype )

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


function! s:SetCompleteFunc()
  let &completefunc = 'youcompleteme#CompleteFunc'
endfunction


function! s:OnVimLeave()
  " Workaround a NeoVim issue - not shutting down timers correctly
  " https://github.com/neovim/neovim/issues/6840
  for poller in values( s:pollers )
    call timer_stop( poller.id )
  endfor
  exec s:python_command "ycm_state.OnVimLeave()"
endfunction


function! s:OnCompleteDone()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  exec s:python_command "ycm_state.OnCompleteDone()"
endfunction


function! s:OnFileTypeSet()
  " The contents of the command-line window are empty when the filetype is set
  " for the first time. Users should never change its filetype so we only rely
  " on the CmdwinEnter event for that window.
  if !empty( getcmdwintype() )
    return
  endif

  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  call s:SetUpCompleteopt()
  call s:SetCompleteFunc()
  call s:StartMessagePoll()

  exec s:python_command "ycm_state.OnBufferVisit()"
  call s:OnFileReadyToParse( 1 )
endfunction


function! s:OnBufferEnter()
  if !s:VisitedBufferRequiresReparse()
    return
  endif

  call s:SetUpCompleteopt()
  call s:SetCompleteFunc()
  call s:StartMessagePoll()

  exec s:python_command "ycm_state.OnBufferVisit()"
  " Last parse may be outdated because of changes from other buffers. Force a
  " new parse.
  call s:OnFileReadyToParse( 1 )
endfunction


function! s:OnBufferUnload()
  " Expanding <abuf> returns the unloaded buffer number as a string but we want
  " it as a true number for the getbufvar function.
  let buffer_number = str2nr( expand( '<abuf>' ) )
  if !s:AllowedToCompleteInBuffer( buffer_number )
    return
  endif

  exec s:python_command "ycm_state.OnBufferUnload( " . buffer_number . " )"
endfunction


function! s:UpdateMatches()
  exec s:python_command "ycm_state.UpdateMatches()"
endfunction


function! s:PollServerReady( timer_id )
  if !s:Pyeval( 'ycm_state.IsServerAlive()' )
    exec s:python_command "ycm_state.NotifyUserIfServerCrashed()"
    " Server crashed. Don't poll it again.
    return
  endif

  if !s:Pyeval( 'ycm_state.CheckIfServerIsReady()' )
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
  if force_parsing || s:Pyeval( "ycm_state.NeedsReparse()" )
    exec s:python_command "ycm_state.OnFileReadyToParse()"

    call timer_stop( s:pollers.file_parse_response.id )
    let s:pollers.file_parse_response.id = timer_start(
          \ s:pollers.file_parse_response.wait_milliseconds,
          \ function( 's:PollFileParseResponse' ) )
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
  if s:Pyeval( "ycm_state.ShouldResendFileParseRequest()" )
    call s:OnFileReadyToParse( 1 )
  endif
endfunction


function! s:SendKeys( keys )
  " By default keys are added to the end of the typeahead buffer. If there are
  " already keys in the buffer, they will be processed first and may change the
  " state that our keys combination was sent for (e.g. <C-X><C-U><C-P> in normal
  " mode instead of insert mode or <C-e> outside of completion mode). We avoid
  " that by inserting the keys at the start of the typeahead buffer with the 'i'
  " option. Also, we don't want the keys to be remapped to something else so we
  " add the 'n' option.
  call feedkeys( a:keys, 'in' )
endfunction


function! s:CloseCompletionMenu()
  if pumvisible()
    call s:SendKeys( "\<C-e>" )
  endif
endfunction


function! s:OnInsertChar()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  call timer_stop( s:pollers.completion.id )
  call s:CloseCompletionMenu()
endfunction


function! s:OnDeleteChar( key )
  if !s:AllowedToCompleteInCurrentBuffer()
    return a:key
  endif

  call timer_stop( s:pollers.completion.id )
  if pumvisible()
    return "\<C-y>" . a:key
  endif
  return a:key
endfunction


function! s:StopCompletion( key )
  call timer_stop( s:pollers.completion.id )
  if pumvisible()
    let s:completion_stopped = 1
    return "\<C-y>"
  endif
  return a:key
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

  if s:completion_stopped
    let s:completion_stopped = 0
    let s:completion = s:default_completion
    return
  endif

  call s:IdentifierFinishedOperations()

  " We have to make sure we correctly leave semantic mode even when the user
  " inserts something like a "operator[]" candidate string which fails
  " CurrentIdentifierFinished check.
  if s:force_semantic && !s:Pyeval( 'base.LastEnteredCharIsIdentifierChar()' )
    let s:force_semantic = 0
  endif

  if &completefunc == "youcompleteme#CompleteFunc" &&
        \ ( g:ycm_auto_trigger || s:force_semantic ) &&
        \ !s:InsideCommentOrStringAndShouldStop() &&
        \ !s:OnBlankLine()
    " Immediately call previous completion to avoid flickers.
    call s:Complete()
    call s:InvokeCompletion()
  endif

  exec s:python_command "ycm_state.OnCursorMoved()"

  if g:ycm_autoclose_preview_window_after_completion
    call s:ClosePreviewWindowIfNeeded()
  endif
endfunction


function! s:OnInsertLeave()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  call timer_stop( s:pollers.completion.id )
  let s:force_semantic = 0
  let s:completion = s:default_completion

  call s:OnFileReadyToParse()
  exec s:python_command "ycm_state.OnInsertLeave()"
  if g:ycm_autoclose_preview_window_after_completion ||
        \ g:ycm_autoclose_preview_window_after_insertion
    call s:ClosePreviewWindowIfNeeded()
  endif
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
  let s:force_semantic = 0
  let s:completion = s:default_completion
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
  exec s:python_command "ycm_state.SendCompletionRequest(" .
        \ "vimsupport.GetBoolValue( 's:force_semantic' ) )"

  call s:PollCompletion()
endfunction


function! s:InvokeSemanticCompletion()
  if &completefunc == "youcompleteme#CompleteFunc"
    let s:force_semantic = 1
    exec s:python_command "ycm_state.SendCompletionRequest( True )"

    call s:PollCompletion()
  endif

  " Since this function is called in a mapping through the expression register
  " <C-R>=, its return value is inserted (see :h c_CTRL-R_=). We don't want to
  " insert anything so we return an empty string.
  return ''
endfunction


function! s:PollCompletion( ... )
  if !s:Pyeval( 'ycm_state.CompletionRequestReady()' )
    let s:pollers.completion.id = timer_start(
          \ s:pollers.completion.wait_milliseconds,
          \ function( 's:PollCompletion' ) )
    return
  endif

  let s:completion = s:Pyeval( 'ycm_state.GetCompletionResponse()' )
  call s:Complete()
endfunction


function! s:Complete()
  " Do not call user's completion function if the start column is after the
  " current column or if there are no candidates. Close the completion menu
  " instead. This avoids keeping the user in completion mode.
  if s:completion.completion_start_column > s:completion.column ||
        \ empty( s:completion.completions )
    call s:CloseCompletionMenu()
  else
    " <c-x><c-u> invokes the user's completion function (which we have set to
    " youcompleteme#CompleteFunc), and <c-p> tells Vim to select the previous
    " completion candidate. This is necessary because by default, Vim selects
    " the first candidate when completion is invoked, and selecting a candidate
    " automatically replaces the current text with it. Calling <c-p> forces Vim
    " to deselect the first candidate and in turn preserve the user's current
    " text until he explicitly chooses to replace it with a completion.
    call s:SendKeys( "\<C-X>\<C-U>\<C-P>" )
  endif
endfunction


function! youcompleteme#CompleteFunc( findstart, base )
  if a:findstart
    " When auto-wrapping is enabled, Vim wraps the current line after the
    " completion request is sent but before calling this function. The starting
    " column returned by the server is invalid in that case and must be
    " recomputed.
    if s:completion.line != line( '.' )
      " Given
      "   scb: column where the completion starts before auto-wrapping
      "   cb: cursor column before auto-wrapping
      "   sca: column where the completion starts after auto-wrapping
      "   ca: cursor column after auto-wrapping
      " we have
      "   ca - sca = cb - scb
      "   sca = scb + ca - cb
      let s:completion.completion_start_column +=
            \ col( '.' ) - s:completion.column
    endif
    return s:completion.completion_start_column - 1
  endif
  return s:completion.completions
endfunction


function! youcompleteme#ServerPid()
  return s:Pyeval( 'ycm_state.ServerPid()' )
endfunction


function! s:SetUpCommands()
  command! YcmRestartServer call s:RestartServer()
  command! YcmDebugInfo call s:DebugInfo()
  command! -nargs=* -complete=custom,youcompleteme#LogsComplete
        \ YcmToggleLogs call s:ToggleLogs(<f-args>)
  if s:Pyeval( 'vimsupport.VimVersionAtLeast( "7.4.1898" )' )
    command! -nargs=* -complete=custom,youcompleteme#SubCommandsComplete -range
          \ YcmCompleter call s:CompleterCommand(<q-mods>,
          \                                      <count>,
          \                                      <line1>,
          \                                      <line2>,
          \                                      <f-args>)
  else
    command! -nargs=* -complete=custom,youcompleteme#SubCommandsComplete -range
          \ YcmCompleter call s:CompleterCommand('',
          \                                      <count>,
          \                                      <line1>,
          \                                      <line2>,
          \                                      <f-args>)
  endif
  command! YcmDiags call s:ShowDiagnostics()
  command! YcmShowDetailedDiagnostic call s:ShowDetailedDiagnostic()
  command! YcmForceCompileAndDiagnostics call s:ForceCompileAndDiagnostics()
endfunction


function! s:RestartServer()
  call s:SetUpOptions()

  exec s:python_command "ycm_state.RestartServer()"

  call timer_stop( s:pollers.receive_messages.id )
  let s:pollers.receive_messages.id = -1

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


function! s:CompleterCommand( mods, count, line1, line2, ... )
  exec s:python_command "ycm_state.SendCommandRequest(" .
        \ "vim.eval( 'a:000' )," .
        \ "vim.eval( 'a:mods' )," .
        \ "vimsupport.GetBoolValue( 'a:count != -1' )," .
        \ "vimsupport.GetIntValue( 'a:line1' )," .
        \ "vimsupport.GetIntValue( 'a:line2' ) )"
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
