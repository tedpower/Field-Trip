from __future__ import division
from google.appengine.ext import db
import datetime
from django.utils import simplejson
from google.appengine.api import urlfetch
import logging

class User(db.Model):
    key_id = db.StringProperty()
    fs_token = db.StringProperty()
    ig_token = db.StringProperty()
    fb_token = db.StringProperty()
    fs_id = db.StringProperty()
    ig_id = db.StringProperty()
    fb_id = db.StringProperty()
    fs_photos = db.StringProperty()
    ig_photos = db.StringProperty()
    all_photos = db.StringListProperty()
    all_friends = db.StringListProperty()
    firstName = db.StringProperty()
    lastName = db.StringProperty()
    email = db.EmailProperty()
    homeCity = db.StringProperty()
    homeCityLat = db.FloatProperty()
    homeCityLng = db.FloatProperty()
    gHomeState = db.StringProperty()
    gHomeStateShort = db.StringProperty()
    gHomeCountry = db.StringProperty()
    gHomeCity = db.StringProperty()
    radius = db.IntegerProperty(default=30)
    fs_profilePic = db.StringProperty()
    # photoCount = db.IntegerProperty()
    trips = db.ListProperty(db.Key)
    friends_trips = db.ListProperty(db.Key)
    twitter = db.StringProperty()
    last_updated = db.DateTimeProperty(auto_now_add=True)
    complete_stage = db.IntegerProperty()

    @property
    def get_fs_photos(self):
        if self.fs_photos:
            return PhotoIndex.get_by_key_name(self.fs_photos)
        else:
            return None

    @property
    def get_ig_photos(self):
        if self.ig_photos:
            return PhotoIndex.get_by_key_name(self.ig_photos)
        else:
            return None


class PhotoIndex(db.Model):
    photos = db.StringListProperty()

class Photo(db.Model):
    # key is photo id
    key_id = db.StringProperty()
    fs_checkin_id = db.StringProperty()
    photo_url = db.StringProperty()
    med_thumb = db.StringProperty()
    small_thumb = db.StringProperty()
    fs_createdAt = db.DateTimeProperty()
    fs_venue_name = db.StringProperty()
    fs_venue_id = db.StringProperty()
    fs_address = db.StringProperty()
    fs_crossStreet = db.StringProperty()
    fs_city = db.StringProperty()
    fs_state = db.StringProperty()
    fs_country = db.StringProperty()
    shout = db.StringProperty()
    fs_lat = db.FloatProperty()
    fs_lng = db.FloatProperty()
    cat_id = db.StringProperty()
    cat_name = db.StringProperty()
    width = db.IntegerProperty()
    height = db.IntegerProperty()
    link = db.StringProperty()
    ig_pushed_to_fs = db.BooleanProperty(default=False)
    fs_venue_only_photo = db.BooleanProperty(default=False)
    hearted = db.StringListProperty()
    hidden = db.BooleanProperty(default=False)
    trip_parent = db.ReferenceProperty()
    next = db.SelfReferenceProperty()
    trip_indx = db.IntegerProperty()

    @property
    def get_orientation(self):
        if self.width >= self.height:
            return "landscape"
        else:
            return "portrait"

    @property
    def get_offset(self):
        side = 380
        if self.width == self.height:
            return ""
        elif self.width > self.height:
            multiplier = self.width / self.height
            resizedWidth = multiplier * side
            offset = (resizedWidth - side) / 2
            return "margin-left: -" + str(int(offset)) + "px;"
        else:
            multiplier = self.height / self.width
            resizedHeight = multiplier * side
            offset = (resizedHeight - side) / 2
            return "margin-top: -" + str(int(offset)) + "px;"

    @property
    def get_short_offset(self):
        widthSide = 380
        heightSide = 188
        multiplier = self.height / self.width
        resizedHeight = multiplier * widthSide
        offset = (resizedHeight - heightSide) / 2
        return "margin-top: -" + str(int(offset)) + "px;"


    @property
    def get_comments(self):
        logging.info('testtttttttttt')
        commentList = []

        if self.fs_venue_only_photo:
            return commentList

        if self.fs_checkin_id:
            thisUser = self.trip_parent.user_parent
            comments_url = "https://api.foursquare.com/v2/checkins/%s?oauth_token=%s" % (self.fs_checkin_id, thisUser.fs_token)
            comments_json = urlfetch.fetch(comments_url, validate_certificate=False)
            comments_response = simplejson.loads(comments_json.content)

            comments = comments_response['response']['checkin']['comments']
            commentCount = comments['count']

            if commentCount > 0:
                for comment in comments['items']:
                    name = comment['user']['firstName']
                    photo = comment['user']['photo']
                    timestamp = comment['createdAt']
                    text = comment['text']
                    commentList.append({'name':name, 'photo':photo, 'timestamp':timestamp, 'text':text})
        else:
            thisUser = self.trip_parent.user_parent
            comments_url = "https://api.instagram.com/v1/media/%s?access_token=%s" % (self.key_id, thisUser.ig_token)
            comments_json = urlfetch.fetch(comments_url, validate_certificate=False, deadline=10)
            comments_response = simplejson.loads(comments_json.content)

            comments = comments_response['data']['comments']
            commentCount = comments['count']

            if commentCount > 0:
                for comment in comments['data']:
                    name = comment['from']['username']
                    photo = comment['from']['profile_picture']
                    timestamp = comment['created_time']
                    text = comment['text']
                    commentList.append({'name':name, 'photo':photo, 'timestamp':timestamp, 'text':text})

        return commentList


    @property
    def get_like_count(self):
        logging.info('2 testtttttttttt')
        likeCount = 0

        if self.fs_venue_only_photo or self.fs_checkin_id:
            return commentList
        else:
            thisUser = self.trip_parent.user_parent
            comments_url = "https://api.instagram.com/v1/media/%s?access_token=%s" % (self.key_id, thisUser.ig_token)
            comments_json = urlfetch.fetch(comments_url, validate_certificate=False, deadline=10)
            comments_response = simplejson.loads(comments_json.content)

            likes = comments_response['data']['likes']
            likeCount = likes['count']

        return likeCount

    @property
    def get_likes(self):
        logging.info('2 testtttttttttt')
        likeList = []
        likeCount = 0

        if self.fs_venue_only_photo or self.fs_checkin_id:
            return likeList
        else:
            thisUser = self.trip_parent.user_parent
            comments_url = "https://api.instagram.com/v1/media/%s?access_token=%s" % (self.key_id, thisUser.ig_token)
            comments_json = urlfetch.fetch(comments_url, validate_certificate=False, deadline=10)
            comments_response = simplejson.loads(comments_json.content)

            likes = comments_response['data']['likes']
            likeCount = likes['count']

            if 5 > likeCount > 0:
                for like in likes['data']:
                    name = like['username']
                    photo = like['profile_picture']
                    likeList.append({'name':name, 'photo':photo})

        return likeList


class Trip(db.Model):
    # key is the checkin id of the first checkin
    key_id = db.StringProperty()
    user_parent = db.ReferenceProperty()
    photos = db.StringListProperty()
    title = db.StringProperty()
    start_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    start_pt = db.GeoPtProperty()
    latest_pt = db.GeoPtProperty()
    ongoing = db.BooleanProperty(default=False)
    home = db.BooleanProperty()
    count = db.IntegerProperty(default=0)

    @property
    def get_date_range(self):
      logging.info('is this working?')
      currentTime = datetime.datetime.now()
      if currentTime.year == self.start_date.year:
        if self.end_date:
          if self.start_date.date() == self.end_date.date():
            return self.start_date.strftime("%b %d").replace(' 0', ' ')
          elif self.start_date.month == self.end_date.month:
            return self.start_date.strftime("%b %d").replace(' 0', ' ') + " - " + self.end_date.strftime("%d").lstrip('0')
          else:
            return self.start_date.strftime("%b %d").replace(' 0', ' ') + " - " + self.end_date.strftime("%b %d").replace(' 0', ' ')
        else:
          return self.start_date.strftime("%b %d").replace(' 0', ' ') # since...
      else:
        if self.end_date:
          if self.start_date.date() == self.end_date.date():
            return self.start_date.strftime("%b %d, %Y").replace(' 0', ' ')
          if self.start_date.year == self.end_date.year:
            if self.start_date.month == self.end_date.month:
              return self.start_date.strftime("%b %d").replace(' 0', ' ') + " - " + self.end_date.strftime("%d, %Y").lstrip('0')
            else:
              return self.start_date.strftime("%b %d").replace(' 0', ' ') + " - " + self.end_date.strftime("%b %d, %Y").replace(' 0', ' ')
          else:
            return self.start_date.strftime("%b %d, %Y").replace(' 0', ' ') + " - " + self.end_date.strftime("%b %d, %Y").replace(' 0', ' ')
        else:
          return self.start_date.strftime("%b %d, %Y").replace(' 0', ' ') # since...



    @property
    def get_all_photos(self):
        listOfPhotos = []
        thisUser = self.user_parent
        for photoKey in self.photos:
            thisPhoto = Photo.get_by_key_name(photoKey)
            if (not thisPhoto.ig_pushed_to_fs) or (thisUser.ig_id == None):
                if thisPhoto.hidden is False:
                    listOfPhotos.append(thisPhoto)
        if self.home is False and self.ongoing is False:
            listOfPhotos.reverse()
        return listOfPhotos

    @property
    def get_photos_mini(self):
        listOfPhotos = []
        for photo in self.photos:
            if len(listOfPhotos) < 5:
                # should sort em
                listOfPhotos.append(Photo.get_by_key_name(photo))
            else:
                break
        return listOfPhotos

    @property
    def get_mini_user(self):
        thisUser = self.user_parent
        return thisUser
