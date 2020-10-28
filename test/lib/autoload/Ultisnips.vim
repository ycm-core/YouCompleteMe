let s:first_run = 1
function! UltiSnips#SnippetsInCurrentScope( num )
  if s:first_run == 1
    let g:current_ulti_dict_info = [ { 'foo': { 'description': 'first' } } ]
  else
    s:first_run = 0
    let g:current_ulti_dict_info = [ { 'foo2': { 'description': 'second' } } ]
  endif
endfunction
