function! CheckCurrentLine( expected_value )
  return assert_equal( a:expected_value, getline( '.' ) )
endfunction

function! AssertDictHasEntries( actual, expected, name = 'expected dict' )
  let l:errs = 0
  for key in keys( a:expected )
    if !has_key( a:actual, key )
      let l:errs += assert_report( 'Key '
                                 \ . key
                                 \ . ' of '
                                 \ . a:name
                                 \ . ' was not found' )
    elseif type( a:expected[ key ] ) == v:t_dict
      if type( a:actual[ key ] ) != v:t_dict
        let l:errs += assert_report( 'Key '
                                   \ . key
                                   \ . ' of '
                                   \ . a:name
                                   \ . ' was expected to be a dict, but was '
                                   \ . string( a:actual[ key ] ) )
      else
        let l:errs += AssertDictHasEntries( a:actual[ key ],
                                          \ a:expected[ key ],
                                          \ 'entry ' . key . ' in ' . a:name )
      endif
    else
      let l:errs += assert_equal( a:expected[ key ],
                                \ a:actual[ key ],
                                \ 'Key '
                                \ . key
                                \ . ' of '
                                \ . a:name
                                \ . ' did not match' )
    endif
  endfor
  return l:errs
endfunction

function! CheckListOfDicts( actual_list, expected_list )
  let l:errs = 0
  let l:idx = 0
  if len( a:actual_list ) != len( a:expected_list )
    let l:errs += assert_report( 'Expected list to contain '
                               \ . len( a:actual_list )
                               \ . ' entries, but found '
                               \ . len( a:expected_list )
                               \ . ': Expected '
                               \ . string( a:expected_list )
                               \ . ' but found '
                               \ . string( a:actual_list ) )
  endif

  while l:idx < len( a:expected_list )
    let l:expected = a:expected_list[ l:idx ]
    if l:idx >= len( a:actual_list )
      let l:errs += assert_report( 'The item at index '
                                 \ . l:idx
                                 \ . ' was not found: '
                                 \ . string( l:expected ) )
    else
      let l:actual = a:actual_list[ l:idx ]
      let l:errs += AssertDictHasEntries( l:actual,
                                        \ l:expected,
                                        \ 'item at index ' . l:idx )
    endif
    let l:idx = l:idx + 1
  endwhile

  while idx < len( a:actual_list )
    let l:actual = a:actual_list[ idx ]
    let l:errs +=  assert_report( 'The following additional property '
                                \ . 'was found: '
                                \ . string( l:actual ) )
    let l:idx = l:idx + 1
  endwhile

  return l:errs > 0 ? 1 : 0
endfunction
