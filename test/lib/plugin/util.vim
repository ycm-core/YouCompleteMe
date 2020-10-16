function! CheckCurrentLine( expected_value )
  return assert_equal( a:expected_value, getline( '.' ) )
endfunction

