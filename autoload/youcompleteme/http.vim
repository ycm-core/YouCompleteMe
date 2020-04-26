" Copyright (C) 2020 YouCompleteMe contributors
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

function! youcompleteme#http#GET( host, port, uri, query_string, headers )
  let uri = a:uri
  if a:query_string != ''
    let uri .= '?' . a:query_string
  endif
  return s:Write( 'GET', a:host, a:port, uri, a:headers, v:none )
endfunction

function! youcompleteme#http#POST( host, port, uri, headers, data )
  return s:Write( 'POST', a:host, a:port, a:uri, a:headers, a:data )
endfunction

" Blocking reads are a little tricky, as we normaly handle the data when the
" socket closes. We therefore block while the channel is open and manually
" invoke the Close callback. Of course that requires us to unset the usual close
" callback on the channel, as this is raised, _after_ this function returns.
function! youcompleteme#http#Block( id, timeout )
  let ch = s:request_state[ a:id ].handle
  call ch_setoptions( ch, { 'close_cb': '' } )
  while count( [ 'open', 'buffered' ],  ch_status( ch ) ) == 1
    let data = ch_read( ch, { 'timeout': a:timeout } )
    let s:request_state[ a:id ].data .= data
  endwhile
  call s:OnClose( ch )
endfunction

let s:request_state = {}
let s:CRLF = "\r\n"

function! s:OnData( channel, msg )
  let id =  ch_info( a:channel ).id
  let s:request_state[ id ].data .= a:msg
endfunction

function! s:OnClose( channel )
  let id = ch_info( a:channel ).id
  let data = s:request_state[ id ].data
  unlet s:request_state[ id ]
  let bounary = match( data, s:CRLF . s:CRLF )
  if bounary < 0
    call s:Reject( id, "Invalid message received" )
    return
  endif

  let header = data[ 0:(bounary - 1) ]
  let body = data[ bounary + 2*len( s:CRLF ): ]

  let headers = split( header, s:CRLF )
  let status_line = headers[ 0 ]
  let headers = headers[ 1: ]

  let header_map = {}
  for header in headers
    let colon = match( header, ':' )
    let header_map[ tolower( header[ : colon-1 ] ) ]
          \ = trim( header[ colon+1: ] )
  endfor

  let status_code = split( status_line )[ 1 ]

  call s:Resolve( id, status_code, header_map, body )
endfunction

function! s:Reject( id, why )
  py3 << EOF
from ycm.client import base_request
base_request.Future.requests.pop( vim.eval( 'a:id' ) ).reject(
  vim.eval( 'a:why' ) )
EOF
endfunction

function! s:Resolve( id, status_code, header_map, body )
  py3 << EOF
from ycm.client import base_request
base_request.Future.requests.pop( vim.eval( 'a:id' ) ).resolve(
  int( vim.eval( 'a:status_code' ) ),
  vim.eval( 'a:header_map' ),
  vim.eval( 'a:body' ) )
EOF
endfunction

function! s:Write( method, host, port, uri, headers, data )
  let ch = ch_open( a:host . ':' . a:port, #{
        \ mode: 'raw',
        \ callback: funcref( 's:OnData' ),
        \ close_cb: funcref( 's:OnClose' ),
        \ waittime: 100,
        \ } )

  if ch_status( ch ) != 'open'
    return v:none
  endif

  let id = ch_info( ch ).id
  let s:request_state[ id ] = #{ data: '', handle: ch }

  let a:headers[ 'Host' ] = a:host
  let a:headers[ 'Connection' ] = 'close'
  let a:headers[ 'Accept' ] = 'application/json'
  if a:data != v:none
    let a:headers[ 'Content-Length' ] = string( len( a:data ) )
  endif

  let msg = a:method . ' '. a:uri . ' HTTP/1.1' . s:CRLF
  for h in keys( a:headers )
    let msg .= h . ':' . a:headers[ h ] . s:CRLF
  endfor
  let msg .= s:CRLF
  if a:data != v:none
    let msg .= a:data
  endif
  call ch_sendraw( ch, msg )
  return id
endfunction

" This is basic vim plugin boilerplate
let &cpo = s:save_cpo
unlet s:save_cpo

" vim: filetype=vim.python foldmethod=marker
