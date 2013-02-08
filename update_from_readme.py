#!/usr/bin/env python

from bs4 import BeautifulSoup
from markdown import markdown
import fileinput

markdown_lines = list( fileinput.input() )

# We delete the first two lines because that's the big YCM heading which we
# already have on the page
del markdown_lines[:2]

markdown_source = ''.join( markdown_lines )

with open('index.html', 'r+') as content_file:
  content = content_file.read()
  soup = BeautifulSoup( content, "html5lib" )
  elem = soup.find( id="markdown-output" )

  new_contents = markdown( unicode( markdown_source, 'utf-8' ),
                           extensions=['fenced_code'] )
  new_tags = BeautifulSoup( new_contents, 'html5lib' )
  elem.clear()
  for new_elem in new_tags.body.contents:
    elem.append( new_elem )

  content_file.seek(0)
  content_file.truncate()
  # content_file.write( soup.prettify().encode( 'utf-8' ) )
  content_file.write( str( soup ) )

