#!/usr/bin/env python

# Copyright (C) 2010-2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Suggestion Box - An example paging application.

A simple Suggestion Box application that demonstrates paging by using cursors
provided for queries.
"""

from google.appengine.ext import ndb
from google.appengine.ext.webapp.util import login_required
import webapp2

from base_handler import BaseHandler


PAGE_SIZE = 5


class SuggestionByCursor(ndb.Model):
  """Model for storing suggestions contributed to the application.

  Suggestions will be displayed in the order they were created.
  """
  suggestion = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)


class SuggestionByCursorHandler(BaseHandler):
  """
  Handles the creation of a single Suggestion, and the display
  of suggestions broken into PAGE_SIZE pages.
  """

  @login_required
  def get(self):
    cursor = None
    bookmark = self.request.get('bookmark')
    if bookmark:
      cursor = ndb.Cursor.from_websafe_string(bookmark)

    query = SuggestionByCursor.query().order(-SuggestionByCursor.created)
    suggestions, next_cursor, more = query.fetch_page(PAGE_SIZE,
                                                      start_cursor=cursor)

    next_bookmark = None
    if more:
      next_bookmark = next_cursor.to_websafe_string()

    self.render_response('suggestion.html', bookmark=next_bookmark,
                         suggestions=suggestions)

  def post(self):
    SuggestionByCursor(suggestion=self.request.get('suggestion')).put()
    self.redirect('/cursor/')


class SuggestionByCursorPopulate(BaseHandler):
  """
  Handles populating the datastore with some sample
  Suggestions to see how the paging works.
  """
  def post(self):
    suggestions = [SuggestionByCursor(suggestion='Suggestion {:d}'.format(i))
                   for i in range(6)]
    ndb.put_multi(suggestions)
    self.redirect('/cursor/')


APPLICATION = webapp2.WSGIApplication([
    ('/cursor/pop/', SuggestionByCursorPopulate),
    ('/cursor/', SuggestionByCursorHandler)],
    debug=True)
