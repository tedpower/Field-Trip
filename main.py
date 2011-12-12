from google.appengine.dist import use_library
use_library('django', '1.2')
from math import *
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from django.utils import simplejson
from google.appengine.ext.webapp import template
from operator import itemgetter
import os
import logging
import wsgiref.handlers
import Cookie
import uuid
import datetime
import time
import calendar
import urllib
import security
from auth import *
from models import *

class Index(webapp.RequestHandler):

  def get(self):
    cookieValue = None
    try:
        cookieValue = self.request.cookies['corpoCookie']
    except KeyError:
        logging.info('no cookie')
    if cookieValue:
        cookieUser = User.get_by_key_name(cookieValue)
        path = os.path.join(os.path.dirname(__file__), 'templates/authreturn.html')
        self.response.out.write(template.render(path, {'user' : cookieUser}))
    else:
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, {}))

  def post(self):
      """Handle data posted from main form"""
      pass
      
class Settings(webapp.RequestHandler):

    def get(self):
        cookieValue = None
        try:
            cookieValue = self.request.cookies['corpoCookie']
        except KeyError:
            logging.info('no cookie')
        if cookieValue:
            cookieUser = User.get_by_key_name(cookieValue)
            path = os.path.join(os.path.dirname(__file__), 'templates/settings.html')
            self.response.out.write(template.render(path, {'user' : cookieUser}))
        else:
            self.redirect("/")        
        
class FS_OAuthRequest(webapp.RequestHandler):

    def get(self):
        self.redirect("https://foursquare.com/oauth2/authenticate?client_id=%s&response_type=code&redirect_uri=%s" % (foursquare_creds['key'], foursquare_creds['return_url']))

class IG_OAuthRequest(webapp.RequestHandler):

    def get(self):
        self.redirect("https://api.instagram.com/oauth/authorize/?client_id=%s&redirect_uri=%s&response_type=code" % (instagram_creds['key'], instagram_creds['return_url']))

class IG_OAuthRequestValid(webapp.RequestHandler):
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
      self_response_url = "https://api.instagram.com/v1/users/self/?access_token=%s" % (access_token['access_token'])
      self_response_json = urlfetch.fetch(self_response_url, validate_certificate=False)
      self_response = simplejson.loads(self_response_json.content)
      
      cookieValue = None
      try:
        cookieValue = self.request.cookies['corpoCookie']
      except KeyError:
        logging.info('no cookie')
      if cookieValue:
        currentUser = User.get_by_key_name(cookieValue)
      else:
        u = uuid.uuid4()        
        currentUser = User(key_name=str(u))
      currentUser.ig_token = access_token['access_token']
      currentUser.ig_id = str(self_response['data']['id'])
      currentUser.put()
            
      taskqueue.add(url='/ig_justphotos', params={'key': currentUser.key().name()})
        
    # set the cookie!
    self.response.headers.add_header(
          'Set-Cookie', 'corpoCookie=%s; expires=Fri, 31-Dec-2020 23:59:59 GMT' % currentUser.key().name())
      
    self.redirect("/")

class FS_OAuthRequestValid(webapp.RequestHandler):
  
  def get(self):
    
    startT = datetime.datetime.now()
    
    code = self.request.get('code')
    url = "https://foursquare.com/oauth2/access_token?client_id=%s&client_secret=%s&grant_type=authorization_code&redirect_uri=%s&code=%s" % (foursquare_creds['key'], foursquare_creds['secret'], foursquare_creds['return_url'], code)
    auth_json = urlfetch.fetch(url, validate_certificate=False)
    access_token = simplejson.loads(auth_json.content)
    
    # we now have a valid token
    # this token needs to be included with every API request
    
    query = db.Query(User)
    query.filter('token =', access_token['access_token'])
    results = query.fetch(limit=1)
    if len(results) > 0:
      logging.info('user exists')
      currentUser = results[0]
    else:
      self_response_url = "https://api.foursquare.com/v2/users/self?oauth_token=%s" % (access_token['access_token'])
      self_response_json = urlfetch.fetch(self_response_url, validate_certificate=False)
      self_response = simplejson.loads(self_response_json.content)
      
      cookieValue = None
      try:
        cookieValue = self.request.cookies['corpoCookie']
      except KeyError:
        logging.info('no cookie')
      if cookieValue:
        currentUser = User.get_by_key_name(cookieValue)
      else:
        u = uuid.uuid4()        
        currentUser = User(key_name=str(u))
      
      currentUser.token = access_token['access_token']
      currentUser.fs_id = str(self_response['response']['user']['id'])
      currentUser.fs_firstName = self_response['response']['user']['firstName']
      currentUser.fs_lastName = self_response['response']['user']['lastName']
      if 'twitter' in self_response['response']['user']['contact']:
        currentUser.twitter = self_response['response']['user']['contact']['twitter']
      if 'photo' in  self_response['response']['user']:
        currentUser.fs_profilePic = self_response['response']['user']['photo']
      currentUser.fs_homeCity = self_response['response']['user']['homeCity']
      currentUser.fs_email = self_response['response']['user']['contact']['email']
      currentUser.put()
          
      taskqueue.add(url='/fs_justphotos', params={'key': currentUser.key().name()})
      
    # set the cookie!
    self.response.headers.add_header(
          'Set-Cookie', 'corpoCookie=%s; expires=Fri, 31-Dec-2020 23:59:59 GMT' % currentUser.key().name())
    
    logging.info("total time of outer thing: " + str(datetime.datetime.now() - startT))
    
    self.redirect("/")


class FindTrips(webapp.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['corpoCookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      # get the lat long from Google
      homeCitySlug = currentUser.fs_homeCity.replace(" ", "+")
      google_url = "http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false" % (homeCitySlug)
      google_json = urlfetch.fetch(google_url, validate_certificate=False)
      google_response = simplejson.loads(google_json.content)
      logging.info(google_url)
      logging.info(google_response)
      if len(google_response['results']) > 0:
        currentUser.homeCityLat = google_response['results'][0]['geometry']['location']['lat']
        currentUser.homeCityLng = google_response['results'][0]['geometry']['location']['lng']
      else: # TODO: remove this, sets it ny
        currentUser.homeCityLat = 40.7143528
        currentUser.homeCityLng = -74.00597309999999

      # now get the photos!
      allDatePts = []
      fillErUp(currentUser, 0, allDatePts)
      
      # mix in dates and points from photos
      for photo in currentUser.all_photos:
        currentPhoto = Photo.get_by_key_name(photo)
        lat = currentPhoto.fs_lat
        lng = currentPhoto.fs_lng
        point = db.GeoPt(lat=lat,lon=lng)
        allDatePts.append((currentPhoto.fs_createdAt, point))
      
      # sort it by date, reverse chronological
      allDatePts = sorted(allDatePts, key=itemgetter(0), reverse=True)
      
      findTripRanges(currentUser, allDatePts)
      
      # Loop through and name the trips      
      for trip in currentUser.trips:
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
          elif len(cities) > 0:
            citystate.reverse()
            thisTrip.title = nameify(thisTrip, citystate)
          elif len(states) > 0:
            states.reverse()
            thisTrip.title = nameify(thisTrip, states)
          thisTrip.put()
      
      # if there are any airports adjacent to a trip, add them to that trip
      allTrips = len(currentUser.trips)
      i = 0
      while i < (allTrips - 1):
        thisTrip = Trip.get_by_key_name(currentUser.trips[i])
        prevTrip = Trip.get_by_key_name(currentUser.trips[i+1])
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
      
      currentUser.updated = True
      currentUser.put()
      # logging.info('wop wop!')
      self.redirect("/")
      


# iterates through all checkins from the user, finds photos and groups the into trips
def fillErUp(currentUser, index, allDatePts):
  
  prevIndex = index
  photos_url = "https://api.foursquare.com/v2/users/self/checkins?limit=200&offset=%s&oauth_token=%s" % (index, currentUser.token)
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
    fillErUp(currentUser, index, allDatePts)

def findTripRanges(currentUser, allDatePts):
  currentTime = allDatePts[0][0]
  tripKey = "f" + currentUser.fs_id + "d" + str(time.mktime(currentTime.timetuple()))
  currentTrip = Trip(key_name=tripKey)
  currentTrip.ongoing = True;
  prevCheckinDate = allDatePts[0][0]
  newTrips = []
  
  for i in range(len(allDatePts)):
    cLat = allDatePts[i][1].lat
    cLng = allDatePts[i][1].lon
    checkinDstnc = haversine(cLat, cLng, currentUser.homeCityLat, currentUser.homeCityLng)
    
    if checkinDstnc > currentUser.radius and currentTrip.home == True:
      # hey we're starting a new trip! First wrap up the old one
      currentTrip.start_date = prevCheckinDate
      currentTrip.put()
      newTrips.append(currentTrip.key().name())
      currentTime = allDatePts[i][0]
      tripKey = "f" + currentUser.fs_id + "d" + str(time.mktime(currentTime.timetuple()))
      currentTrip = Trip(key_name=tripKey)
      currentTrip.end_date = allDatePts[i][0]
      currentTrip.home = False
    elif checkinDstnc < currentUser.radius and currentTrip.home == False:
      # end trip
      currentTrip.start_date = prevCheckinDate
      currentTrip.put()
      newTrips.append(currentTrip.key().name())
      # Start a new trip at home
      currentTime = allDatePts[i][0]
      tripKey = "f" + currentUser.fs_id + "d" + str(time.mktime(currentTime.timetuple()))
      currentTrip = Trip(key_name=tripKey)
      currentTrip.end_date = allDatePts[i][0]
    prevCheckinDate = allDatePts[i][0]
  
  # add the first trip
  currentTrip.start_date = prevCheckinDate
  newTrips.append(currentTrip.key().name())
  currentTrip.put()
  
  # now add the photos to the trips
  tripIndx = 0
  photoCount = 0
  thisTrip = Trip.get_by_key_name(newTrips[tripIndx])
  for photo in currentUser.all_photos:
    thisPhoto = Photo.get_by_key_name(photo)
    notAdded = True
    photoCount += 1
    while notAdded:
      if thisTrip.start_date <= thisPhoto.fs_createdAt and thisTrip.ongoing == True:
        thisTrip.photos.append(photo)
        notAdded = False
      elif thisTrip.start_date <= thisPhoto.fs_createdAt <= thisTrip.end_date:
        thisTrip.photos.append(photo)
        notAdded = False
      else:
        thisTrip.put()
        tripIndx += 1
        thisTrip = Trip.get_by_key_name(newTrips[tripIndx])
    thisTrip.put()
          
  # now loop through and delete trips without photos
  for trip in newTrips:
    thisTrip = Trip.get_by_key_name(trip)
    if not thisTrip.photos and not thisTrip.ongoing:
      thisTrip.delete()
    else:
      currentUser.trips.append(trip)
  
  # collapse consecutive @home trips
  i = 0
  while i < (len(currentUser.trips) - 1):
    thisTrip = Trip.get_by_key_name(currentUser.trips[i])
    prevTrip = Trip.get_by_key_name(currentUser.trips[i+1])
    if thisTrip.home == True and prevTrip.home == True:
      thisTrip.photos.extend(prevTrip.photos)
      thisTrip.start_date = prevTrip.start_date
      thisTrip.put()
      prevTrip.delete()
      currentUser.trips.remove(currentUser.trips[i+1])
    else:
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

class FreshStart(webapp.RequestHandler):
    def get(self):
        taskqueue.add(url='/freshstartworker', params={})
        self.redirect("/")

class FreshStartWorker(webapp.RequestHandler):
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
        query = db.GqlQuery("SELECT * FROM IG_Photo")
        for q in query:
          db.delete(q)
        ############################################################

class IG_JustPhotos(webapp.RequestHandler):
  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)
    fillErUpI(currentUser)
    currentUser.put()
    
def fillErUpI(currentUser):
  self_response_url = "https://api.instagram.com/v1/users/self/media/recent/?access_token=%s" % (currentUser.ig_token)
  self_response_json = urlfetch.fetch(self_response_url, validate_certificate=False)
  self_response = simplejson.loads(self_response_json.content)
  logging.info(self_response_url)
  
  for photo in self_response['data']:
    if photo['location']:
      if 'latitude' in photo['location']:
        photoID = photo['id']
        newPhoto = Photo(key_name=photoID)
        newPhoto.fs_id = photoID
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
          newPhoto.fs_shout = photo['caption']['text']
        newPhoto.link = photo['link']
        newPhoto.put()
        currentUser.ig_photos.append(photoID)
                
class FS_JustPhotos(webapp.RequestHandler):
  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)
    recursivePhotoPull(currentUser, 0)
    currentUser.put()
    taskqueue.add(url='/getfriends', params={'key': currentUser.key().name()})
        
def recursivePhotoPull(currentUser, indx):
  indxStart = indx
  photos_url = "https://api.foursquare.com/v2/users/self/photos?offset=%s&limit=500&oauth_token=%s" % (indx, currentUser.token)
  photos_json = urlfetch.fetch(photos_url, validate_certificate=False)
  photos_response = simplejson.loads(photos_json.content)
  count = photos_response['response']['photos']['count']
  # TODO if count == 0:
    # some sort of error handling
  logging.info('fetching ' + photos_url + " count is " + str(count))
  for photo in photos_response['response']['photos']['items']:            
    if 'lat' in photo['venue']['location']:
      addPhotoEndpoint(photo, currentUser)
      indx += 1
      if indx == 20: # quick return to get something up on the screen
        currentUser.put()
  if indx < count and indxStart != indx:
    recursivePhotoPull(currentUser, indx)

# variation of add photos for the /photos endpoint
def addPhotoEndpoint(photo, currentUser):
  photoID = str(photo['id'])
  newPhoto = Photo(key_name=photoID)
  newPhoto.fs_id = photoID
  newPhoto.fs_venue_name = photo['venue']['name']
  newPhoto.fs_venue_id = photo['venue']['id']
  if 'checkin' in photo:
    newPhoto.fs_checkin_id = photo['checkin']['id']
    userPath = ""
    if currentUser.twitter:
      userPath = currentUser.twitter
    else:
      userPath = currentUser.fs_id
    newPhoto.link = "https://foursquare.com/%s/checkin/%s" % (userPath, newPhoto.fs_checkin_id)
    if 'shout' in photo['checkin']:
      newPhoto.fs_shout = photo['checkin']['shout']
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
  newPhoto.fs_lat = photo['venue']['location']['lat']
  newPhoto.fs_lng = photo['venue']['location']['lng']
  newPhoto.photo_url = photo['url']
  newPhoto.width = photo['sizes']['items'][0]['width']
  newPhoto.height = photo['sizes']['items'][0]['height']
  newPhoto.fs_300 = photo['sizes']['items'][1]['url']
  newPhoto.fs_createdAt = datetime.datetime.fromtimestamp(photo['createdAt'])
  newPhoto.put()
  
  # add the photo to the user as well, just in case
  currentUser.fs_photos.append(photoID)

class Preview(webapp.RequestHandler):
  def get(self):
    cookieValue = None
    try:
        cookieValue = self.request.cookies['corpoCookie']
    except KeyError:
        logging.info('no cookie')
    if cookieValue:
        currentUser = User.get_by_key_name(cookieValue)
        startAt = int(self.request.get("startAt"))
        endAt = startAt + 51
        if currentUser.all_photos:
          allLen = len(currentUser.all_photos)
          listOfPhotos = []
          moreLeft = False
          if endAt < allLen:
            moreLeft = True
          else: 
            endAt = allLen
          logging.info("startat is " + str(startAt) + " end is " + str(endAt))
          for photoKey in currentUser.all_photos[startAt : endAt]:
              listOfPhotos.append(Photo.get_by_key_name(photoKey))
          path = os.path.join(os.path.dirname(__file__), 'templates/preview.html')
          self.response.out.write(template.render(path, {'photos' : listOfPhotos[:-1], 'more': moreLeft, 'startNext': endAt - 1}))
        else:
          path = os.path.join(os.path.dirname(__file__), 'templates/preview.html')
          self.response.out.write(template.render(path, {'loading': True }))

class GetFriends(webapp.RequestHandler):
  def post(self):
    key = self.request.get('key')
    currentUser = User.get_by_key_name(key)
    recursiveFriendPull(currentUser, 0)
    currentUser.put()
    
def recursiveFriendPull(currentUser, indx):
  indxStart = indx
  friends_url = "https://api.foursquare.com/v2/users/self/friends?offset=%s&limit=500&oauth_token=%s" % (indx, currentUser.token)
  friends_json = urlfetch.fetch(friends_url, validate_certificate=False)
  friends_response = simplejson.loads(friends_json.content)
  count = friends_response['response']['friends']['count']
  logging.info('fetching ' + friends_url + " count is " + str(count))
  for friend in friends_response['response']['friends']['items']:
    if friend['relationship'] == 'friend':
      currentUser.fs_friends.append(friend['id'])      
    indx += 1
  if indx < count and indxStart != indx:
    recursiveFriendPull(currentUser, indx)

# probably make this a taskque
class MergeIgFs(webapp.RequestHandler):
  def get(self):
    cookieValue = None
    try:
      cookieValue = self.request.cookies['corpoCookie']
    except KeyError:
      logging.info('no cookie')
    if cookieValue:
      currentUser = User.get_by_key_name(cookieValue)
      currentUser.all_photos = []
      logging.info('hey up here!')
      
      if len(currentUser.fs_photos) > 0 and len(currentUser.ig_photos) > 0:
        logging.info('hey in here')
        instaIndx = 0
        ig_photo = Photo.get_by_key_name(currentUser.ig_photos[0])
        for photoKey in currentUser.fs_photos:
          logging.info(instaIndx)
          fs_photo = Photo.get_by_key_name(photoKey)
          if fs_photo.fs_createdAt > ig_photo.fs_createdAt:
            currentUser.all_photos.append(photoKey)
          else:
            if (instaIndx + 1) < len(currentUser.ig_photos):
              currentUser.all_photos.append(currentUser.ig_photos[instaIndx])
              instaIndx += 1
              ig_photo = Photo.get_by_key_name(currentUser.ig_photos[instaIndx])
            elif (instaIndx + 1) == len(currentUser.ig_photos):
              currentUser.all_photos.append(currentUser.ig_photos[instaIndx])
              instaIndx += 1
            else:
              currentUser.all_photos.append(photoKey)
        while instaIndx < len(currentUser.ig_photos):
          currentUser.all_photos.append(currentUser.ig_photos[instaIndx])
          instaIndx += 1
      elif len(currentUser.fs_photos) > 0 and len(currentUser.ig_photos) == 0:
        currentUser.all_photos = currentUser.fs_photos
      elif len(currentUser.fs_photos) == 0 and len(currentUser.ig_photos) > 0:
        currentUser.all_photos = currentUser.ig_photos
      currentUser.put()
    self.redirect("/")      

class HidePhoto(webapp.RequestHandler):
  def get(self):
    photoID = self.request.get('id')
    cookieValue = None
    try:
      cookieValue = self.request.cookies['corpoCookie']
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
    
application = webapp.WSGIApplication([('/', Index,),
                                      ('/fs_auth', FS_OAuthRequest),
                                      ('/ig_auth', IG_OAuthRequest),
                                      ('/fs_authreturn', FS_OAuthRequestValid),
                                      ('/ig_authreturn', IG_OAuthRequestValid),
                                      ('/fs_justphotos', FS_JustPhotos),
                                      ('/ig_justphotos', IG_JustPhotos),
                                      ('/settings', Settings),
                                      ('/freshstart', FreshStart),
                                      ('/freshstartworker', FreshStartWorker),
                                      ('/preview', Preview),
                                      ('/getfriends', GetFriends),
                                      ('/findTrips', FindTrips),
                                      ('/hidePhoto', HidePhoto),
                                      ('/merge', MergeIgFs)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()