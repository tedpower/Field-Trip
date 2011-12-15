from google.appengine.dist import use_library
use_library('django', '1.2')
import logging
import time
import datetime
from operator import attrgetter
from google.appengine.api import urlfetch
from django.utils import simplejson
import main
from auth import *
from models import *

userList = User.all()
photoDiff = []

for user in userList:

  lastUpdated = user.last_updated.strftime('%s')

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

  # sort photodiff by date
  if len(photoDiff) > 0:
    photoDiff = sorted(photoDiff, key=attrgetter('fs_createdAt'))
    for photo in photoDiff:
      if (not photo.ig_pushed_to_fs) or (user.ig_id == None):
        user.all_photos.insert(0, photo.key_id)

  # adjust current trip / check the whole trip thing / pull any and all geo pt. updates



  logging.info(datetime.datetime.now())
  logging.info(user.last_updated)
  user.last_updated = datetime.datetime.now()
  user.put()


  # check friends

