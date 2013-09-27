#!/usr/bin/env python
#
# Copyright (C) 2013  Strahinja Val Markovic <val@markovic.io>
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.


# TODO: Move this file under server/ and rename it responses.py

def BuildGoToResponse( filepath, line_num, column_num, description = None ):
  response = {
    'filepath': filepath,
    'line_num': line_num,
    'column_num': column_num
  }

  if description:
    response[ 'description' ] = description
  return response


def BuildDescriptionOnlyGoToResponse( text ):
  return {
    'description': text,
  }


def BuildDisplayMessageResponse( text ):
  return {
    'message': text
  }


def BuildCompletionData( insertion_text,
                         extra_menu_info = None,
                         detailed_info = None,
                         menu_text = None,
                         kind = None ):
  completion_data = {
    'insertion_text': insertion_text
  }

  if extra_menu_info:
    completion_data[ 'extra_menu_info' ] = extra_menu_info
  if menu_text:
    completion_data[ 'menu_text' ] = menu_text
  if detailed_info:
    completion_data[ 'detailed_info' ] = detailed_info
  if kind:
    completion_data[ 'kind' ] = kind
  return completion_data


def BuildDiagnosticData( filepath,
                         line_num,
                         column_num,
                         text,
                         kind ):
  return {
    'filepath': filepath,
    'line_num': line_num,
    'column_num': column_num,
    'text': text,
    'kind': kind
  }


def BuildExceptionResponse( error_message, traceback ):
  return {
    'message': error_message,
    'traceback': traceback
  }

