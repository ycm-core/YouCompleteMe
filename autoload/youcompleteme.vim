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
let s:old_cursor_text = ''
let g:ycm_min_num_of_chars_for_completion = 2

" Set up the plugin, load all our modules, bind our keys etc.
function! youcompleteme#Enable()

  augroup youcompleteme
    autocmd!
    autocmd CursorMovedI * call s:OnMovedI()
    autocmd BufRead,BufEnter * call s:SetCompleteFunc()
    autocmd CursorHold,CursorHoldI * py csystem.AddBufferIdentifiers()
  augroup END

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

  " We need this in spite of binding SetCompleteFunc to bufread and bufenter
  " because neither event is called when vim is started and the cursor is placed
  " in the file that was previously open (with for instance the session.vim
  " plugin)
  call s:SetCompleteFunc()

  " With this command, when the completion window is visible, the tab key will
  " select the next candidate in the window. In vim, this also changes the
  " typed-in text to that of the candidate completion.
  inoremap <expr><TAB>  pumvisible() ? "\<C-n>" : "\<TAB>"

  py import vim
  exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../python"]'
  py import ycm
  py csystem = ycm.CompletionSystem()
endfunction


function! s:SetCompleteFunc()
  let &completefunc = 'youcompleteme#Complete'
  let &l:completefunc = 'youcompleteme#Complete'
endfunction


function! s:OnMovedI()
  " Technically, what we are doing here is not thread-safe. We are adding a new
  " identifier to the database while a background thread may be going through
  " that db, searching for matches for the previous query. BUT, we don't care
  " what junk that thread may get; those results don't matter anymore since
  " right after this function is called, we start a new candidate search with a
  " new query, and the old one is thrown away. The background thread never
  " modifies the db, only reads it.
  call s:AddIdentifierIfNeeded()
  call s:InvokeCompletion()
endfunction


function! s:AddIdentifierIfNeeded()
  py vim.command( "let should_add_identifier = '" +
        \ str( ycm.ShouldAddIdentifier() ) + "'" )
  if should_add_identifier != 1
    return
  endif
  py csystem.AddPreviousIdentifier()
endfunction


function! s:InvokeCompletion()
  if &completefunc != "youcompleteme#Complete"
    return
  endif

  py vim.command( "let cursor_text = '" + ycm.CurrentCursorTextVim() + "'" )

  " infinite loops are bad, mkay?
  if cursor_text == '' || cursor_text == s:old_cursor_text
    return
  endif

  " <c-x><c-u> invokes the user's completion function (which we have set to
  " youcompleteme#Complete), and <c-p> tells vim to select the previous
  " completion candidate. This is necessary because by default, vim selects the
  " first candidate when completion is invoked, and selecting a candidate
  " automatically replaces the current text with it. Calling <c-p> forces vim to
  " deselect the first candidate and in turn preserve the user's current text
  " until he explicitly chooses to replace it with a completion.
  call feedkeys( "\<C-X>\<C-U>\<C-P>", 'n' )
endfunction


" This is our main entry point. This is what vim calls to get completions.
function! youcompleteme#Complete(findstart, base)
  if a:findstart
    py vim.command( 'let start_column = ' + str(
                   \ ycm.CompletionStartColumn() ) )
    return start_column
  else
    let s:old_cursor_text = a:base
    if strlen( a:base ) < g:ycm_min_num_of_chars_for_completion
      return []
    endif

	  py csystem.CandidatesForQueryAsync( vim.eval('a:base') )

		let l:results_ready = 0
		while !l:results_ready
      py << EOF
results_ready = csystem.AsyncCandidateRequestReady()
if results_ready:
  vim.command( 'let l:results_ready = 1' )
EOF
			if complete_check()
				return { 'words' : [], 'refresh' : 'always'}
			endif
		endwhile

    let l:results = []
    py << EOF
results = csystem.CandidatesFromStoredRequest()
if results:
  vim.command( 'let l:results = ' + str( results ) )
EOF
    " We need a very recent version of vim for this to work; otherwise, even
    " when we set refresh = always, vim won't call our completefunc on every
    " keystroke. The problem is still present in vim 7.3.390 but is fixed in
    " 7.3.475. It's possible that patch 404 was the one that fixed this issue,
    " but I haven't tested this assumption.
    " A bug in vim causes the '.' register to break when we use set this... sigh
		return { 'words' : l:results, 'refresh' : 'always'}
  endif
endfunction

" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
