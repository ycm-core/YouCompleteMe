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

" This needs to be called outside of a function
let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
let s:searched_and_results_found = 0
let s:should_use_filetype_completion = 0
let s:completion_start_column = 0
let s:omnifunc_mode = 0

let s:old_cursor_position = []
let s:cursor_moved = 0
let s:moved_vertically_in_insert_mode = 0
let s:previous_num_chars_on_current_line = -1

function! youcompleteme#Enable()
  " When vim is in diff mode, don't run
  if &diff
    return
  endif

  py3 import sys
  py3 import vim
  exe 'python3 sys.path.insert( 0, "' . s:script_folder_path . '/../python" )'
  py3 import ycm

  if !py3eval( 'ycm.CompatibleWithYcmCore()')
    echohl WarningMsg |
      \ echomsg "YouCompleteMe unavailable: ycm_core too old, PLEASE RECOMPILE ycm_core" |
      \ echohl None
    return
  endif

  py3 ycm_state = ycm.YouCompleteMe()

  augroup youcompleteme
    autocmd!
    autocmd CursorMovedI * call s:OnCursorMovedInsertMode()
    autocmd CursorMoved * call s:OnCursorMovedNormalMode()
    " Note that these events will NOT trigger for the file vim is started with;
    " so if you do "vim foo.cc", these events will not trigger when that buffer
    " is read. This is because youcompleteme#Enable() is called on VimEnter and
    " that happens *after" BufRead/BufEnter has already triggered for the
    " initial file.
    autocmd BufRead,BufEnter * call s:OnBufferVisit()
    autocmd BufDelete * call s:OnBufferDelete( expand( '<afile>:p' ) )
    autocmd CursorHold,CursorHoldI * call s:OnCursorHold()
    autocmd InsertLeave * call s:OnInsertLeave()
    autocmd InsertEnter * call s:OnInsertEnter()
  augroup END

  call s:SetUpCompleteopt()
  call s:SetUpKeyMappings()

  if g:ycm_register_as_syntastic_checker
    call s:ForceSyntasticCFamilyChecker()
  endif

  if g:ycm_allow_changing_updatetime
    set ut=2000
  endif

  " Calling this once solves the problem of BufRead/BufEnter not triggering for
  " the first loaded file. This should be the last command executed in this
  " function!
  call s:OnBufferVisit()
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
    " <c-x><c-o> trigger omni completion, <c-p> deselects the first completion
    " candidate that vim selects by default
    silent! exe 'inoremap <unique> ' . g:ycm_key_invoke_completion .
          \ ' <C-X><C-O><C-P>'
  endif

  if !empty( g:ycm_key_detailed_diagnostics )
    silent! exe 'nnoremap <unique> ' . g:ycm_key_detailed_diagnostics .
          \ ' :YcmShowDetailedDiagnostic<cr>'
  endif
endfunction


function! s:ForceSyntasticCFamilyChecker()
  " Needed so that YCM is used as the syntastic checker
  let g:syntastic_cpp_checkers = ['ycm']
  let g:syntastic_c_checkers = ['ycm']
  let g:syntastic_objc_checkers = ['ycm']
  let g:syntastic_objcpp_checkers = ['ycm']
endfunction


function! s:AllowedToCompleteInCurrentFile()
  if empty( &filetype )
    return 0
  endif

  let whitelist_allows = has_key( g:ycm_filetype_whitelist, '*' ) ||
        \ has_key( g:ycm_filetype_whitelist, &filetype )
  let blacklist_allows = !has_key( g:ycm_filetype_blacklist, &filetype )

  return whitelist_allows && blacklist_allows
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


function! s:OnBufferVisit()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  call s:SetUpCompleteopt()
  call s:SetCompleteFunc()
  call s:OnFileReadyToParse()
endfunction


function! s:OnBufferDelete( deleted_buffer_file )
  if !s:AllowedToCompleteInCurrentFile() || empty( a:deleted_buffer_file )
    return
  endif

  py3 ycm_state.OnBufferDelete( vim.eval( 'a:deleted_buffer_file' ) )
endfunction


function! s:OnCursorHold()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  call s:SetUpCompleteopt()
  " Order is important here; we need to extract any done diagnostics before
  " reparsing the file again
  call s:UpdateDiagnosticNotifications()
  call s:OnFileReadyToParse()
endfunction


function! s:OnFileReadyToParse()
  py3 ycm_state.OnFileReadyToParse()
endfunction


function! s:SetCompleteFunc()
  let &completefunc = 'youcompleteme#Complete'
  let &l:completefunc = 'youcompleteme#Complete'

  if py3eval( 'ycm_state.NativeFiletypeCompletionUsable()' )
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


function! s:OnCursorMovedInsertMode()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  call s:UpdateCursorMoved()

  " Basically, we need to only trigger the completion menu when the user has
  " inserted or deleted a character, NOT just when the user moves in insert mode
  " (with, say, the arrow keys). If we trigger the menu even on pure moves, then
  " it's impossible to move in insert mode since the up/down arrows start moving
  " the selected completion in the completion menu. Yeah, people shouldn't be
  " moving in insert mode at all (that's what normal mode is for) but explain
  " that to the users who complain...
  if !s:BufferTextChangedSinceLastMoveInInsertMode()
    return
  endif

  call s:IdentifierFinishedOperations()
  if g:ycm_autoclose_preview_window_after_completion
    call s:ClosePreviewWindowIfNeeded()
  endif
  call s:InvokeCompletion()
endfunction


function! s:OnCursorMovedNormalMode()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  call s:UpdateDiagnosticNotifications()
endfunction


function! s:OnInsertLeave()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  let s:omnifunc_mode = 0
  call s:UpdateDiagnosticNotifications()
  py3 ycm_state.OnInsertLeave()
  if g:ycm_autoclose_preview_window_after_completion ||
        \ g:ycm_autoclose_preview_window_after_insertion
    call s:ClosePreviewWindowIfNeeded()
  endif
endfunction


function! s:OnInsertEnter()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  let s:old_cursor_position = []
endfunction


function! s:UpdateCursorMoved()
  let current_position = getpos('.')
  let s:cursor_moved = current_position != s:old_cursor_position

  let s:moved_vertically_in_insert_mode = s:old_cursor_position != [] &&
        \ current_position[ 1 ] != s:old_cursor_position[ 1 ]

  let s:old_cursor_position = current_position
endfunction


function! s:BufferTextChangedSinceLastMoveInInsertMode()
  if s:moved_vertically_in_insert_mode
    let s:previous_num_chars_on_current_line = -1
    return 0
  endif

  let num_chars_in_current_cursor_line = strlen( getline('.') )

  if s:previous_num_chars_on_current_line == -1
    let s:previous_num_chars_on_current_line = num_chars_in_current_cursor_line
    return 0
  endif

  let changed_text_on_current_line = num_chars_in_current_cursor_line !=
        \ s:previous_num_chars_on_current_line
  let s:previous_num_chars_on_current_line = num_chars_in_current_cursor_line

  return changed_text_on_current_line
endfunction


function! s:ClosePreviewWindowIfNeeded()
  let current_buffer_name = bufname('')

  " We don't want to try to close the preview window in special buffers like
  " "[Command Line]"; if we do, Vim goes bonkers. Special buffers always start
  " with '['.
  if current_buffer_name[ 0 ] == '['
    return
  endif

  if s:searched_and_results_found
    " This command does the actual closing of the preview window. If no preview
    " window is shown, nothing happens.
    pclose
  endif
endfunction


function! s:UpdateDiagnosticNotifications()
  if get( g:, 'loaded_syntastic_plugin', 0 ) &&
        \ py3eval( 'ycm_state.NativeFiletypeCompletionUsable()' ) &&
        \ py3eval( 'ycm_state.DiagnosticsForCurrentFileReady()' )
    SyntasticCheck
  endif
endfunction


function! s:IdentifierFinishedOperations()
  if !py3eval( 'ycm.CurrentIdentifierFinished()' )
    return
  endif
  py3 ycm_state.OnCurrentIdentifierFinished()
  let s:omnifunc_mode = 0
endfunction


function! s:InsideCommentOrString()
  if g:ycm_complete_in_comments_and_strings
    return 0
  endif

  " Has to be col('.') -1 because col('.') doesn't exist at this point. We are
  " in insert mode when this func is called.
  let syntax_group = synIDattr( synIDtrans( synID( line( '.' ), col( '.' ) - 1, 1 ) ), 'name')
  if stridx(syntax_group, 'Comment') > -1 || stridx(syntax_group, 'String') > -1
    return 1
  endif
  return 0
endfunction


function! s:OnBlankLine()
  return py3eval( 'not vim.current.line or vim.current.line.isspace()' )
endfunction


function! s:InvokeCompletion()
  if &completefunc != "youcompleteme#Complete"
    return
  endif

  if s:InsideCommentOrString() || s:OnBlankLine()
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


function! s:CompletionsForQuery( query, use_filetype_completer )
  if a:use_filetype_completer
    py3 completer = ycm_state.GetFiletypeCompleter()
  else
    py3 completer = ycm_state.GetIdentifierCompleter()
  endif

  " TODO: don't trigger on a dot inside a string constant
  py3 completer.CandidatesForQueryAsync( vim.eval( 'a:query' ) )

  let l:results_ready = 0
  while !l:results_ready
    let l:results_ready = py3eval( 'completer.AsyncCandidateRequestReady()' )
    if complete_check()
      let s:searched_and_results_found = 0
      return { 'words' : [], 'refresh' : 'always'}
    endif
  endwhile

  let l:results = py3eval( 'completer.CandidatesFromStoredRequest()' )
  let s:searched_and_results_found = len( l:results ) != 0
  return { 'words' : l:results, 'refresh' : 'always' }
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


    " TODO: make this a function-local variable instead of a script-local one
    let s:completion_start_column = py3eval( 'ycm.CompletionStartColumn()' )
    let s:should_use_filetype_completion =
          \ py3eval( 'ycm_state.ShouldUseFiletypeCompleter(' .
          \ s:completion_start_column . ')' )

    if !s:should_use_filetype_completion &&
          \ !py3eval( 'ycm_state.ShouldUseIdentifierCompleter(' .
          \ s:completion_start_column . ')' )
      " for vim, -2 means not found but don't trigger an error message
      " see :h complete-functions
      return -2
    endif
    return s:completion_start_column
  else
    return s:CompletionsForQuery( a:base, s:should_use_filetype_completion )
  endif
endfunction


function! youcompleteme#OmniComplete( findstart, base )
  if a:findstart
    let s:omnifunc_mode = 1
    let s:completion_start_column = py3eval( 'ycm.CompletionStartColumn()' )
    return s:completion_start_column
  else
    return s:CompletionsForQuery( a:base, 1 )
  endif
endfunction


function! s:ShowDetailedDiagnostic()
  py3 ycm_state.ShowDetailedDiagnostic()
endfunction

command! YcmShowDetailedDiagnostic call s:ShowDetailedDiagnostic()


" This is what Syntastic calls indirectly when it decides an auto-check is
" required (currently that's on buffer save) OR when the SyntasticCheck command
" is invoked
function! youcompleteme#CurrentFileDiagnostics()
  return py3eval( 'ycm_state.GetDiagnosticsForCurrentFile()' )
endfunction


function! s:DebugInfo()
  echom "Printing YouCompleteMe debug information..."
  let debug_info = py3eval( 'ycm_state.DebugInfo()' )
  for line in split( debug_info, "\n" )
    echom '-- ' . line
  endfor
endfunction

command! YcmDebugInfo call s:DebugInfo()

function! s:CompleterCommand(...)
  " CompleterCommand will call the OnUserCommand function of a completer.
  " If the first arguments is of the form "ft=..." it can be used to specify the
  " completer to use (for example "ft=cpp").  Else the native filetype completer
  " of the current buffer is used.  If no native filetype completer is found and
  " no completer was specified this throws an error.  You can use "ft=ycm:omni"
  " to select the omni completer or "ft=ycm:ident" to select the identifier
  " completer.  The remaining arguments will passed to the completer.
  let arguments = copy(a:000)

  if a:0 > 0 && strpart(a:1, 0, 3) == 'ft='
    if a:1 == 'ft=ycm:omni'
      py3 completer = ycm_state.GetOmniCompleter()
    elseif a:1 == 'ft=ycm:ident'
      py3 completer = ycm_state.GetIdentifierCompleter()
    else
      py3 completer = ycm_state.GetFiletypeCompleterForFiletype(
                   \ vim.eval('a:1').lstrip('ft=') )
    endif
    let arguments = arguments[1:]
  elseif py3eval( 'ycm_state.NativeFiletypeCompletionAvailable()' )
    py3 completer = ycm_state.GetFiletypeCompleter()
  else
    echohl WarningMsg |
      \ echomsg "No native completer found for current buffer." |
      \ echomsg  "Use ft=... as the first argument to specify a completer." |
      \ echohl None
    return
  endif

  py3 completer.OnUserCommand( vim.eval( 'l:arguments' ) )
endfunction

command! -nargs=* YcmCompleter call s:CompleterCommand(<f-args>)

function! s:ForceCompile()
  if !py3eval( 'ycm_state.NativeFiletypeCompletionUsable()' )
    echom "Native filetype completion not supported for current file, "
          \ . "cannot force recompilation."
    return 0
  endif

  echom "Forcing compilation, this will block Vim until done."
  py3 ycm_state.OnFileReadyToParse()
  while 1
    let diagnostics_ready = py3eval(
          \ 'ycm_state.DiagnosticsForCurrentFileReady()' )
    if diagnostics_ready
      break
    endif

    let getting_completions = py3eval(
          \ 'ycm_state.GettingCompletions()' )

    if !getting_completions
      echom "Unable to retrieve diagnostics, see output of `:mes` for possible details."
      return 0
    endif

    sleep 100m
  endwhile
  return 1
endfunction


function! s:ForceCompileAndDiagnostics()
  let compilation_succeeded = s:ForceCompile()
  if !compilation_succeeded
    return
  endif

  call s:UpdateDiagnosticNotifications()
  echom "Diagnostics refreshed."
endfunction

command! YcmForceCompileAndDiagnostics call s:ForceCompileAndDiagnostics()


function! s:ShowDiagnostics()
  let compilation_succeeded = s:ForceCompile()
  if !compilation_succeeded
    return
  endif

  let diags = py3eval( 'ycm_state.GetDiagnosticsForCurrentFile()' )
  if !empty( diags )
    call setloclist( 0, diags )
    lopen
  else
    echom "No warnings or errors detected"
  endif
endfunction

command! YcmDiags call s:ShowDiagnostics()


" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
