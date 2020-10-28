let s:first_run = 1

function! UltiSnips#DisableSnippetsInCurrentScope()
  delfunction UltiSnips#SnippetsInCurrentScope
  unlet g:current_ulti_dict_info
endfunctio

function! UltiSnips#EnableSnippetsInCurrentScope()
  function! UltiSnips#SnippetsInCurrentScope( num )
    if s:first_run == 1
      let g:current_ulti_dict_info = { 'foo': { 'description': 'first' } }
      let s:first_run = 0
    else
      let g:current_ulti_dict_info = { 'foo2': { 'description': 'second' } }
    endif
  endfunction
endfunction
