import logging
import time
import datetime
import webapp2
from operator import itemgetter, attrgetter
from google.appengine.api import urlfetch
from django.utils import simplejson
import main
from auth import *
from models import *

class UpdateAllPhotos(webapp2.RequestHandler):
  def get(self):
    userList = User.all()

    for user in userList:
      photoDiff = []
      lastUpdated = str(int(time.mktime(user.last_updated.timetuple())))

      # update instagram
      self_response_url = "https://api.instagram.com/v1/users/self/media/recent/?min_timestamp=%s&access_token=%s" % (lastUpdated, user.ig_token)
      self_response_json = urlfetch.fetch(self_response_url, validate_certificate=False)
      self_response = simplejson.loads(self_response_json.content)
      logging.info(self_response_url)
      for photo in self_response['data']:
        if int(photo['created_time']) > int(lastUpdated):
          if photo['location']:
            if 'latitude' in photo['location']:
              logging.info('adding an ig photo')
              newPhoto = main.IG_AddPhoto(photo)
              newPhoto.put()
              user.ig_photos.append(newPhoto.key_id)
              photoDiff.append(newPhoto)

      # update fs photos
      photos_url = "https://api.foursquare.com/v2/users/self/photos?limit=100&oauth_token=%s" % (user.fs_token)
      photos_json = urlfetch.fetch(photos_url, validate_certificate=False)
      photos_response = simplejson.loads(photos_json.content)
      logging.info('fetching ' + photos_url)
      for photo in photos_response['response']['photos']['items']:
        if int(photo['createdAt']) > int(lastUpdated):
          if 'lat' in photo['venue']['location']:
            logging.info('adding a fs photo ' + photo['url'])
            newPhoto = main.FS_LoadPhoto(photo, user)
            newPhoto.put()
            user.fs_photos.append(newPhoto.key_id)
            photoDiff.append(newPhoto)

      # get new date points
      datePtsDiff = []
      photos_url = "https://api.foursquare.com/v2/users/self/checkins?afterTimestamp=%s&limit=200&oauth_token=%s" % (lastUpdated, user.fs_token)
      photos_json = urlfetch.fetch(photos_url, validate_certificate=False)
      photos_response = simplejson.loads(photos_json.content)
      logging.info(photos_url)
      for item in photos_response['response']['checkins']['items']:
        if 'venue' in item: # we need this check to weed out shouts
          if 'lat' in item['venue']['location']:
            lat = float(item['venue']['location']['lat'])
            lng = float(item['venue']['location']['lng'])
            datePtsDiff.append((datetime.datetime.fromtimestamp(item['createdAt']), db.GeoPt(lat=lat,lon=lng)))

      if len(photoDiff) > 0 or len(datePtsDiff) > 0:

        # load in the ongoing trip photos
        ongoingTrip = Trip.get_by_key_name(user.ongoingTrip)
        for photoKey in ongoingTrip.photos:
          photoDiff.append(Photo.get_by_key_name(photoKey))

        # sort photodiff by date
        photoDiff = sorted(photoDiff, key=attrgetter('fs_createdAt'), reverse=True)
        for photo in photoDiff:
          if (not photo.ig_pushed_to_fs) or (user.ig_id == None):
            user.all_photos.insert(0, photo.key_id)

        # mix in date pts from photos
        for photo in photoDiff:
          lat = photo.fs_lat
          lng = photo.fs_lng
          point = db.GeoPt(lat=lat,lon=lng)
          datePtsDiff.append((photo.fs_createdAt, point))

        # sort geoPts by date, reverse chronological
        datePtsDiff = sorted(datePtsDiff, key=itemgetter(0), reverse=True)

        tripDiff = main.findTripRanges(user, photoDiff, datePtsDiff)

        # Loop through and name the trips
        main.nameTrips(tripDiff)

        # if there are any airports adjacent to a trip, add them to that trip
        main.airportJiggle(tripDiff)

        # pop the old ongoing trip from the trip list and replace it with these trips
        user.trips = user.trips[1:]
        for trip in tripDiff:
          user.trips.insert(0, trip)

      logging.info(datetime.datetime.now())
      logging.info(user.last_updated)
      user.last_updated = datetime.datetime.now()
      user.put()
      logging.info('end')

      # check friends

class UpdateAllFriends(webapp2.RequestHandler):
  def get(self):
    userList = User.all()
    photoDiff = []

    # 1. make a list of all fb ids and fs ids in the system
    allUsers = User.all()
    allUserKeys = []
    for user in allUsers:
      if user.fs_id is not None:
        allUserKeys.append(user.fs_id)
    logging.info(allUserKeys)

    for user in userList:

      a_multiset = collections.Counter(allUserKeys)
      b_multiset = collections.Counter(currentUser.fs_friends)

      overlap = list((a_multiset & b_multiset).elements())
      logging.info(overlap)

      friends = []
      for friendKey in overlap:
        query = db.Query(User)
        query.filter('fs_id =', friendKey)
        results = query.fetch(limit=1)
      if len(results) > 0:
        friend = results[0]
        friends.append(friend)

      # next update facebook friends
      # don't store 4sq friends, store friends on here

      path = os.path.join(os.path.dirname(__file__), 'templates/friends.html')
      self.response.out.write(template.render(path, {'friends' : friends}))


app = webapp2.WSGIApplication([('/update/photos', UpdateAllPhotos),
                               ('/update/friends', UpdateAllFriends)], debug=True)



