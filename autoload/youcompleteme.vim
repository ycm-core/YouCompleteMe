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
let s:searched_and_no_results_found = 0
let s:should_use_clang = 0
let s:completion_start_column = 0
let g:ycm_min_num_of_chars_for_completion = 2

function! youcompleteme#Enable()
  augroup youcompleteme
    autocmd!
    autocmd CursorMovedI * call s:OnMovedI()
    " Note that these events will NOT trigger for the file vim is started with;
    " so if you do "vim foo.cc", these events will not trigger when that buffer
    " is read. This is because youcompleteme#Enable() is called on VimEnter and
    " that happens *after" BufRead/BufEnter has already triggered for the
    " initial file.
    autocmd BufRead,BufEnter * call s:OnBufferVisit()
    autocmd CursorHold,CursorHoldI * call s:OnCursorHold()
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

  " With this command, when the completion window is visible, the tab key will
  " select the next candidate in the window. In vim, this also changes the
  " typed-in text to that of the candidate completion.
  inoremap <expr><TAB>  pumvisible() ? "\<C-n>" : "\<TAB>"

  py import vim
  exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../python"]'
  py import ycm
  py identcomp = ycm.IdentifierCompleter()

  if g:ycm_clang_completion_enabled
    py clangcomp = ycm.ClangCompleter()
  endif

  " Calling this once solves the problem of BufRead/BufEnter not triggering for
  " the first loaded file. This should be the last command executed in this
  " function!
  call s:OnBufferVisit()
endfunction


function! s:OnBufferVisit()
  call s:SetCompleteFunc()
  py identcomp.OnFileEnter()

  if pyeval('ycm.ClangAvailableForFile()')
    py clangcomp.OnFileEnter()
  endif
endfunction


function! s:OnCursorHold()
  " TODO: make this async, it's causing lag
  py identcomp.AddBufferIdentifiers()
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
  if pyeval( 'ycm.ShouldAddIdentifier()' )
    py identcomp.AddPreviousIdentifier()
  endif
endfunction


function! s:InsideCommentOrString()
  " Has to be col('.') -1 because col('.') doesn't exist at this point. We are
  " in insert mode when this func is called.
  let syntax_group = synIDattr( synID( line( '.' ), col( '.' ) - 1, 1 ), 'name')
  if stridx(syntax_group, 'Comment') > -1 || stridx(syntax_group, 'String') > -1
    return 1
  endif
  return 0
endfunction


function! s:InvokeCompletion()
  if &completefunc != "youcompleteme#Complete"
    return
  endif

  if s:InsideCommentOrString()
    return
  endif

  " This is tricky. First, having 'refresh' set to 'always' in the dictionary
  " that our completion function returns makes sure that our completion function
  " is called on every keystroke when the completion menu is showing
  " (pumvisible() == true). So there's no point in invoking the completion menu
  " with our feedkeys call then.
  " Secondly, when the sequence of characters the user typed produces no
  " results in our search an infinite loop can occur. The problem is that our
  " feedkeys call triggers the OnCursorMovedI event which we are tied to.
  " So we solve this with the searched_and_no_results_found script-scope
  " variable that prevents this infinite loop from starting.
  if pumvisible() || s:searched_and_no_results_found
    let s:searched_and_no_results_found = 0
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


function! s:IdentifierCompletion(query)
  if strlen( a:query ) < g:ycm_min_num_of_chars_for_completion
    return []
  endif

  py identcomp.CandidatesForQueryAsync( vim.eval( 'a:query' ) )

  let l:results_ready = 0
  while !l:results_ready
    let l:results_ready = pyeval( 'identcomp.AsyncCandidateRequestReady()' )
    if complete_check()
      return { 'words' : [], 'refresh' : 'always'}
    endif
  endwhile

  let l:results = pyeval( 'identcomp.CandidatesFromStoredRequest()' )
  let s:searched_and_no_results_found = len( l:results ) == 0
  return { 'words' : l:results, 'refresh' : 'always' }
endfunction


function! s:ClangCompletion( query )
  " TODO: don't trigger on a dot inside a string constant
  py clangcomp.CandidatesForQueryAsync( vim.eval( 'a:query' ) )

  let l:results_ready = 0
  while !l:results_ready
    let l:results_ready = pyeval( 'clangcomp.AsyncCandidateRequestReady()' )
    if complete_check()
      return { 'words' : [], 'refresh' : 'always'}
    endif
  endwhile

  let l:results = pyeval( 'clangcomp.CandidatesFromStoredRequest()' )
  let s:searched_and_no_results_found = len( l:results ) == 0
  return { 'words' : l:results, 'refresh' : 'always' }
endfunction


" This is our main entry point. This is what vim calls to get completions.
function! youcompleteme#Complete( findstart, base )
  if a:findstart
    let s:completion_start_column = pyeval( 'ycm.CompletionStartColumn()' )
    let s:should_use_clang =
          \ pyeval( 'ycm.ShouldUseClang(' . s:completion_start_column . ')' )

    if ( s:should_use_clang )
      return s:completion_start_column
    else
      let l:current_column = col('.') - 1
      let l:query_length = current_column - s:completion_start_column

      if ( query_length < g:ycm_min_num_of_chars_for_completion )
        " for vim, -2 means not found but don't trigger an error message
        " see :h complete-functions
        return -2
      endif
      return s:completion_start_column
    endif
  else
    if ( s:should_use_clang )
      return s:ClangCompletion( a:base )
    else
      return s:IdentifierCompletion( a:base )
    endif
  endif
endfunction

" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo
