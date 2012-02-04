from math import *
import webapp2
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from django.utils import simplejson
from google.appengine.ext.webapp import template
from operator import itemgetter, attrgetter
import collections
import os
import logging
import wsgiref.handlers
import Cookie
import uuid
import datetime
import time
import calendar
import urllib
import urlparse
import security
from auth import *
from models import *

class Index(webapp2.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue is not None:
      logging.info('cookie found')
      cookieUser = User.get_by_key_name(cookieValue)
      if cookieUser.complete_stage == 1:
        self.redirect("/signup")
      if cookieUser.complete_stage == 2:
        path = os.path.join(os.path.dirname(__file__), 'templates/loading.html')
        self.response.out.write(template.render(path, {}))
      else:
        requestPath = self.request.path
        logging.info(requestPath)
        path = os.path.join(os.path.dirname(__file__), 'templates/you.html')
        self.response.out.write(template.render(path, {'user' : cookieUser, 'path' : requestPath}))
    else:
      path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
      self.response.out.write(template.render(path, {}))

  def post(self):
      """Handle data posted from main form"""
      pass


class FriendPage(webapp2.RequestHandler):
  def get(self, friend_id):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      cookieUser = User.get_by_key_name(cookieValue)

      requestPath = self.request.path
      logging.info(requestPath)
      path = os.path.join(os.path.dirname(__file__), 'templates/you.html')
      self.response.out.write(template.render(path, {'user' : cookieUser, 'path' : requestPath}))


class Settings(webapp2.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      cookieUser = User.get_by_key_name(cookieValue)
      path = os.path.join(os.path.dirname(__file__), 'templates/settings.html')
      self.response.out.write(template.render(path, {'user' : cookieUser}))
    else:
      self.redirect("/")


class FS_OAuthRequest(webapp2.RequestHandler):
  def get(self):
    self.redirect("https://foursquare.com/oauth2/authenticate?client_id=%s&response_type=code&redirect_uri=%s" % (foursquare_creds['key'], foursquare_creds['return_url']))


class IG_OAuthRequest(webapp2.RequestHandler):
  def get(self):
    self.redirect("https://api.instagram.com/oauth/authorize/?client_id=%s&redirect_uri=%s&response_type=code" % (instagram_creds['key'], instagram_creds['return_url']))


class FB_OAuthRequest(webapp2.RequestHandler):
  def get(self):
    self.redirect("https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s&scope=offline_access" % (facebook_creds['key'], facebook_creds['return_url']))


class FS_OAuthRequestValid(webapp2.RequestHandler):
  def get(self):
    code = self.request.get('code')
    url = "https://foursquare.com/oauth2/access_token?client_id=%s&client_secret=%s&grant_type=authorization_code&redirect_uri=%s&code=%s" % (foursquare_creds['key'], foursquare_creds['secret'], foursquare_creds['return_url'], code)
    logging.info(url)
    auth_json = urlfetch.fetch(url, method=urlfetch.GET, deadline=10)
    access_token = simplejson.loads(auth_json.content)

    query = db.Query(User)
    query.filter('fs_token =', access_token['access_token'])
    results = query.fetch(limit=1)
    if len(results) > 0:
      logging.info('user exists')
      currentUser = results[0]
    else:

      cookieValue = None
      try:
        cookieValue = self.request.cookies['FT_Cookie']
      except KeyError:
        logging.info('no cookie')
      if cookieValue:
        currentUser = User.get_by_key_name(cookieValue)
      else:
        u = uuid.uuid4()
        currentUser = User(key_name=str(u))
        currentUser.key_id = str(u)

      self_response_url = "https://api.foursquare.com/v2/users/self?oauth_token=%s" % (access_token['access_token'])
      self_response_json = urlfetch.fetch(self_response_url, validate_certificate=False)
      self_response = simplejson.loads(self_response_json.content)

      currentUser.fs_token = access_token['access_token']
      currentUser.fs_id = str(self_response['response']['user']['id'])
      if not currentUser.firstName:
        currentUser.firstName = self_response['response']['user']['firstName']
      if not currentUser.lastName:
        currentUser.lastName = self_response['response']['user']['lastName']
      if 'twitter' in self_response['response']['user']['contact']:
        currentUser.twitter = self_response['response']['user']['contact']['twitter']
      if 'photo' in  self_response['response']['user']:
        currentUser.fs_profilePic = self_response['response']['user']['photo']
      if not currentUser.homeCity:
        currentUser.homeCity = self_response['response']['user']['homeCity']
      if not currentUser.email:
        currentUser.email = self_response['response']['user']['contact']['email']
      u = uuid.uuid4()
      currentUser.fs_photos = str(u)

      if not currentUser.ig_token:
        currentUser.complete_stage = 1 # just fs

      currentUser.put()

      taskqueue.add(url='/fs_justphotos', params={'key': currentUser.key().name()})

    # set the cookie! TODO: make this something like today + 2 weeks?
    cookieString = str('FT_Cookie=%s; expires=Fri, 31-Dec-2020 23:59:59 GMT' % currentUser.key().name())
    self.response.headers.add_header('Set-Cookie', cookieString)

    self.redirect("/")


class IG_OAuthRequestValid(webapp2.RequestHandler):
  def get(self):
    code = self.request.get('code')
    data = urllib.urlencode({"client_id":instagram_creds['key'],"client_secret":instagram_creds['secret'],"grant_type":"authorization_code","redirect_uri":instagram_creds['return_url'],"code":code})
    result = urllib.urlopen("https://api.instagram.com/oauth/access_token",data).read()
    logging.info(result)
    access_token = simplejson.loads(result)

    query = db.Query(User)
    query.filter('ig_token =', access_token['access_token'])
    results = query.fetch(limit=1)
    if len(results) > 0:
        logging.info('user exists')
        currentUser = results[0]
    else:
      cookieValue = None
      try:
        cookieValue = self.request.cookies['FT_Cookie']
      except KeyError:
        logging.info('no cookie')
      if cookieValue:
        currentUser = User.get_by_key_name(cookieValue)
      else:
        u = uuid.uuid4()
        currentUser = User(key_name=str(u))
        currentUser.key_id = str(u)

      currentUser.ig_token = access_token['access_token']
      currentUser.ig_id = str(access_token['user']['id'])
      u = uuid.uuid4()
      currentUser.ig_photos = str(u)

      if not currentUser.fs_token:
        currentUser.complete_stage = 1 # just ig

      currentUser.put()

      taskqueue.add(url='/ig_justphotos', params={'key': currentUser.key().name()})

    # set the cookie! TODO: make this something like today + 2 weeks?
    cookieString = str('FT_Cookie=%s; expires=Fri, 31-Dec-2020 23:59:59 GMT' % currentUser.key().name())
    self.response.headers.add_header('Set-Cookie', cookieString)

    self.redirect("/")


class FB_OAuthRequestValid(webapp2.RequestHandler):
  def get(self):
    code = self.request.get('code')
    logging.info(code)
    url = "https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s" % (facebook_creds['key'], facebook_creds['return_url'], facebook_creds['secret'], code)
    logging.info(url)
    url_response = urlfetch.fetch(url)
    access_token = urlparse.parse_qs(str(url_response.content))['access_token'][0]
    logging.info(access_token)

    query = db.Query(User)
    query.filter('fb_token =', access_token)
    results = query.fetch(limit=1)
    if len(results) > 0:
      logging.info('user exists')
      currentUser = results[0]
    else:
      cookieValue = None
      try:
        cookieValue = self.request.cookies['FT_Cookie']
      except KeyError:
        logging.info('no cookie')
      if cookieValue:
        currentUser = User.get_by_key_name(cookieValue)
        currentUser.fb_token = access_token

        # get the fb id
        fb_url = "https://graph.facebook.com/me?access_token=%s" % (currentUser.fb_token)
        logging.info(fb_url)
        fb_json = urlfetch.fetch(fb_url, validate_certificate=False)
        fb_response = simplejson.loads(fb_json.content)
        currentUser.fb_id = fb_response['id']

        currentUser.put()

    self.redirect("/")


class FS_JustPhotos(webapp2.RequestHandler):
  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)
    photoIndx = PhotoIndex(key_name=currentUser.fs_photos)
    FS_RecursivePhotoPull(currentUser, photoIndx, 0)
    photoIndx.put()


def FS_RecursivePhotoPull(currentUser, photoIndx, indx):
  indxStart = indx
  photos_url = "https://api.foursquare.com/v2/users/self/photos?offset=%s&limit=500&oauth_token=%s" % (indx, currentUser.fs_token)
  photos_json = urlfetch.fetch(photos_url, validate_certificate=False)
  photos_response = simplejson.loads(photos_json.content)
  count = photos_response['response']['photos']['count']
  logging.info('fetching ' + photos_url + " count is " + str(count))
  for photo in photos_response['response']['photos']['items']:
    if 'venue' in photo:
      if 'lat' in photo['venue']['location']:
        newPhoto = FS_LoadPhoto(photo, currentUser)
        newPhoto.put()
        photoIndx.photos.append(newPhoto.key_id)
    indx += 1
  logging.info("indx is " + str(indx) + " count is " + str(count))
  if indx < count and indxStart != indx:
    FS_RecursivePhotoPull(currentUser, photoIndx, indx)


# variation of add photos for the /photos endpoint
def FS_LoadPhoto(photo, currentUser):
  photoID = str(photo['id'])
  newPhoto = Photo(key_name=photoID)
  newPhoto.key_id = photoID
  newPhoto.fs_venue_name = photo['venue']['name']
  newPhoto.fs_venue_id = photo['venue']['id']
  if 'checkin' in photo:
    newPhoto.fs_checkin_id = photo['checkin']['id']
    newPhoto.fs_createdAt = datetime.datetime.fromtimestamp(photo['checkin']['createdAt'])
    userPath = ""
    if currentUser.twitter:
      userPath = currentUser.twitter
    else:
      userPath = currentUser.fs_id
    newPhoto.link = "https://foursquare.com/%s/checkin/%s" % (userPath, newPhoto.fs_checkin_id)
    if 'shout' in photo['checkin']:
      newPhoto.shout = photo['checkin']['shout']
  else:
    newPhoto.fs_createdAt = datetime.datetime.fromtimestamp(photo['createdAt'])
  if 'address' in photo['venue']['location']:
    newPhoto.fs_address = photo['venue']['location']['address']
  if 'crossStreet' in photo['venue']['location']:
    newPhoto.fs_crossStreet = photo['venue']['location']['crossStreet']
  if 'city' in photo['venue']['location']:
    newPhoto.fs_city = photo['venue']['location']['city']
  if 'state' in photo['venue']['location']:
    newPhoto.fs_state = photo['venue']['location']['state']
  if 'country' in photo['venue']['location']:
    newPhoto.fs_country = photo['venue']['location']['country']
  if 'categories' in photo['venue']:
    if len(photo['venue']['categories']) > 0:
      newPhoto.cat_id = photo['venue']['categories'][0]['id']
      newPhoto.cat_name = photo['venue']['categories'][0]['name']
  if 'source' in photo:
    if photo['source']['name'] == 'Instagram':
      newPhoto.ig_pushed_to_fs = True
  newPhoto.fs_lat = photo['venue']['location']['lat']
  newPhoto.fs_lng = photo['venue']['location']['lng']
  newPhoto.photo_url = photo['url']
  newPhoto.width = photo['sizes']['items'][0]['width']
  newPhoto.height = photo['sizes']['items'][0]['height']
  newPhoto.fs_300 = photo['sizes']['items'][1]['url']
  return newPhoto


class IG_JustPhotos(webapp2.RequestHandler):
  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)
    photoIndx = PhotoIndex(key_name=currentUser.ig_photos)
    IG_LoadPhotos(currentUser, photoIndx)
    photoIndx.put()


def IG_LoadPhotos(currentUser, photoIndx):
  self_response_url = "https://api.instagram.com/v1/users/self/media/recent/?access_token=%s" % (currentUser.ig_token)
  self_response_json = urlfetch.fetch(self_response_url, validate_certificate=False)
  self_response = simplejson.loads(self_response_json.content)
  logging.info(self_response_url)

  for photo in self_response['data']:
    if photo['location']:
      if 'latitude' in photo['location']:
        newPhoto = IG_AddPhoto(photo)
        newPhoto.put()
        photoIndx.photos.append(newPhoto.key_id)


def IG_AddPhoto(photo):
  photoID = photo['id']
  newPhoto = Photo(key_name=photoID)
  newPhoto.key_id = photoID
  newPhoto.photo_url = photo['images']['standard_resolution']['url']
  newPhoto.width = photo['images']['standard_resolution']['width']
  newPhoto.height = photo['images']['standard_resolution']['height']
  newPhoto.fs_300 = photo['images']['low_resolution']['url']
  newPhoto.fs_createdAt = datetime.datetime.fromtimestamp(float(photo['created_time']))
  newPhoto.fs_lat = float(photo['location']['latitude'])
  newPhoto.fs_lng = float(photo['location']['longitude'])
  if 'name' in photo['location']:
    newPhoto.fs_venue_name = photo['location']['name']
  if photo['caption'] is not None:
    newPhoto.shout = photo['caption']['text']
  newPhoto.link = photo['link']
  return newPhoto


class MergeIgFs(webapp2.RequestHandler):
  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)
    currentUser.all_photos = []

    if currentUser.get_fs_photos is not None and currentUser.get_ig_photos is not None:
      allPhotosKeys = currentUser.get_fs_photos.photos + currentUser.get_ig_photos.photos
    elif currentUser.get_fs_photos is None and currentUser.get_ig_photos is not None:
      allPhotosKeys = currentUser.get_ig_photos.photos
    elif currentUser.get_fs_photos is not None and currentUser.get_ig_photos is None:
      allPhotosKeys = currentUser.get_fs_photos.photos
    allPhotos = []
    for key in allPhotosKeys:
      allPhotos.append(Photo.get_by_key_name(key))
    allPhotos = sorted(allPhotos, key=attrgetter('fs_createdAt'), reverse=True)
    orderedKeys = []
    for photo in allPhotos:
      orderedKeys.append(photo.key_id)
    currentUser.all_photos = orderedKeys
    currentUser.put()
    taskqueue.add(url='/findTrips', params={'key': currentUser.key().name()})


class FindTrips(webapp2.RequestHandler):
  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)

    # now get the photos!
    allDatePts = []
    getDatePts(currentUser, 0, allDatePts)

    # mix in dates and points from photos
    for photo in currentUser.all_photos:
      currentPhoto = Photo.get_by_key_name(photo)
      lat = currentPhoto.fs_lat
      lng = currentPhoto.fs_lng
      point = db.GeoPt(lat=lat,lon=lng)
      allDatePts.append((currentPhoto.fs_createdAt, point))

    # sort it by date, reverse chronological
    allDatePts = sorted(allDatePts, key=itemgetter(0), reverse=True)

    # get the photos and find the trips
    allPhotos = []
    for photo in currentUser.all_photos:
      allPhotos.append(Photo.get_by_key_name(photo))
    currentUser.trips = findTripRanges(currentUser, allPhotos, allDatePts)

    # Loop through and name the trips
    nameTrips(currentUser.trips, currentUser.homeCity, currentUser.gHomeState, currentUser.gHomeCountry)

    # if there are any airports adjacent to a trip, add them to that trip
    airportJiggle(currentUser.trips)

    currentUser.complete_stage = 4
    currentUser.put()
    # logging.info('wop wop!')

    taskqueue.add(url='/update/friends', params={'key': currentUser.key().name()})


# iterates through all checkins from the user
def getDatePts(currentUser, index, allDatePts):
  prevIndex = index
  photos_url = "https://api.foursquare.com/v2/users/self/checkins?limit=200&offset=%s&oauth_token=%s" % (index, currentUser.fs_token)
  photos_json = urlfetch.fetch(photos_url, validate_certificate=False)
  photos_response = simplejson.loads(photos_json.content)
  count = photos_response['response']['checkins']['count']
  logging.info('fetching ' + photos_url + " and index is " + str(index) + "/" + str(count))
  for item in photos_response['response']['checkins']['items']:
    if 'venue' in item:  # we need this check to weed out shouts
      if 'lat' in item['venue']['location']:
        lat = float(item['venue']['location']['lat'])
        lng = float(item['venue']['location']['lng'])
        allDatePts.append((datetime.datetime.fromtimestamp(item['createdAt']), db.GeoPt(lat=lat,lon=lng)))
    index += 1
  if index < count and prevIndex != index:
    getDatePts(currentUser, index, allDatePts)


def findTripRanges(currentUser, photos, datePts):
  currentTime = datePts[0][0]
  tripKey = "f" + currentUser.fs_id + "d" + str(int(time.mktime(currentTime.timetuple())))
  currentTrip = Trip(key_name=tripKey)
  currentTrip.key_id = tripKey
  currentTrip.user_id = currentUser.key().name()
  currentTrip.ongoing = True
  currentUser.ongoingTrip = currentTrip.key_id

  cLat = datePts[0][1].lat
  cLng = datePts[0][1].lon
  checkinDstnc = haversine(cLat, cLng, currentUser.homeCityLat, currentUser.homeCityLng)
  if checkinDstnc > currentUser.radius:
    currentTrip.home = False
  else:
    currentTrip.home = True
  prevCheckinDate = datePts[0][0]
  newTrips = []

  for i in range(1, len(datePts)):
    cLat = datePts[i][1].lat
    cLng = datePts[i][1].lon
    checkinDstnc = haversine(cLat, cLng, currentUser.homeCityLat, currentUser.homeCityLng)
    if checkinDstnc > currentUser.radius and currentTrip.home == True:
      # hey we're starting a new trip! First wrap up the old one
      currentTrip.start_date = prevCheckinDate
      currentTrip.put()
      newTrips.append(currentTrip.key().name())
      currentTime = datePts[i][0]
      tripKey = "f" + currentUser.fs_id + "d" + str(int(time.mktime(currentTime.timetuple())))
      currentTrip = Trip(key_name=tripKey)
      currentTrip.key_id = tripKey
      currentTrip.user_id = currentUser.key().name()
      currentTrip.end_date = datePts[i][0]
      currentTrip.home = False
    elif checkinDstnc < currentUser.radius and currentTrip.home == False:
      # end trip
      currentTrip.start_date = prevCheckinDate
      currentTrip.put()
      newTrips.append(currentTrip.key().name())
      # Start a new trip at home
      currentTime = datePts[i][0]
      tripKey = "f" + currentUser.fs_id + "d" + str(int(time.mktime(currentTime.timetuple())))
      currentTrip = Trip(key_name=tripKey)
      currentTrip.key_id = tripKey
      currentTrip.user_id = currentUser.key().name()
      currentTrip.end_date = datePts[i][0]
      currentTrip.home = True
    prevCheckinDate = datePts[i][0]

  # add the first trip
  currentTrip.start_date = prevCheckinDate
  newTrips.append(currentTrip.key().name())
  currentTrip.put()

  # now add the photos to the trips
  tripIndx = 0
  thisTrip = Trip.get_by_key_name(newTrips[tripIndx])
  for photo in photos:
    notAdded = True
    while notAdded:
      if thisTrip.start_date <= photo.fs_createdAt and thisTrip.ongoing == True:
        thisTrip.photos.append(photo.key_id)
        notAdded = False
      elif thisTrip.start_date <= photo.fs_createdAt <= thisTrip.end_date:
        thisTrip.photos.append(photo.key_id)
        notAdded = False
      else:
        thisTrip.put()
        tripIndx += 1
        thisTrip = Trip.get_by_key_name(newTrips[tripIndx])
  thisTrip.put()

  tripList = []
  # now loop through and delete trips without photos
  for trip in newTrips:
    thisTrip = Trip.get_by_key_name(trip)
    if not thisTrip.photos and not thisTrip.ongoing:
      thisTrip.delete()
    else:
      tripList.append(trip)

  # collapse consecutive @home trips
  i = 0
  while i < (len(tripList) - 1):
    thisTrip = Trip.get_by_key_name(tripList[i])
    prevTrip = Trip.get_by_key_name(tripList[i+1])
    if thisTrip.home == True and prevTrip.home == True:
      thisTrip.photos.extend(prevTrip.photos)
      thisTrip.start_date = prevTrip.start_date
      thisTrip.put()
      prevTrip.delete()
      tripList.remove(tripList[i+1])
    else:
      i += 1

  # check if the ongoing trip has photos
  currentTrip = Trip.get_by_key_name(tripList[0])
  if currentTrip.photos:
    currentUser.lastTripWithPhotos = tripList[0]
  else:
    if len(tripList) > 1:
      currentUser.lastTripWithPhotos = tripList[1]
    elif len(currentUser.trips) > 1:
      currentUser.lastTripWithPhotos = currentUser.trips[1]

  return tripList


def nameTrips(trips, homeTown, homeState, homeCountry):
  for trip in trips:
    thisTrip = Trip.get_by_key_name(trip)
    if thisTrip.home == False:
      cities = []
      countries = []
      states = []
      stateShort = False
      citystate = []
      newCity = False
      for photo in thisTrip.photos:
        thisPhoto = Photo.get_by_key_name(photo)
        city = None
        subCity = None
        if thisPhoto.cat_id != '4bf58dd8d48988d1ed931735' and thisPhoto.cat_id != '4bf58dd8d48988d1eb931735':
          google_url = "http://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&sensor=false" % (thisPhoto.fs_lat, thisPhoto.fs_lng)
          google_json = urlfetch.fetch(google_url, validate_certificate=False)
          google_response = simplejson.loads(google_json.content)
          if len(google_response['results']) > 0:
            firstGeocode = google_response['results'][0]
            for component in firstGeocode['address_components']:
              for gType in component['types']:
                if gType == 'locality':
                  thisPhoto.fs_city = component['long_name']
                  city = component['long_name']
                  if thisPhoto.fs_city not in cities:
                    cities.append(thisPhoto.fs_city)
                    newCity = component['long_name']
                if gType == 'sublocality':
                  subCity = component['long_name']
                if gType == 'administrative_area_level_1':
                  thisPhoto.fs_state = component['long_name']
                  stateShort = component['short_name']
                  if thisPhoto.fs_state not in states:
                    states.append(thisPhoto.fs_state)
                if gType == 'country':
                  thisPhoto.fs_country = component['long_name']
                  if thisPhoto.fs_country not in countries:
                    countries.append(thisPhoto.fs_country)
            if city is None and subCity is not None:
              thisPhoto.fs_city = subCity
              if subCity not in cities:
                cities.append(subCity)
                newCity = subCity
            if newCity:
              if stateShort:
                combinedCityState = newCity + ", " + stateShort
                citystate.append(combinedCityState)
              else:
                citystate.append(newCity)
            stateShort = False
            newCity = False
            thisPhoto.put()

      logging.info("------------------------------------------")
      logging.info(cities)
      logging.info(states)
      logging.info(citystate)
      logging.info(countries)
      logging.info("------------------------------------------")

      if len(countries) > 1:
        countries.reverse()
        thisTrip.title = nameify(thisTrip, countries)
        thisTrip.put()
      elif len(states) > 1:
        states.reverse()
        thisTrip.title = nameify(thisTrip, states)
        thisTrip.put()
      elif len(cities) > 1:
        # check if all the photos have the same state
        if Photo.get_by_key_name(thisTrip.photos[0]).fs_state:
          firstState = Photo.get_by_key_name(thisTrip.photos[0]).fs_state
          allGood = True
          for photo in thisTrip.photos:
            thisPhoto = Photo.get_by_key_name(photo)
            if firstState != thisPhoto.fs_state:
              allGood = False
          if allGood == True:
            if firstState != homeState:
              thisTrip.title = firstState
              thisTrip.put()
            else:
              citystate.reverse()
              thisTrip.title = nameify(thisTrip, citystate)
              thisTrip.put()
          else:
            citystate.reverse()
            thisTrip.title = nameify(thisTrip, citystate)
            thisTrip.put()
        else:
          citystate.reverse()
          thisTrip.title = nameify(thisTrip, citystate)
          thisTrip.put()
      elif len(cities) == 1:
        thisTrip.title = citystate[0]
        thisTrip.put()

    else:
      thisTrip.title = homeTown
      thisTrip.put()


def airportJiggle(trips):
  allTrips = len(trips)
  i = 0
  while i < (allTrips - 1):
    thisTrip = Trip.get_by_key_name(trips[i])
    prevTrip = Trip.get_by_key_name(trips[i+1])
    if thisTrip.home and not prevTrip.home and len(thisTrip.photos) > 0:
      lastPhoto = Photo.get_by_key_name(thisTrip.photos[-1])
      if lastPhoto.cat_id == '4bf58dd8d48988d1ed931735' or lastPhoto.cat_id == '4bf58dd8d48988d1eb931735':
        # logging.info('found One')
        prevTrip.photos.insert(0, thisTrip.photos[-1])
        thisTrip.photos = thisTrip.photos[0:-1]
        newLastPhoto = Photo.get_by_key_name(thisTrip.photos[-1])
        thisTrip.start_date = newLastPhoto.fs_createdAt
        prevTrip.end_date = lastPhoto.fs_createdAt
        thisTrip.put()
        prevTrip.put()
    elif not thisTrip.home and prevTrip.home:
      firstPhoto = Photo.get_by_key_name(prevTrip.photos[0])
      if firstPhoto.cat_id == '4bf58dd8d48988d1ed931735' or firstPhoto.cat_id == '4bf58dd8d48988d1eb931735':
        # logging.info('found another')
        thisTrip.photos.append(prevTrip.photos[0])
        prevTrip.photos = prevTrip.photos[1:]
        thisTrip.start_date = firstPhoto.fs_createdAt
        newFirstPhoto = Photo.get_by_key_name(thisTrip.photos[0])
        prevTrip.end_date = newFirstPhoto.fs_createdAt
        thisTrip.put()
        prevTrip.put()
    i += 1


def nameify(trip, places):
    title = ""
    placeCount = len(places)
    if placeCount == 1:
        title = places[0]
    elif placeCount == 2:
        title = places[0] + " & " + places[1]
    elif placeCount > 2:
        endChunk = places[-2] + ", & " + places[-1]
        startChunk = ""
        for place in places[0:-2]:
            startChunk = startChunk + place + ", "
        title = startChunk + endChunk
    return title


class TripLoad(webapp2.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      startAt = int(self.request.get("startAt"))
      if len(currentUser.trips) > startAt:
        thisTrip = Trip.get_by_key_name(currentUser.trips[startAt])
        while not thisTrip.photos:
          startAt += 1
          thisTrip = Trip.get_by_key_name(currentUser.trips[startAt])
        logging.info(thisTrip.title)
        logging.info(thisTrip.key_id)
        path = os.path.join(os.path.dirname(__file__), 'templates/tripLoad.html')
        self.response.out.write(template.render(path, {'trip' : thisTrip, 'next' : startAt + 1}))
      else:
        self.response.out.write('<script>youDone = true;</script>')


class FriendTripLoad(webapp2.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      startAt = int(self.request.get("startAt"))
      if len(currentUser.friends_trips) > startAt:
        thisTrip = Trip.get_by_key_name(currentUser.friends_trips[startAt])
        while not thisTrip.photos:
          startAt += 1
          thisTrip = Trip.get_by_key_name(currentUser.friends_trips[startAt])
        logging.info(thisTrip.title)
        logging.info(thisTrip.key_id)
        path = os.path.join(os.path.dirname(__file__), 'templates/friendTripLoad.html')
        currentTime = datetime.datetime.now()
        self.response.out.write(template.render(path, {'trip' : thisTrip, 'next' : startAt + 1, 'currentTime' : currentTime}))
      else:
        self.response.out.write('<script>friendDone = true;</script>')

class HidePhoto(webapp2.RequestHandler):
  def get(self):
    photoID = self.request.get('id')
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      thisPhoto = Photo.get_by_key_name(photoID)
      thisPhoto.hidden = True
      thisPhoto.put()
      # thisTrip.put()

    # remove it from the trip... probably also need a check to only render trips with at least 1 photo
    # rename the trip... there should be a way to look up which trip each photo belongs to
    #
    # or maybe do it with a hidden count on the trip, if it's < then show the trip? prob. not if we care about naming
    # in the javascript ajax remove the photo and the preview


class Friends(webapp2.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      requestPath = str(self.request.path)
      path = os.path.join(os.path.dirname(__file__), 'templates/friends.html')
      self.response.out.write(template.render(path, {'user' : currentUser, 'path' : requestPath}))


class Networks(webapp2.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      requestPath = str(self.request.path)
      path = os.path.join(os.path.dirname(__file__), 'templates/networks.html')
      self.response.out.write(template.render(path, {'user' : currentUser, 'path' : requestPath}))


class LoadingStage(webapp2.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      if currentUser.complete_stage < 3:
        ready = True
        if currentUser.fs_token:
          if currentUser.get_fs_photos is None:
            ready = False
        if currentUser.ig_token:
          if currentUser.get_ig_photos is None:
            ready = False
        if not ready:
          logging.info('not ready')
          self.response.out.write('Loading all your photos...')
        else:
          logging.info('loading trips')
          currentUser.complete_stage = 3
          currentUser.put()
          taskqueue.add(url='/merge', params={'key': currentUser.key().name()})
          self.response.out.write('Merging your photos into trips (this could take a minute) ...')
      elif currentUser.complete_stage == 3:
        logging.info('loading trips')
        self.response.out.write('Merging your photos into trips (this could take a minute) ...')
      elif currentUser.complete_stage == 4:
        logging.info('finding friends')
        self.response.out.write('Finding your friends')
      elif currentUser.complete_stage == 5:
        self.response.out.write('<div id="go"></div>')



class SignUp(webapp2.RequestHandler):
  def post(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)

      currentUser.firstName = self.request.get('fname')
      currentUser.lastName = self.request.get('lname')
      currentUser.email = self.request.get('email')
      currentUser.homeCity = self.request.get('homeCity')

      errorList = []
      if currentUser.firstName and currentUser.email and currentUser.homeCity:

        # get the lat long from Google
        homeCitySlug = currentUser.homeCity.replace(" ", "+")
        google_url = "http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false" % (homeCitySlug)
        google_json = urlfetch.fetch(google_url, validate_certificate=False)
        google_response = simplejson.loads(google_json.content)
        logging.info(google_url)
        logging.info(google_response)
        if len(google_response['results']) > 0:
          currentUser.homeCityLat = google_response['results'][0]['geometry']['location']['lat']
          currentUser.homeCityLng = google_response['results'][0]['geometry']['location']['lng']
        if not currentUser.homeCityLat:
          errorList.append("Woops! Couldn't find that city")

        subCity = None
        google_url = "http://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&sensor=false" % (currentUser.homeCityLat, currentUser.homeCityLng)
        google_json = urlfetch.fetch(google_url, validate_certificate=False)
        google_response = simplejson.loads(google_json.content)
        if len(google_response['results']) > 0:
          firstGeocode = google_response['results'][0]
          for component in firstGeocode['address_components']:
            for gType in component['types']:
              if gType == 'administrative_area_level_1':
                currentUser.gHomeState = component['long_name']
                currentUser.gHomeStateShort = component['short_name']
              if gType == 'locality':
                currentUser.gHomeCity = component['long_name']
              if gType == 'sublocality':
                subCity = component['long_name']
              if gType == 'country':
                currentUser.gHomeCountry = component['long_name']
            if currentUser.gHomeCity is None and subCity is not None:
              currentUser.gHomeCity = subCity

      else:
        errorList.append("Fist name, email, and home city are required")

      if len(errorList) == 0:
        currentUser.complete_stage = 2
        currentUser.put()
        self.redirect("/networks")
      else:
        path = os.path.join(os.path.dirname(__file__), 'templates/onboarding.html')
        self.response.out.write(template.render(path, {'user' : currentUser, 'errors' : errorList}))

  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      path = os.path.join(os.path.dirname(__file__), 'templates/onboarding.html')
      self.response.out.write(template.render(path, {'user' : currentUser}))


class Logout(webapp2.RequestHandler):
  def get(self):
    cookie = None
    try:
      cookie = self.request.cookies['FT_Cookie']
    except KeyError:
      logging.info('no cookie')
    if cookie:
      cookieString = str('FT_Cookie=%s; expires=Thu, 01-Jan-1970 00:00:01 GMT' % cookie)
      self.response.headers.add_header('Set-Cookie', cookieString)

    self.redirect("/")


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    km = 6367 * c
    mi = km * .6214
    return mi


class FreshStart(webapp2.RequestHandler):
    def get(self):
        taskqueue.add(url='/freshstartworker', params={})
        self.redirect("/")


class FreshStartWorker(webapp2.RequestHandler):
    def post(self):
        ######### DANGER! this empties the datastore ##############
        query = db.GqlQuery("SELECT * FROM Photo")
        for q in query:
          db.delete(q)
        query = db.GqlQuery("SELECT * FROM User")
        for q in query:
          db.delete(q)
        query = db.GqlQuery("SELECT * FROM Trip")
        for q in query:
          db.delete(q)
        query = db.GqlQuery("SELECT * FROM PhotoIndex")
        for q in query:
          db.delete(q)
        ############################################################


app = webapp2.WSGIApplication([('/', Index,),
                               ('/fs_auth', FS_OAuthRequest),
                               ('/ig_auth', IG_OAuthRequest),
                               ('/fb_auth', FB_OAuthRequest),
                               ('/fs_authreturn', FS_OAuthRequestValid),
                               ('/ig_authreturn', IG_OAuthRequestValid),
                               ('/fb_authreturn', FB_OAuthRequestValid),
                               ('/fs_justphotos', FS_JustPhotos),
                               ('/ig_justphotos', IG_JustPhotos),
                               ('/settings', Settings),
                               ('/freshstart', FreshStart),
                               ('/freshstartworker', FreshStartWorker),
                               ('/tripLoad', TripLoad),
                               ('/friendTripLoad', FriendTripLoad),
                               ('/findTrips', FindTrips),
                               ('/hidePhoto', HidePhoto),
                               ('/friends', Friends),
                               ('/merge', MergeIgFs),
                               ('/signup', SignUp),
                               ('/networks', Networks),
                               ('/loadingStage', LoadingStage),
                               ('/friends/(.*)', FriendPage),
                               ('/logout', Logout)],
                              debug=True)