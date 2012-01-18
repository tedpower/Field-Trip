import logging
import time
import datetime
import collections
import webapp2
from operator import itemgetter, attrgetter
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
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
      if user.ig_token:
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
                user.get_ig_photos.photos.append(newPhoto.key_id)
                photoDiff.append(newPhoto)

      # update fs photos
      if user.fs_token:
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
              user.get_fs_photos.photos.append(newPhoto.key_id)
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
        main.nameTrips(tripDiff, user.homeCity)

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


class UpdateAllFriends(webapp2.RequestHandler):
  def get(self):
    allUsers = User.all()
    # First make a list of all fb ids and fs ids in the system
    FS_userKeys = []
    FB_userKeys = []
    for user in allUsers:
      if user.fs_id is not None:
        FS_userKeys.append(user.fs_id)
      if user.fb_id is not None:
        FB_userKeys.append(user.fb_id)

    logging.info(FS_userKeys)
    logging.info(FB_userKeys)
    logging.info('-------')

    for user in allUsers:
      overlap = []

      if user.fs_token is not None:

        # first update the fs friends
        fs_friends = FS_friendPull(user, [], 0)

        # find overlaps between all friends and friends on field trip
        a_multiset = collections.Counter(FS_userKeys)
        b_multiset = collections.Counter(fs_friends)
        intersect = list((a_multiset & b_multiset).elements())
        logging.info(intersect)

        for friendKey in intersect:
          query = db.Query(User)
          query.filter('fs_id =', friendKey)
          results = query.fetch(limit=1)
          if len(results) > 0:
            friend = results[0]
            overlap.append(friend.key().name())

      if user.fb_token is not None:

        # update fb friends
        fb_friends = FB_friendPull(user)

        # find overlaps between all friends and friends on field trip
        a_multiset = collections.Counter(FB_userKeys)
        b_multiset = collections.Counter(fb_friends)
        intersect = list((a_multiset & b_multiset).elements())

        for friendKey in intersect:
          query = db.Query(User)
          query.filter('fb_id =', friendKey)
          results = query.fetch(limit=1)
          if len(results) > 0:
            friend = results[0]
            overlap.append(friend.key().name())

      logging.info('here it is')
      logging.info(overlap)
      # dedupe the list
      overlap = list(set(overlap))
      logging.info(overlap)
      logging.info('-------')

      user.all_friends = overlap
      user.put()

  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)

    allUsers = User.all()
    FS_userKeys = []
    FB_userKeys = []
    for user in allUsers:
      if user.fs_id is not None:
        FS_userKeys.append(user.fs_id)
      if user.fb_id is not None:
        FB_userKeys.append(user.fb_id)

    overlap = []
    if currentUser.fs_token is not None:

      # first update the fs friends
      fs_friends = FS_friendPull(currentUser, [], 0)

      # find overlaps between all friends and friends on field trip
      a_multiset = collections.Counter(FS_userKeys)
      b_multiset = collections.Counter(fs_friends)
      intersect = list((a_multiset & b_multiset).elements())
      logging.info(intersect)

      for friendKey in intersect:
        query = db.Query(currentUser)
        query.filter('fs_id =', friendKey)
        results = query.fetch(limit=1)
        if len(results) > 0:
          friend = results[0]
          overlap.append(friend.key().name())

    if currentUser.fb_token is not None:

      # update fb friends
      fb_friends = FB_friendPull(currentUser)

      # find overlaps between all friends and friends on field trip
      a_multiset = collections.Counter(FB_userKeys)
      b_multiset = collections.Counter(fb_friends)
      intersect = list((a_multiset & b_multiset).elements())

      for friendKey in intersect:
        query = db.Query(User)
        query.filter('fb_id =', friendKey)
        results = query.fetch(limit=1)
        if len(results) > 0:
          friend = results[0]
          overlap.append(friend.key().name())

    overlap = list(set(overlap))
    currentUser.all_friends = overlap
    currentUser.put()
    taskqueue.add(url='/update/friendtrips', params={'key': currentUser.key().name()})

class UpdateFriendTrips(webapp2.RequestHandler):
  def get(self):
    allUsers = User.all()
    for user in allUsers:
      allTripsList = [];
      for friendKey in user.all_friends:
        friend = User.get_by_key_name(friendKey)
        for tripKey in friend.trips:
          trip = Trip.get_by_key_name(tripKey)
          if trip.photos:
            latestPhoto = Photo.get_by_key_name(trip.photos[0])
            allTripsList.append((tripKey, latestPhoto.fs_createdAt))

      for tripKey in user.trips:
        trip = Trip.get_by_key_name(tripKey)
        if trip.photos:
          latestPhoto = Photo.get_by_key_name(trip.photos[0])
          allTripsList.append((tripKey, latestPhoto.fs_createdAt))

      # sort them chronologically... this needs to handle ongoing trips
      allTripsList = sorted(allTripsList, key=itemgetter(1), reverse=True)

      orderedKeys = []
      for tripTuple in allTripsList:
        orderedKeys.append(tripTuple[0])
      user.friends_trips = orderedKeys
      user.put()


  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)
    if len(currentUser.all_friends) > 0:
      allTripsList = [];
      for friendKey in currentUser.all_friends:
        friend = User.get_by_key_name(friendKey)
        for tripKey in friend.trips:
          trip = Trip.get_by_key_name(tripKey)
          if trip.photos:
            latestPhoto = Photo.get_by_key_name(trip.photos[0])
            allTripsList.append((tripKey, latestPhoto.fs_createdAt))

      for tripKey in currentUser.trips:
        trip = Trip.get_by_key_name(tripKey)
        if trip.photos:
          latestPhoto = Photo.get_by_key_name(trip.photos[0])
          allTripsList.append((tripKey, latestPhoto.fs_createdAt))

      # sort them chronologically... this needs to handle ongoing trips
      allTripsList = sorted(allTripsList, key=itemgetter(1), reverse=True)

      orderedKeys = []
      for tripTuple in allTripsList:
        orderedKeys.append(tripTuple[0])
      currentUser.friends_trips = orderedKeys
    currentUser.complete_stage = 5
    currentUser.put()


def FS_friendPull(currentUser, fs_friends, indx):
  indxStart = indx
  friends_url = "https://api.foursquare.com/v2/users/self/friends?offset=%s&limit=500&oauth_token=%s" % (indx, currentUser.fs_token)
  friends_json = urlfetch.fetch(friends_url, validate_certificate=False)
  friends_response = simplejson.loads(friends_json.content)
  count = friends_response['response']['friends']['count']
  for friend in friends_response['response']['friends']['items']:
    if friend['relationship'] == 'friend':
      fs_friends.append(friend['id'])
    indx += 1
  if indx < count and indxStart != indx:
    recursiveFriendPull(currentUser, fs_friends, indx)
  else:
    return fs_friends


def FB_friendPull(currentUser):
  fb_friends = []
  friends_url = "https://graph.facebook.com/me/friends?access_token=%s" % (currentUser.fb_token)
  friends_json = urlfetch.fetch(friends_url, validate_certificate=False)
  friends_response = simplejson.loads(friends_json.content)
  for friend in friends_response['data']:
    fb_friends.append(friend['id'])
  return fb_friends


app = webapp2.WSGIApplication([('/update/photos', UpdateAllPhotos),
                               ('/update/friendtrips', UpdateFriendTrips),
                               ('/update/friends', UpdateAllFriends)], debug=True)


