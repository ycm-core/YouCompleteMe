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

let s:DEBUG = 0

" This needs to be called outside of a function
let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
let s:force_semantic = 0
let s:completion_stopped = 0
" These two variables are initialized in youcompleteme#Enable.
let s:default_completion = {}
let s:completion = s:default_completion
let s:default_signature_help = {}
let s:signature_help = s:default_completion
let s:previous_allowed_buffer_number = 0
let s:pollers = {
      \   'completion': {
      \     'id': -1,
      \     'wait_milliseconds': 10
      \   },
      \   'signature_help': {
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
let s:last_char_inserted_by_user = v:true
let s:enable_hover = 0
let s:cursorhold_popup = -1

" We can use one of two approaches to auto-triggering completion
"  * completefunc - the classic way - we set completefunc to our function and
"    use feedkeys() to trigger user-defined
"  * complete() - the 'new' way - this uses complete() and TextChangedP to avoid
"    closing the pum on every keystroke. This reduces redraw and flickering
"    appreciably, but is only supported on more recent vims.
let s:COMPLETION_COMPLETEFUNC = 0
let s:COMPLETION_TEXTCHANGEDP = 1

" By default (if possible) use the new complete()/TextChangedP API
let s:completion_api = get( g:,
                          \ 'ycm_use_completion_api',
                          \ s:COMPLETION_TEXTCHANGEDP )

" Fall back to using completefunc if the TextChangedP/CompleteChanged API
" isn't available. Both are needed to ensure correct behaviour with the 'new'
" complete() api
if !exists( '##TextChangedP' ) || !exists( '##CompleteChanged' )
      \ || s:completion_api != s:COMPLETION_TEXTCHANGEDP
  let s:completion_api = s:COMPLETION_COMPLETEFUNC
endif


function! s:StartMessagePoll()
  if s:pollers.receive_messages.id < 0
    let s:pollers.receive_messages.id = timer_start(
          \ s:pollers.receive_messages.wait_milliseconds,
          \ function( 's:ReceiveMessages' ) )
  endif
endfunction


function! s:ReceiveMessages( timer_id )
  let poll_again = v:false
  if s:AllowedToCompleteInCurrentBuffer()
    let poll_again = py3eval( 'ycm_state.OnPeriodicTick()' )
  endif

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
    autocmd BufWritePost,FileWritePost * call s:OnFileSave()
    autocmd FileType * call s:OnFileTypeSet()
    autocmd BufEnter,CmdwinEnter * call s:OnBufferEnter()
    autocmd BufUnload * call s:OnBufferUnload()
    autocmd InsertLeave * call s:OnInsertLeave()
    autocmd VimLeave * call s:OnVimLeave()
    autocmd CompleteDone * call s:OnCompleteDone()
    if exists( '##CompleteChanged' )
      autocmd CompleteChanged * call s:OnCompleteChanged()
    endif
    autocmd BufEnter,WinEnter * call s:UpdateMatches()
  augroup END

  " The FileType event is not triggered for the first loaded file. We wait until
  " the server is ready to manually run the s:OnFileTypeSet function.
  let s:pollers.server_ready.id = timer_start(
        \ s:pollers.server_ready.wait_milliseconds,
        \ function( 's:PollServerReady' ) )

  let s:default_completion = py3eval( 'vimsupport.NO_COMPLETIONS' )
  let s:completion = s:default_completion

  if exists( '*prop_type_add' ) && exists( '*prop_type_delete' )
    hi default YCMInverse term=reverse cterm=reverse gui=reverse
    call prop_type_delete( 'YCM-signature-help-current-argument' )
    call prop_type_add( 'YCM-signature-help-current-argument', {
          \   'highlight': 'YCMInverse',
          \   'combine':   1,
          \   'priority':  50,
          \ } )
  endif
endfunction


function! youcompleteme#EnableCursorMovedAutocommands()
  augroup ycmcompletemecursormove
    autocmd!
    autocmd CursorMoved * call s:OnCursorMovedNormalMode()
    autocmd TextChanged * call s:OnTextChangedNormalMode()
    autocmd TextChangedI * call s:OnTextChangedInsertMode( v:false )
    if s:completion_api == s:COMPLETION_TEXTCHANGEDP
      autocmd TextChangedP * call s:OnTextChangedInsertMode( v:true )
    endif
    autocmd InsertCharPre * call s:OnInsertChar()
  augroup END
endfunction


function! youcompleteme#DisableCursorMovedAutocommands()
  autocmd! ycmcompletemecursormove
endfunction


function! youcompleteme#GetErrorCount()
  return py3eval( 'ycm_state.GetErrorCount()' )
endfunction


function! youcompleteme#GetWarningCount()
  return py3eval( 'ycm_state.GetWarningCount()' )
endfunction


function! s:SetUpPython() abort
  py3 << EOF
import os.path as p
import sys
import traceback
import vim

root_folder = p.normpath( p.join( vim.eval( 's:script_folder_path' ), '..' ) )
third_party_folder = p.join( root_folder, 'third_party' )

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

sys.path[ 0:0 ] = dependencies

# We enclose this code in a try/except block to avoid backtraces in Vim.
try:
  # Import the modules used in this file.
  from ycm import base, vimsupport, youcompleteme

  if 'ycm_state' in globals():
    # If re-initializing, pretend that we shut down
    ycm_state.OnVimLeave()
    del ycm_state

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
    exe 'inoremap <expr>' . key .  ' pumvisible() ? "\<C-n>" : "\' . key .'"'
  endfor

  for key in g:ycm_key_list_previous_completion
    " This selects the previous candidate for shift-tab (default)
    exe 'inoremap <expr>' . key . ' pumvisible() ? "\<C-p>" : "\' . key .'"'
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
          \ ' <C-R>=<SID>RequestSemanticCompletion()<CR>'
  endif

  if !empty( g:ycm_key_detailed_diagnostics )
    silent! exe 'nnoremap <unique> ' . g:ycm_key_detailed_diagnostics .
          \ ' :YcmShowDetailedDiagnostic<CR>'
  endif

  if s:completion_api == s:COMPLETION_COMPLETEFUNC
    " The TextChangedI event is not triggered when deleting a character while
    " the completion menu is open. We handle this by closing the completion menu
    " on the keys that delete a character in insert mode.
    for key in [ "<BS>", "<C-h>" ]
      silent! exe 'inoremap <unique> <expr> ' . key .
            \ ' <SID>OnDeleteChar( "\' . key . '" )'
    endfor
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
    py3 vimsupport.PostVimMessage( 'YouCompleteMe is disabled in this buffer;' +
          \ ' the file exceeded the max size (see YCM options).' )
  endif
  return b:ycm_largefile
endfunction

function! s:HasAnyKey( dict, keys )
  for key in a:keys
    if has_key( a:dict, key )
      return 1
    endif
  endfor
  return 0
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
        \ s:HasAnyKey( g:ycm_filetype_whitelist, split( filetype, '\.' ) )
  let blacklist_allows = type( g:ycm_filetype_blacklist ) != type( {} ) ||
        \ !s:HasAnyKey( g:ycm_filetype_blacklist, split( filetype, '\.' ) )

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
  if s:completion_api == s:COMPLETION_COMPLETEFUNC
    let &completefunc = 'youcompleteme#CompleteFunc'
  endif
  let b:ycm_completing = 1
endfunction


function s:StopPoller( poller ) abort
  call timer_stop( a:poller.id )
  let a:poller.id = -1
endfunction


function! s:OnVimLeave()
  " Workaround a NeoVim issue - not shutting down timers correctly
  " https://github.com/neovim/neovim/issues/6840
  for poller in values( s:pollers )
    call s:StopPoller( poller )
  endfor
  py3 ycm_state.OnVimLeave()
endfunction


function! s:OnCompleteDone()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  if s:DEBUG
    call ch_log( 'ycm: s:OnCompleteDone()' .
               \ ' - last_char_inserted_by_user=' .
               \ s:last_char_inserted_by_user .
               \ ' - v:completed_item=' .
               \ string( v:completed_item ) )
  endif

  let s:last_char_inserted_by_user = v:false

  py3 ycm_state.OnCompleteDone()
  call s:UpdateSignatureHelp()
endfunction


function! s:OnCompleteChanged()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  if s:DEBUG
    call ch_log( 'ycm: s:OnCompleteChanged()' .
               \ ' - last_char_inserted_by_user=' .
               \ s:last_char_inserted_by_user .
               \ ' - v:event=' .
               \ string( v:event ) )
  endif

  if ! empty( v:event.completed_item )
    let s:last_char_inserted_by_user = v:false
  endif

  call s:UpdateSignatureHelp()
endfunction


function! s:EnableAutoHover()
  if g:ycm_auto_hover ==# 'CursorHold' && s:enable_hover
    augroup YcmBufHover
      autocmd! * <buffer>
      autocmd CursorHold <buffer> call s:Hover()
    augroup END
  endif
endfunction


function! s:DisableAutoHover()
  augroup YcmBufHover
    autocmd! * <buffer>
  augroup END
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
  call s:EnableAutoHover()

  py3 ycm_state.OnFileTypeSet()
  call s:OnFileReadyToParse( 1 )
endfunction


function! s:OnFileSave()
  let buffer_number = str2nr( expand( '<abuf>' ) )
  if !s:AllowedToCompleteInBuffer( buffer_number )
    return
  endif
  py3 ycm_state.OnFileSave( vimsupport.GetIntValue( 'buffer_number' ) )
endfunction


function! s:OnBufferEnter()
  call s:StartMessagePoll()
  if !s:VisitedBufferRequiresReparse()
    return
  endif

  call s:SetUpCompleteopt()
  call s:SetCompleteFunc()

  py3 ycm_state.OnBufferVisit()
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

  py3 ycm_state.OnBufferUnload( vimsupport.GetIntValue( 'buffer_number' ) )
endfunction


function! s:UpdateMatches()
  py3 ycm_state.UpdateMatches()
endfunction


function! s:PollServerReady( timer_id )
  if !py3eval( 'ycm_state.IsServerAlive()' )
    py3 ycm_state.NotifyUserIfServerCrashed()
    " Server crashed. Don't poll it again.
    return
  endif

  if !py3eval( 'ycm_state.CheckIfServerIsReady()' )
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
  if force_parsing || py3eval( "ycm_state.NeedsReparse()" )
    " We switched buffers or somethuing, so claer.
    " FIXME: sig hekp should be buffer local?
    call s:ClearSignatureHelp()
    py3 ycm_state.OnFileReadyToParse()

    call s:StopPoller( s:pollers.file_parse_response )
    let s:pollers.file_parse_response.id = timer_start(
          \ s:pollers.file_parse_response.wait_milliseconds,
          \ function( 's:PollFileParseResponse' ) )
  endif
endfunction


function! s:PollFileParseResponse( ... )
  if !py3eval( "ycm_state.FileParseRequestReady()" )
    let s:pollers.file_parse_response.id = timer_start(
          \ s:pollers.file_parse_response.wait_milliseconds,
          \ function( 's:PollFileParseResponse' ) )
    return
  endif

  py3 ycm_state.HandleFileParseRequest()
  if py3eval( "ycm_state.ShouldResendFileParseRequest()" )
    call s:OnFileReadyToParse( 1 )
  endif
endfunction


function! s:SendKeys( keys )
  " By default keys are added to the end of the typeahead buffer. If there are
  " already keys in the buffer, they will be processed first and may change
  " the state that our keys combination was sent for (e.g. <C-X><C-U><C-P> in
  " normal mode instead of insert mode or <C-e> outside of completion mode).
  " We avoid that by inserting the keys at the start of the typeahead buffer
  " with the 'i' option. Also, we don't want the keys to be remapped to
  " something else so we add the 'n' option.
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

  if s:DEBUG
    call ch_log( 'ycm: s:OnInsertChar()' .
               \ ' - last_char_inserted_by_user=' .
               \ s:last_char_inserted_by_user .
               \ ' - v:char = ' .
               \ v:char )
  endif

  let s:last_char_inserted_by_user = v:true

  if s:completion_api == s:COMPLETION_COMPLETEFUNC
    call s:StopPoller( s:pollers.completion )
    call s:StopPoller( s:pollers.signature_help )
    call s:CloseCompletionMenu()
  endif
endfunction


if s:completion_api == s:COMPLETION_COMPLETEFUNC
  function! s:OnDeleteChar( key )
    if !s:AllowedToCompleteInCurrentBuffer()
      return a:key
    endif

    call s:StopPoller( s:pollers.completion )
    call s:StopPoller( s:pollers.signature_help )
    if pumvisible()
      return "\<C-y>" . a:key
    endif
    return a:key
  endfunction
endif


function! s:StopCompletion( key )
  call s:StopPoller( s:pollers.completion )

  call s:ClearSignatureHelp()

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

  py3 ycm_state.OnCursorMoved()
endfunction


function! s:OnTextChangedNormalMode()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  call s:OnFileReadyToParse()
endfunction


function! s:OnTextChangedInsertMode( popup_is_visible )
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  if s:DEBUG
    call ch_log( 'ycm: s:OnTextChangedInsertMode( ' . a:popup_is_visible . ')' .
               \ ' - last_char_inserted_by_user=' .
               \ s:last_char_inserted_by_user )
  endif

  if a:popup_is_visible && !s:last_char_inserted_by_user
    " If the last "input" wasn't from a user typing (i.e. didn't come from
    " InsertCharPre, then ignore this change in the text. This prevents ctrl-n
    " or tab from causing us to re-filter the list based on the now-selected
    " item.
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
  if s:force_semantic && !py3eval( 'base.LastEnteredCharIsIdentifierChar()' )
    let s:force_semantic = 0
  endif

  if get( b:, 'ycm_completing' ) &&
        \ ( g:ycm_auto_trigger || s:force_semantic ) &&
        \ !s:InsideCommentOrStringAndShouldStop() &&
        \ !s:OnBlankLine()
    " The call to s:Complete here is necessary, to minimize flicker when we
    " close the pum on every keypress. In that case, we try to quickly show it
    " again with whatver the latest completion result is. When using complete(),
    " we don't need to do this, as we only close the pum when there are no
    " completions. However, it's still useful as we don't want Vim's filtering
    " to _ever_ apply. Examples of when this is problematic is when typing some
    " keys to filter (that are not a prefix of the completion), then deleting a
    " character. Normally Vim would re-filter based on the new "query", but we
    " don't want that.
    call s:Complete()
    call s:RequestCompletion()

    call s:UpdateSignatureHelp()
    call s:RequestSignatureHelp()
  endif

  py3 ycm_state.OnCursorMoved()

  if g:ycm_autoclose_preview_window_after_completion
    call s:ClosePreviewWindowIfNeeded()
  endif
endfunction


function! s:OnInsertLeave()
  if !s:AllowedToCompleteInCurrentBuffer()
    return
  endif

  let s:last_char_inserted_by_user = v:false

  call s:StopPoller( s:pollers.completion )
  let s:force_semantic = 0
  let s:completion = s:default_completion

  call s:OnFileReadyToParse()
  py3 ycm_state.OnInsertLeave()
  if g:ycm_autoclose_preview_window_after_completion ||
        \ g:ycm_autoclose_preview_window_after_insertion
    call s:ClosePreviewWindowIfNeeded()
  endif

  call s:ClearSignatureHelp()
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
  if !py3eval( 'base.CurrentIdentifierFinished()' )
    return
  endif
  py3 ycm_state.OnCurrentIdentifierFinished()
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
  return py3eval( 'not vim.current.line or vim.current.line.isspace()' )
endfunction


function! s:RequestCompletion()
  if s:completion_api == s:COMPLETION_TEXTCHANGEDP
    call s:StopPoller( s:pollers.completion )
  endif

  py3 ycm_state.SendCompletionRequest(
        \ vimsupport.GetBoolValue( 's:force_semantic' ) )

  if s:completion_api == s:COMPLETION_TEXTCHANGEDP &&
        \ py3eval( 'ycm_state.CompletionRequestReady()' )
    " We can't call complete() syncrhounsouly in the TextChangedI/TextChangedP
    " autocommmands (it's designed to be used async only completion). The result
    " (somewhat oddly) is that the completion menu is shown, but ctrl-n doesn't
    " actually select anything.
    " When the request is satisfied synchronously (e.g. the omnicompleter), we
    " must return to the main loop before triggering completion, so we use a 0ms
    " timer for that.
    let s:pollers.completion.id = timer_start( 0,
                                             \ function( 's:PollCompletion' ) )
  else
    " Otherwise, use our usual poll timeout
    call s:PollCompletion()
  endif
endfunction


function! s:RequestSemanticCompletion()
  if !s:AllowedToCompleteInCurrentBuffer()
    return ''
  endif

  if get( b:, 'ycm_completing' )
    let s:force_semantic = 1
    if s:completion_api == s:COMPLETION_TEXTCHANGEDP
      call s:StopPoller( s:pollers.completion )
    endif
    py3 ycm_state.SendCompletionRequest( True )

    if s:completion_api == s:COMPLETION_TEXTCHANGEDP &&
          \ py3eval( 'ycm_state.CompletionRequestReady()' )
      " We can't call complete() syncrhounsouly in the TextChangedI/TextChangedP
      " autocommmands (it's designed to be used async only completion). The
      " result (somewhat oddly) is that the completion menu is shown, but ctrl-n
      " doesn't actually select anything.  When the request is satisfied
      " synchronously (e.g. the omnicompleter), we must return to the main loop
      " before triggering completion, so we use a 0ms timer for that.
      let s:pollers.completion.id = timer_start(
            \ 0,
            \ function( 's:PollCompletion' ) )
    else
      " Otherwise, use our usual poll timeout
      call s:PollCompletion()
    endif
  endif

  " Since this function is called in a mapping through the expression register
  " <C-R>=, its return value is inserted (see :h c_CTRL-R_=). We don't want to
  " insert anything so we return an empty string.
  return ''
endfunction


function! s:PollCompletion( ... )
  if !py3eval( 'ycm_state.CompletionRequestReady()' )
    let s:pollers.completion.id = timer_start(
          \ s:pollers.completion.wait_milliseconds,
          \ function( 's:PollCompletion' ) )
    return
  endif

  let s:completion = py3eval( 'ycm_state.GetCompletionResponse()' )
  call s:Complete()
endfunction


function! s:ShouldUseSignatureHelp()
  return py3eval( 'vimsupport.VimSupportsPopupWindows()' )
endfunction


function! s:RequestSignatureHelp()
  if !s:ShouldUseSignatureHelp()
    return
  endif

  call s:StopPoller( s:pollers.signature_help )

  if py3eval( 'ycm_state.SendSignatureHelpRequest()' )
    call s:PollSignatureHelp()
  endif
endfunction


function! s:PollSignatureHelp( ... )
  if !s:ShouldUseSignatureHelp()
    return
  endif

  if a:0 == 0 && s:pollers.signature_help.id >= 0
    " OK this is a bug. We have tried to poll for a response while the timer is
    " already running. Just return and wait for the timer to fire.
    return
  endif

  if !py3eval( 'ycm_state.SignatureHelpRequestReady()' )
    let s:pollers.signature_help.id = timer_start(
          \ s:pollers.signature_help.wait_milliseconds,
          \ function( 's:PollSignatureHelp' ) )
    return
  endif

  let s:signature_help = py3eval( 'ycm_state.GetSignatureHelpResponse()' )
  call s:UpdateSignatureHelp()
endfunction


if s:completion_api == s:COMPLETION_TEXTCHANGEDP
  function! s:Complete()
    " It's possible for us to be called (by our timer) when we're not _strictly_
    " in insert mode. This can happen when mode is temporarily switched, e.g.
    " due to Ctrl-r or Ctrl-o or a timer or something. If we're not in insert
    " mode _now_ do nothing (FIXME: or should we queue a timer ?)
    if count( [ 'i', 'R' ], mode() ) == 0
      return
    endif

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
    if len( s:completion.completions )
      let old_completeopt = &completeopt
      set completeopt+=noselect
      call complete( s:completion.completion_start_column,
                   \ s:completion.completions )
      let &completeopt = old_completeopt
    elseif pumvisible()
      call s:CloseCompletionMenu()
    endif
  endfunction
else
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
      " the first candidate when completion is invoked, and selecting a
      " candidate automatically replaces the current text with it. Calling <c-p>
      " forces Vim to deselect the first candidate and in turn preserve the
      " user's current text until he explicitly chooses to replace it with a
      " completion.
      call s:SendKeys( "\<C-X>\<C-U>\<C-P>" )
    endif
    " Displaying or hiding the PUM might mean we need to hide the sig help
    call s:UpdateSignatureHelp()
  endfunction

  function! youcompleteme#CompleteFunc( findstart, base )
    if a:findstart
      " When auto-wrapping is enabled, Vim wraps the current line after the
      " completion request is sent but before calling this function. The
      " starting column returned by the server is invalid in that case and must
      " be recomputed.
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
endif

function! s:UpdateSignatureHelp()
  if !s:ShouldUseSignatureHelp()
    return
  endif

  call py3eval(
        \ 'ycm_state.UpdateSignatureHelp( vim.eval( "s:signature_help" ) )' )
endfunction


function! s:ClearSignatureHelp()
  if !s:ShouldUseSignatureHelp()
    return
  endif

  call s:StopPoller( s:pollers.signature_help )
  let s:signature_help = s:default_signature_help
  call py3eval( 'ycm_state.ClearSignatureHelp()' )
endfunction


function! youcompleteme#ServerPid()
  return py3eval( 'ycm_state.ServerPid()' )
endfunction


function! s:SetUpCommands()
  command! YcmRestartServer call s:RestartServer()
  command! YcmDebugInfo call s:DebugInfo()
  command! -nargs=* -complete=custom,youcompleteme#LogsComplete -count=0
        \ YcmToggleLogs call s:ToggleLogs( <f-count>,
                                         \ <f-mods>,
                                         \ <f-args>)
  if py3eval( 'vimsupport.VimVersionAtLeast( "7.4.1898" )' )
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

  py3 ycm_state.RestartServer()

  call s:StopPoller( s:pollers.receive_messages )
  call s:ClearSignatureHelp()

  call s:StopPoller( s:pollers.server_ready )
  let s:pollers.server_ready.id = timer_start(
        \ s:pollers.server_ready.wait_milliseconds,
        \ function( 's:PollServerReady' ) )
endfunction


function! s:DebugInfo()
  echom "Printing YouCompleteMe debug information..."
  let debug_info = py3eval( 'ycm_state.DebugInfo()' )
  echom '-- Completion API: ' . string( s:completion_api )
  for line in split( debug_info, "\n" )
    echom '-- ' . line
  endfor
endfunction


function! s:ToggleLogs( count, ... )
  py3 ycm_state.ToggleLogs( vimsupport.GetIntValue( 'a:count' ),
                          \ *vim.eval( 'a:000' ) )
endfunction


function! youcompleteme#LogsComplete( arglead, cmdline, cursorpos )
  return join( py3eval( 'list( ycm_state.GetLogfiles() )' ), "\n" )
endfunction


function! youcompleteme#GetCommandResponse( ... )
  if !s:AllowedToCompleteInCurrentBuffer()
    return ''
  endif

  if !get( b:, 'ycm_completing' )
    return ''
  endif

  return py3eval( 'ycm_state.GetCommandResponse( vim.eval( "a:000" ) )' )
endfunction


function! s:CompleterCommand( mods, count, line1, line2, ... )
  py3 ycm_state.SendCommandRequest(
        \ vim.eval( 'a:000' ),
        \ vim.eval( 'a:mods' ),
        \ vimsupport.GetBoolValue( 'a:count != -1' ),
        \ vimsupport.GetIntValue( 'a:line1' ),
        \ vimsupport.GetIntValue( 'a:line2' ) )
endfunction


function! youcompleteme#SubCommandsComplete( arglead, cmdline, cursorpos )
  return join( py3eval( 'ycm_state.GetDefinedSubcommands()' ), "\n" )
endfunction


function! youcompleteme#GetDefinedSubcommands()
  if !s:AllowedToCompleteInCurrentBuffer()
    return []
  endif

  if !exists( 'b:ycm_completing' )
    return []
  endif

  return py3eval( 'ycm_state.GetDefinedSubcommands()' )
endfunction


function! youcompleteme#OpenGoToList()
  py3 vimsupport.PostVimMessage(
        \ "'WARNING: youcompleteme#OpenGoToList function is deprecated. " .
        \ "Do NOT use it.'" )
  py3 vimsupport.OpenQuickFixList( True, True )
endfunction


function! s:ShowDiagnostics()
  py3 ycm_state.ShowDiagnostics()
endfunction


function! s:ShowDetailedDiagnostic()
  py3 ycm_state.ShowDetailedDiagnostic()
endfunction


function! s:ForceCompileAndDiagnostics()
  py3 ycm_state.ForceCompileAndDiagnostics()
endfunction


if exists( '*popup_atcursor' )
  function s:Hover()
    if !py3eval( 'ycm_state.NativeFiletypeCompletionUsable()' )
      " Cancel the autocommand if it happens to have been set
      call s:DisableAutoHover()
      return
    endif

    if !has_key( b:, 'ycm_hover' )
      let cmds = youcompleteme#GetDefinedSubcommands()
      if index( cmds, 'GetHover' ) >= 0
        let b:ycm_hover = {
              \ 'command': 'GetHover',
              \ 'syntax': 'markdown',
              \ }
      elseif index( cmds, 'GetDoc' ) >= 0
        let b:ycm_hover = {
              \ 'command': 'GetDoc',
              \ 'syntax': '',
              \ }
      elseif index( cmds, 'GetType' ) >= 0
        let b:ycm_hover = {
              \ 'command': 'GetType',
              \ 'syntax': &syntax,
              \ }
      else
        let b:ycm_hover = {}
      endif
    endif

    if empty( b:ycm_hover )
      return
    endif

    let response = youcompleteme#GetCommandResponse( b:ycm_hover.command )
    if response == ''
      return
    endif

    call popup_hide( s:cursorhold_popup )
    let s:cursorhold_popup = popup_atcursor(
          \   split( response, "\n" ),
          \   {
          \     'padding': [ 0, 1, 0, 1 ],
          \     'maxwidth': &columns,
          \     'moved': 'word',
          \     'close': 'button',
          \   }
          \ )
    call setbufvar( winbufnr( s:cursorhold_popup ),
                            \ '&syntax',
                            \ b:ycm_hover.syntax )
  endfunction

  function! s:ToggleHover()
    let pos = popup_getpos( s:cursorhold_popup )
    if !empty( pos ) && pos.visible
      call popup_hide( s:cursorhold_popup )
      let s:cursorhold_popup = -1

      " Diable the auto-trigger until the next cursor movement.
      call s:DisableAutoHover()
      augroup YCMHover
        autocmd! CursorMoved <buffer>
        autocmd CursorMoved <buffer> call s:EnableAutoHover()
      augroup END
    else
      call s:Hover()
    endif
  endfunction

  let s:enable_hover = 1
  nnoremap <silent> <plug>(YCMHover) :<C-u>call <SID>ToggleHover()<CR>
else
  " Don't break people's mappings if this feature is disabled, just do nothing.
  nnoremap <silent> <plug>(YCMHover) <Nop>
endif

" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
