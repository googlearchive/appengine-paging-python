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
paging by using the __key__ property provided for every
entity.

"""

import base64
import datetime
import hashlib
import logging
import os
import pickle
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required
from time import mktime


PAGESIZE = 5  


class SuggestionByKey(db.Model):
  """
  A suggestion in the suggestion box, which we want to display
  in the order they were created.
  """
  suggestion = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)  


def encodebookmark(created, key):
  """
  From the created timestamp and the key for an entity create
  a base64 encoded bookmark that can be used for paging.
  
  Args:
    created:  datetime when the entity was created.
    key:      db.Key() of the entity.
  
  Returns:
    A base64 encoded representation of the values.
  """
  timestamp = mktime(created.timetuple())+1e-6*created.microsecond
  return base64.b64encode("%f|%s" % (timestamp, key))


def decodebookmark(b64bookmark):
  """
  Takes a string encoded by 'encodebookmark' and reverses 
  the process.
  
  Args:
    A base64 encoded representation of the values.
  
  Returns:
    (created, key) where 
    
    created:  datetime when the entity was created.
    key:      db.Key() of the entity.
  """
  timestamp, key = base64.b64decode(b64bookmark).split('|')
  created = datetime.datetime.fromtimestamp(float(timestamp))
  return created, key

  
class SuggestionByKeyHandler(webapp.RequestHandler):
  """
  Handles the creation of a single Suggestion, and the display
  of suggestions broken into PAGESIZE pages.
  """

  @login_required
  def get(self):
    bookmark = self.request.get('bookmark')
    next = None
    if bookmark:
      created, key = decodebookmark(bookmark)
      logging.info('key = %s, created = %s' % (key, created))
      query = SuggestionByKey.gql(
        ' WHERE created = :created AND __key__ >= :key ORDER BY __key__ ASC', 
        created = created, key = db.Key(key))
      suggestions = query.fetch(PAGESIZE+1) 
      logging.info(type(suggestions))
      if len(suggestions) < (PAGESIZE + 1):
        logging.info('Going for more entities since we only got %d' % len(suggestions))
        remainder = PAGESIZE + 1 - len(suggestions)
        query = SuggestionByKey.gql(
          'WHERE created < :created ORDER BY created DESC, __key__ ASC', 
          created = created)
        moresuggestions = query.fetch(remainder)
        logging.info('Got %d more' % len(moresuggestions))
        suggestions += moresuggestions
        logging.info('For a total of %d entities' % len(suggestions))
    else:
      query = SuggestionByKey.gql('ORDER BY created DESC, __key__ ASC')
      suggestions = query.fetch(PAGESIZE+1)
    if len(suggestions) == PAGESIZE+1:
      next = encodebookmark(suggestions[-1].created, suggestions[-1].key())
      suggestions = suggestions[:PAGESIZE]
      
    template_values = {'next': next, 'suggestions': suggestions}    
    template_file = os.path.join(os.path.dirname(__file__), 'suggestion.html')
    self.response.out.write(template.render(template_file, template_values))

  def post(self):
    s = SuggestionByKey(suggestion = self.request.get('suggestion'))        
    s.put()
    self.redirect('/key/')

    
class SuggestionByKeyPopulate(webapp.RequestHandler):
  """
  Handles populating the datastore with some sample
  Suggestions to see how the paging works.
  """
  def post(self):
    now = datetime.datetime.now()
    for i in range(6):
      s = SuggestionByKey(suggestion = 'Suggestion %d' % i, created = now)
      s.put()
    self.redirect('/key/')
        

def main():
  application = webapp.WSGIApplication([
    ('/key/pop/', SuggestionByKeyPopulate),
    ('/key/', SuggestionByKeyHandler)
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
  

