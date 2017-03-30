def FlagsForFile( filename, **kwargs ):
  temp_dir = kwargs[ 'client_data' ][ 'tempname()' ]

  return {
    'flags': [ temp_dir ],
    'do_cache': False
  }
