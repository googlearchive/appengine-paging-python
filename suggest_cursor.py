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
import webapp2

from base_handler import BaseHandler


PAGE_SIZE = 5


class SuggestionByCursor(ndb.Model):
    """Model for storing suggestions contributed to the application.

    Suggestions will be displayed in the order they were created.
    """
    suggestion = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def populate(cls, num_values=PAGE_SIZE + 1):
        """Populates dummy suggestions for demonstration purposes.

        Args:
            num_values: Integer; defaults to PAGE_SIZE + 1. The number of dummy
                suggestions to add.
        """
        suggestions = [cls(suggestion='Suggestion {:d}'.format(i))
                       for i in range(num_values)]
        ndb.put_multi(suggestions)


class SuggestionByCursorHandler(BaseHandler):
    """Handles the insert of a suggestion and display of existing suggestions.

    The GET handler is intended for general display and paging and the POST
    handler is used for inserting new suggestions.
    """

    def get(self):
        """Handles GET requests to the paging by cursors sub-application.

        If there is a bookmark value in the query parameters, uses it to create
        a cursor and page using it. Includes up to PAGE_SIZE results and a link
        to the next page of results if any more exist.
        """
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
        """Handles POST requests for inserting a single suggestion."""
        SuggestionByCursor(suggestion=self.request.get('suggestion')).put()
        self.redirect('/cursor/')


class SuggestionByCursorPopulate(BaseHandler):
    """Populates the datastore with some sample suggestions

    Provided so end users can pre-populate with PAGE_SIZE + 1 entities to see
    how cursor-based paging works.
    """

    def post(self):
        """Handles POST requests and adds sample suggestions."""
        SuggestionByCursor.populate()
        self.redirect('/cursor/')


APPLICATION = webapp2.WSGIApplication([
        ('/cursor/pop/', SuggestionByCursorPopulate),
        ('/cursor/', SuggestionByCursorHandler)],
        debug=True)
