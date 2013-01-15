#!/usr/bin/env python
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Suggestion Box - An example paging application.

A simple Suggestion Box application that demonstrates
paging by creating a unique value for each suggestion. The
uniqueness is created by sharding counters across
all the users of the system.

"""

import datetime
import hashlib

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required
import webapp2

from base_handler import BaseHandler


PAGE_SIZE = 5
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class Contributor(ndb.Model):
  """Model for storing users that contribute suggestions.

  Contributors are stored with a key of the users email address. The 'count' is
  used as a per user counter that is incremented each time a user adds a
  Suggestion and is used to generate a unique property value 'creation_token'
  that allows paging over suggestions in creation order.
  """
  count = ndb.IntegerProperty(default=0)

  @classmethod
  @ndb.transactional
  def unique_id(cls, email):
    """Increments contributor suggestion count and creates a unique ID from it

    The resulting string is hashed to keep the users email address private.

    Args:
       email: String; The email of the currently logged in user.

    Returns:
       A hashed unique value based on the user and the associated incremented
         Contributor.count.
    """
    contributor = cls.get_by_id(email)
    if contributor == None:
      contributor = cls(id=email)
    contributor.count += 1
    contributor.put()

    md5_hash = hashlib.md5('{}|{:d}'.format(email, contributor.count))
    return md5_hash.hexdigest()


class CreationTokenProperty(ndb.StringProperty):
  """Custom string property which adds creation token value if not set."""

  def _prepare_for_put(self, entity):
    """A method to augment the current value if not already set.

    Args:
      entity: The entity possessing this property.
    """
    if not self._has_value(entity):
      user = users.get_current_user()
      # This will fail if there is no signed in user
      unique_id = Contributor.unique_id(user.email())

      now_as_string = datetime.datetime.now().strftime(TIME_FORMAT)
      value = '{}|{}'.format(now_as_string, unique_id)

      self._store_value(entity, value)


class Suggestion(ndb.Model):
  """Model for storing suggestions contributed to the application.

  A suggestion in the suggestion box, which we want to display in the order
  they were created.
  """
  suggestion = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)
  creation_token = CreationTokenProperty()

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


class SuggestionHandler(BaseHandler):
  """
  Handles the creation of a single Suggestion, and the display
  of suggestions broken into PAGE_SIZE pages.
  """

  @login_required
  def get(self):
    bookmark = self.request.get('bookmark')
    query = Suggestion.query().order(-Suggestion.creation_token)
    if bookmark:
      query = query.filter(Suggestion.creation_token <= bookmark)
    suggestions = query.fetch(PAGE_SIZE + 1)

    creation_token = None
    if len(suggestions) == PAGE_SIZE + 1:
      creation_token = suggestions[-1].creation_token
      suggestions = suggestions[:PAGE_SIZE]

    self.render_response('suggestion.html', bookmark=creation_token,
                         suggestions=suggestions)

  def post(self):
    Suggestion(suggestion=self.request.get('suggestion')).put()
    self.redirect('/unique/')


class SuggestionPopulate(BaseHandler):

  def post(self):
    Suggestion.populate()
    self.redirect('/unique/')


APPLICATION = webapp2.WSGIApplication([('/unique/pop/', SuggestionPopulate),
                                       ('/unique/', SuggestionHandler)],
                                      debug=True)
