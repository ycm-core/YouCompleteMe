class NvimYcmAsyncHelper(object):
    def __init__(self, vim):
      self.vim = vim
      self.script_context = vim.script_context
      self.ycm_state = None


    def on_ycm_setup(self, none):
      self.ycm_state = self.script_context.ycm_state


    def on_ycm_teardown(self, none):
      self.ycm_state.OnVimLeave()


    def on_ycmd_response_ready( self, request ):
      request_data = request.request_data
      response_data = request.Response()

      if 'file_data' in request_data:
        # Avoid sending big files back to nvim
        del request_data[ 'file_data' ]

      if getattr( request, '_event_name', None ) == 'FileReadyToParse':
        self.on_end_compilation( request_data, response_data )


    def on_buffer_visit( self, request_data ):
      self.ycm_state.OnBufferVisit( request_data )


    def on_buffer_unload( self, filepath ):
      self.ycm_state.OnBufferUnload( filepath )


    def on_begin_compilation( self, request_data ):
      self.ycm_state.OnFileReadyToParse( request_data )

    
    def on_end_compilation( self, request_data, response_data ):
      self.ycm_state.UpdateDiagnosticInterface()


