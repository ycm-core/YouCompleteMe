from json import dumps

class NvimYcmAsyncHelper(object):
    def __init__( self, vim ):
      self.vim = vim
      self.script_context = vim.script_context
      self.ycm_state = None


    def on_ycm_setup( self, none ):
      self.ycm_state = self.script_context.ycm_state
      self.base = self.script_context.base


    def on_plugin_teardown( self ):
      self.ycm_state.OnVimLeave()


    def on_ycmd_response_ready( self, request ):
      request_data = request.request_data
      response_data = request.Response()

      if 'file_data' in request_data:
        # Avoid sending big files back to nvim
        del request_data[ 'file_data' ]

      if hasattr( request, '_event_name' ):
        if request._event_name == 'FileReadyToParse':
          self.ycm_state.UpdateDiagnosticInterface()
      else:
        # Completion response
        results = self.base.AdjustCandidateInsertionText( response_data )
        args = dumps( [ request_data, results ] )[ 1 : -1 ]
        self.vim.eval( 'youcompleteme#EndCompletion({0})'.format( args ) )


    def on_buffer_visit( self, request_data ):
      self.ycm_state.OnBufferVisit( request_data )


    def on_buffer_unload( self, filepath ):
      self.ycm_state.OnBufferUnload( filepath )


    def on_begin_compilation( self, request_data ):
      self.ycm_state.OnFileReadyToParse( request_data )

    
    def on_begin_completion( self, request_data ):
      vim = self.vim
      self.ycm_state.CreateCompletionRequest( request_data = request_data )
      self.ycm_state._latest_completion_request.Start()
