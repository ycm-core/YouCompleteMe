def FlagsForFile( filename, **kwargs ):
  return {
    'flags': kwargs['client_data']['flags'],
    'do_cache': True
  }
