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
import os
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app


PAGESIZE = 5


class Contributor (db.Model):
  """
  Contributors are stored with a key of the users email
  address. The 'count' is used as a per user
  counter that is incremented each time a user
  adds a Suggestion and is used to generate a unique
  property value 'Suggestion.when' that allows paging
  over suggestions in creation order.
  """
  count = db.IntegerProperty(default=0)


class Suggestion(db.Model):
  """
  A suggestion in the suggestion box, which we want to display
  in the order they were created.
  """
  suggestion = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  when = db.StringProperty()
  
  
def _unique_user(user):
  """
  Creates a unique string by using an increasing
  counter sharded per user. The resulting string
  is hashed to keep the users email address private.
  
  Args:
     The currently logged in user.
     
  Returns:
     A hashed unique value based on the user
     and the associated incremented Contributor.count.
  """
  email = user.email()
 
  def txn():
    contributor = Contributor.get_by_key_name(email)
    if contributor == None:
      contributor = Contributor(key_name=email) 
    contributor.count += 1
    contributor.put()
    return contributor.count

  count = db.run_in_transaction(txn)

  return hashlib.md5(email + '|' + str(count)).hexdigest()

  
def whenfromcreated(created):
  """
  Create a unique 'when' property value based on the
  time the entity was created.
  
  Args:
    created:  datetime the entity was created.
  
  Returns:
    A unique value that will be ordered by 
    entity creation time.
  """
  return created.isoformat()[0:19] + '|' + _unique_user(users.get_current_user())


class SuggestionHandler(webapp.RequestHandler):
  """
  Handles the creation of a single Suggestion, and the display
  of suggestions broken into PAGESIZE pages.
  """
  
  @login_required
  def get(self):
    bookmark = self.request.get('bookmark')
    next = None
    if bookmark:
      query = Suggestion.gql('WHERE when <= :bookmark ORDER BY when DESC', 
        bookmark=bookmark)
      suggestions = query.fetch(PAGESIZE+1)
    else:
      suggestions = Suggestion.gql('ORDER BY when DESC').fetch(PAGESIZE+1)
    if len(suggestions) == PAGESIZE+1:
      next = suggestions[-1].when
      suggestions = suggestions[:PAGESIZE]
      
    template_values = {'next': next, 'suggestions': suggestions}    
    template_file = os.path.join(os.path.dirname(__file__), 'suggestion.html')
    self.response.out.write(template.render(template_file, template_values))

  def post(self):
    now = datetime.datetime.now()
    when = whenfromcreated(now)
    s = Suggestion(
      suggestion = self.request.get('suggestion'), 
      when=when, 
      created=now)        
    s.put()

    self.redirect('/unique/')


class SuggestionPopulate(webapp.RequestHandler):
  def post(self):
    now = datetime.datetime.now()
    for i in range(6):
      s = Suggestion(
        suggestion = 'Suggestion %d' % i, 
        created = now, 
        when = whenfromcreated(now))
      s.put()

    self.redirect('/unique/')       


def main():
  application = webapp.WSGIApplication([
    ('/unique/pop/', SuggestionPopulate),
    ('/unique/', SuggestionHandler)
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
