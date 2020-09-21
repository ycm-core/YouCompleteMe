vim9script

const CRLF = "\r\n"
let request_state: dict< dict< any > > = {}


def Write( method: string,
           host: string,
           port: number,
           uri: string,
           headers: dict< any  >,
           data: string ): number

  let ch = ch_open( host .. ':' .. string( port ), #{
    mode: 'raw',
    callback: funcref( 's:OnData' ),
    close_cb: funcref( 's:OnClose' ),
    waittime: 100,
  } )

  if ch_status( ch ) != 'open'
    return 0
  endif

  let id = ch_info( ch ).id
  request_state[ id ] = #{ data: '', handle: ch }

  let all_headers = copy( headers )
  all_headers->extend( {
    'Host': host,
    'Connection': 'close',
    'Accept': 'application/json',
  } )

  if !empty( data )
    all_headers->extend( {
      'Content-Length': string( len( data ) )
    } )
  endif

  let msg = method .. ' ' .. uri .. ' HTTP/1.1' .. CRLF
  for h in keys( all_headers )
    msg ..= h .. ':' .. all_headers[h] .. CRLF
  endfor
  msg ..= s:CRLF
  msg ..= data
  call ch_sendraw( ch, msg )
  return id
enddef

def OnData( channel: channel, msg: string )
  let id = ch_info( channel ).id
  let data = request_state[id].data
  request_state[id]->extend( #{
    data: data .. msg
  } )
enddef

def OnClose( channel: channel )
  let id = ch_info( channel ).id
  let data = request_state[id].data
  remove( request_state, id )

  let boundary = match( data, CRLF .. CRLF )
  if boundary < 0
    Reject( id, "Invalid message received" )
    return
  endif

  let header_data = data->strpart( 0, boundary )
  let body = data->strpart( boundary + 2 * len( CRLF ) )

  let headers = split( header_data, CRLF )
  let status_line = headers[0]
  remove( headers, 0 )

  let header_map: dict< string > = {}
  for header in headers
    let colon = match( header, ':' )
    let key = header->strpart( 0, colon )
    let value = header->strpart( colon + 1 )
    header_map[ tolower( key ) ] = trim( value )
  endfor

  let status_code = split( status_line )[1]

  Resolve( id, status_code, header_map, body )
enddef

def Resolve( id: number,
             status_code: string,
             header_map: dict< string >,
             body: string )

  g:ycm_http9_vars->extend( #{
    id: id,
    status_code: status_code,
    header_map: header_map,
    body: body
  } )

  call ch_log( 'Resolve! ' .. string( g:ycm_http9_vars ) )

  py3 from ycm.client import base_request
  py3 base_request.Future.requests.pop(
        \ vim.eval( 'g:ycm_http9_vars.id' ) ).resolve(
          \ int( vim.eval( 'g:ycm_http9_vars.status_code' ) ),
          \ vim.eval( 'g:ycm_http9_vars.header_map' ),
          \ vim.eval( 'g:ycm_http9_vars.body' ) )
enddef

def Reject( id: number, why: string )
  g:ycm_http9_vars->extend( #{
    id: id,
    why: why
  } )

  py3 from ycm.client import base_request
  py3 base_request.Future.requests.pop(
        \ vim.eval( 'g:ycm_http9_vars.id' ) ).reject(
        \ vim.eval( 'g:ycm_http9_vars.why' ) )
enddef

def youcompleteme#http9#GET( host: string,
                             port: number,
                             uri: string,
                             query_string: string,
                             headers: dict< any  > ): number
  return Write( 'GET',
                host,
                port,
                empty( query_string ) ? uri : uri .. '?' .. query_string,
                headers,
                '' )
enddef


def youcompleteme#http9#POST( host: string,
                              port: number,
                              uri: string,
                              headers: dict< any >,
                              data: string ): number
  return Write( 'POST', host, port, uri, headers, data )
enddef

def youcompleteme#http9#Block( id: number, timeout: number )
  let ch = request_state[id].handle
  ch_setoptions( ch, { 'close_cb': '' } )
  while count( [ 'open', 'buffered' ],  ch_status( ch ) ) == 1
    let data  = ch_read( ch, { 'timeout': timeout } )
    OnData( ch, data )
  endwhile
  OnClose( ch )
enddef

defcompile
