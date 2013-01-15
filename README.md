# Suggestion Box

"Suggestion Box" is an example application that covers two different
approaches to paging through result sets in Google App Engine datastore
queries.

The first approach ("Unique") manually creates a unique value for each
suggestion in submitted and uses that to query on when paging.

The second approach ("Cursor") simply tracks the timestamp when each suggestion
was submitted and uses a datastore cursor returned from each query to page
through the result set.

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [NDB Datastore API][3]

## Dependencies
- [webapp2][4]
- [jinja2][5]


[1]: https://developers.google.com/appengine
[2]: https://python.org
[3]: https://developers.google.com/appengine/docs/python/ndb/
[4]: http://webapp-improved.appspot.com/
[5]: http://jinja.pocoo.org/docs/
