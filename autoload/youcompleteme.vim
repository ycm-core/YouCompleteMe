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
let s:moved_vertically_in_insert_mode = 0
let s:previous_num_chars_on_current_line = -1

let s:diagnostic_ui_filetypes = {
      \ 'cpp': 1,
      \ 'cs': 1,
      \ 'c': 1,
      \ 'objc': 1,
      \ 'objcpp': 1,
      \ }


function! youcompleteme#Enable()
  " When vim is in diff mode, don't run
  if &diff
    return
  endif

  call s:SetUpBackwardsCompatibility()

  if !s:SetUpPython()
    return
  endif

  call s:SetUpCpoptions()
  call s:SetUpCompleteopt()
  call s:SetUpKeyMappings()

  if g:ycm_show_diagnostics_ui
    call s:TurnOffSyntasticForCFamily()
  endif

  call s:SetUpSigns()
  call s:SetUpSyntaxHighlighting()

  if g:ycm_allow_changing_updatetime && &updatetime > 2000
    set ut=2000
  endif

  augroup youcompleteme
    autocmd!
    autocmd CursorMovedI * call s:OnCursorMovedInsertMode()
    autocmd CursorMoved * call s:OnCursorMovedNormalMode()
    " Note that these events will NOT trigger for the file vim is started with;
    " so if you do "vim foo.cc", these events will not trigger when that buffer
    " is read. This is because youcompleteme#Enable() is called on VimEnter and
    " that happens *after" BufRead/BufEnter has already triggered for the
    " initial file.
    " We also need to trigger buf init code on the FileType event because when
    " the user does :enew and then :set ft=something, we need to run buf init
    " code again.
    autocmd BufRead,BufEnter,FileType * call s:OnBufferVisit()
    autocmd BufUnload * call s:OnBufferUnload( expand( '<afile>:p' ) )
    autocmd CursorHold,CursorHoldI * call s:OnCursorHold()
    autocmd InsertLeave * call s:OnInsertLeave()
    autocmd InsertEnter * call s:OnInsertEnter()
    autocmd VimLeave * call s:OnVimLeave()
  augroup END

  " Calling this once solves the problem of BufRead/BufEnter not triggering for
  " the first loaded file. This should be the last command executed in this
  " function!
  call s:OnBufferVisit()
endfunction


function! s:SetUpPython()
  py import sys
  py import vim
  exe 'python sys.path.insert( 0, "' . s:script_folder_path . '/../python" )'
  exe 'python sys.path.insert( 0, "' . s:script_folder_path .
        \ '/../third_party/ycmd" )'
  py from ycmd import utils
  exe 'py utils.AddNearestThirdPartyFoldersToSysPath("'
        \ . s:script_folder_path . '")'

  " We need to import ycmd's third_party folders as well since we import and
  " use ycmd code in the client.
  py utils.AddNearestThirdPartyFoldersToSysPath( utils.__file__ )
  py from ycm import base
  py base.LoadJsonDefaultsIntoVim()
  py from ycmd import user_options_store
  py user_options_store.SetAll( base.BuildServerConf() )
  py from ycm import vimsupport

  if !pyeval( 'base.CompatibleWithYcmCore()')
    echohl WarningMsg |
      \ echomsg "YouCompleteMe unavailable: YCM support libs too old, PLEASE RECOMPILE" |
      \ echohl None
    return 0
  endif

  py from ycm.youcompleteme import YouCompleteMe
  py ycm_state = YouCompleteMe( user_options_store.GetAll() )
  return 1
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
    if invoke_key ==# '<C-Space>' && !has('gui_running')
      let invoke_key = '<Nul>'
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


function! s:DiagnosticUiSupportedForCurrentFiletype()
  return get( s:diagnostic_ui_filetypes, &filetype, 0 )
endfunction


function! s:AllowedToCompleteInCurrentFile()
  if empty( &filetype ) ||
        \ getbufvar( winbufnr( winnr() ), "&buftype" ) ==# 'nofile' ||
        \ &filetype ==# 'qf'
    return 0
  endif

  let whitelist_allows = has_key( g:ycm_filetype_whitelist, '*' ) ||
        \ has_key( g:ycm_filetype_whitelist, &filetype )
  let blacklist_allows = !has_key( g:ycm_filetype_blacklist, &filetype )

  return whitelist_allows && blacklist_allows
endfunction


function! s:SetUpCpoptions()
  " Without this flag in cpoptions, critical YCM mappings do not work. There's
  " no way to not have this and have YCM working, so force the flag.
  set cpoptions+=B

  " This prevents the display of "Pattern not found" & similar messages during
  " completion. This is only available since Vim 7.4.314
  if pyeval( 'vimsupport.VimVersionAtLeast("7.4.314")' )
    set shortmess+=c
  endif
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


" For various functions/use-cases, we want to keep track of whether the buffer
" has changed since the last time they were invoked. We keep the state of
" b:changedtick of the last time the specific function was called in
" b:ycm_changedtick.
function! s:SetUpYcmChangedTick()
  let b:ycm_changedtick  =
        \ get( b:, 'ycm_changedtick', {
        \   'file_ready_to_parse' : -1,
        \ } )
endfunction


function! s:OnVimLeave()
  py ycm_state.OnVimLeave()
endfunction


function! s:OnBufferVisit()
  " We need to do this even when we are not allowed to complete in the current
  " file because we might be allowed to complete in the future! The canonical
  " example is creating a new buffer with :enew and then setting a filetype.
  call s:SetUpYcmChangedTick()

  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  call s:SetUpCompleteopt()
  call s:SetCompleteFunc()
  py ycm_state.OnBufferVisit()
  call s:OnFileReadyToParse()
endfunction


function! s:OnBufferUnload( deleted_buffer_file )
  if !s:AllowedToCompleteInCurrentFile() || empty( a:deleted_buffer_file )
    return
  endif

  py ycm_state.OnBufferUnload( vim.eval( 'a:deleted_buffer_file' ) )
endfunction


function! s:OnCursorHold()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  call s:SetUpCompleteopt()
  call s:OnFileReadyToParse()
endfunction


function! s:OnFileReadyToParse()
  " We need to call this just in case there is no b:ycm_changetick; this can
  " happen for special buffers.
  call s:SetUpYcmChangedTick()

  " Order is important here; we need to extract any done diagnostics before
  " reparsing the file again. If we sent the new parse request first, then
  " the response would always be pending when we called
  " UpdateDiagnosticNotifications.
  call s:UpdateDiagnosticNotifications()

  let buffer_changed = b:changedtick != b:ycm_changedtick.file_ready_to_parse
  if buffer_changed
    py ycm_state.OnFileReadyToParse()
  endif
  let b:ycm_changedtick.file_ready_to_parse = b:changedtick
endfunction


function! s:SetCompleteFunc()
  let &completefunc = 'youcompleteme#Complete'
  let &l:completefunc = 'youcompleteme#Complete'

  if pyeval( 'ycm_state.NativeFiletypeCompletionUsable()' )
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

  py ycm_state.OnCursorMoved()
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

  if g:ycm_auto_trigger || s:omnifunc_mode
    call s:InvokeCompletion()
  endif

  " We have to make sure we correctly leave omnifunc mode even when the user
  " inserts something like a "operator[]" candidate string which fails
  " CurrentIdentifierFinished check.
  if s:omnifunc_mode && !pyeval( 'base.LastEnteredCharIsIdentifierChar()')
    let s:omnifunc_mode = 0
  endif
endfunction


function! s:OnCursorMovedNormalMode()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  call s:OnFileReadyToParse()
  py ycm_state.OnCursorMoved()
endfunction


function! s:OnInsertLeave()
  if !s:AllowedToCompleteInCurrentFile()
    return
  endif

  let s:omnifunc_mode = 0
  call s:OnFileReadyToParse()
  py ycm_state.OnInsertLeave()
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

  " This command does the actual closing of the preview window. If no preview
  " window is shown, nothing happens.
  pclose
endfunction


function! s:UpdateDiagnosticNotifications()
  let should_display_diagnostics = g:ycm_show_diagnostics_ui &&
        \ s:DiagnosticUiSupportedForCurrentFiletype() &&
        \ pyeval( 'ycm_state.NativeFiletypeCompletionUsable()' )

  if !should_display_diagnostics
    return
  endif

  py ycm_state.UpdateDiagnosticInterface()
endfunction


function! s:IdentifierFinishedOperations()
  if !pyeval( 'base.CurrentIdentifierFinished()' )
    return
  endif
  py ycm_state.OnCurrentIdentifierFinished()
  let s:omnifunc_mode = 0
endfunction


" Returns 1 when inside comment and 2 when inside string
function! s:InsideCommentOrString()
  " Has to be col('.') -1 because col('.') doesn't exist at this point. We are
  " in insert mode when this func is called.
  let syntax_group = synIDattr( synIDtrans( synID( line( '.' ), col( '.' ) - 1, 1 ) ), 'name')

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
  return pyeval( 'not vim.current.line or vim.current.line.isspace()' )
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


python << EOF
def GetCompletionsInner():
  request = ycm_state.GetCurrentCompletionRequest()
  request.Start()
  while not request.Done():
    if bool( int( vim.eval( 'complete_check()' ) ) ):
      return { 'words' : [], 'refresh' : 'always'}

  results = base.AdjustCandidateInsertionText( request.Response() )
  return { 'words' : results, 'refresh' : 'always' }
EOF


function! s:GetCompletions()
  py results = GetCompletionsInner()
  let results = pyeval( 'results' )
  return results
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

    if !pyeval( 'ycm_state.IsServerAlive()' )
      return -2
    endif
    py ycm_state.CreateCompletionRequest()
    return pyeval( 'base.CompletionStartColumn()' )
  else
    return s:GetCompletions()
  endif
endfunction


function! youcompleteme#OmniComplete( findstart, base )
  if a:findstart
    if !pyeval( 'ycm_state.IsServerAlive()' )
      return -2
    endif
    let s:omnifunc_mode = 1
    py ycm_state.CreateCompletionRequest( force_semantic = True )
    return pyeval( 'base.CompletionStartColumn()' )
  else
    return s:GetCompletions()
  endif
endfunction


function! youcompleteme#ServerPid()
  return pyeval( 'ycm_state.ServerPid()' )
endfunction


function! s:RestartServer()
  py ycm_state.RestartServer()
endfunction

command! YcmRestartServer call s:RestartServer()


function! s:ShowDetailedDiagnostic()
  py ycm_state.ShowDetailedDiagnostic()
endfunction

command! YcmShowDetailedDiagnostic call s:ShowDetailedDiagnostic()


function! s:DebugInfo()
  echom "Printing YouCompleteMe debug information..."
  let debug_info = pyeval( 'ycm_state.DebugInfo()' )
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

  py ycm_state.SendCommandRequest( vim.eval( 'l:arguments' ),
        \                          vim.eval( 'l:completer' ) )
endfunction


function! youcompleteme#OpenGoToList()
  set lazyredraw
  cclose
  execute 'belowright copen 3'
  set nolazyredraw
  au WinLeave <buffer> q  " automatically leave, if an option is chosen
  redraw!
endfunction


command! -nargs=* -complete=custom,youcompleteme#SubCommandsComplete
  \ YcmCompleter call s:CompleterCommand(<f-args>)

function! youcompleteme#SubCommandsComplete( arglead, cmdline, cursorpos )
  return join( pyeval( 'ycm_state.GetDefinedSubcommands()' ),
    \ "\n")
endfunction


function! s:ForceCompile()
  if !pyeval( 'ycm_state.NativeFiletypeCompletionUsable()' )
    echom "Native filetype completion not supported for current file, "
          \ . "cannot force recompilation."
    return 0
  endif

  echom "Forcing compilation, this will block Vim until done."
  py ycm_state.OnFileReadyToParse()
  while 1
    let diagnostics_ready = pyeval(
          \ 'ycm_state.DiagnosticsForCurrentFileReady()' )
    if diagnostics_ready
      break
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

  let diags = pyeval(
        \ 'ycm_state.GetDiagnosticsFromStoredRequest( qflist_format = True )' )
  if !empty( diags )
    call setloclist( 0, diags )

    if g:ycm_open_loclist_on_ycm_diags
      lopen
    endif
  else
    echom "No warnings or errors detected"
  endif
endfunction

command! YcmDiags call s:ShowDiagnostics()


" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
