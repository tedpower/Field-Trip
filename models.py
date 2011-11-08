from google.appengine.ext import db
import datetime


class FS_User(db.Model):
    # Contains the user to foursquare_id + oauth token mapping
    # the key is currently the token, but shouldn't be
    token = db.StringProperty()
    ig_token = db.StringProperty()
    fs_id = db.StringProperty()
    fs_firstName = db.StringProperty()
    fs_lastName = db.StringProperty()
    fs_email = db.EmailProperty()
    fs_homeCity = db.StringProperty()
    homeCityLat = db.FloatProperty()
    homeCityLng = db.FloatProperty()
    radius = db.IntegerProperty(default=30)
    fs_photos = db.StringListProperty()
    ig_photos = db.StringListProperty()
    photoCount = db.IntegerProperty()
    trips = db.StringListProperty()
    twitter = db.StringProperty()
    last_updated = db.DateTimeProperty(auto_now_add=True)
    updated = db.BooleanProperty(default=False)

    @property
    def get_all_photos(self):
        listOfPhotos = []
        for photoKey in self.fs_photos:
            listOfPhotos.append(FS_Photo.get_by_key_name(photoKey))
        return listOfPhotos
    
    @property
    def get_all_ig_photos(self):
        listOfPhotos = []
        for photoKey in self.ig_photos:
            listOfPhotos.append(IG_Photo.get_by_key_name(photoKey))
        return listOfPhotos

    @property
    def get_all_trips(self):
        listOfTrips = []
        for tripKey in self.trips:
            listOfTrips.append(Trip.get_by_key_name(tripKey))
        return listOfTrips

class FS_Photo(db.Model):
    # A foursquare place, with the list of people who've been there
    # key is photo id
    fs_id = db.StringProperty()
    fs_checkin_id = db.StringProperty()
    photo_url = db.StringProperty()
    fs_300 = db.StringProperty()
    fs_100 = db.StringProperty()
    fs_createdAt = db.DateTimeProperty()
    fs_venue_name = db.StringProperty()
    fs_venue_id = db.StringProperty()
    fs_address = db.StringProperty()
    fs_crossStreet = db.StringProperty()
    fs_city = db.StringProperty()
    fs_state = db.StringProperty()
    fs_country = db.StringProperty()
    fs_shout = db.StringProperty()
    fs_lat = db.FloatProperty()
    fs_lng = db.FloatProperty()
    cat_id = db.StringProperty()
    cat_name = db.StringProperty()
    width = db.IntegerProperty()
    height = db.IntegerProperty()
    portrait = db.BooleanProperty(default=False)

class IG_Photo(db.Model):
    photo_url = db.StringProperty()
    ig_createdAt = db.DateTimeProperty()
    
class Trip(db.Model):
    # key is the checkin id of the first checkin
    photos = db.StringListProperty()
    title = db.StringProperty()
    start_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    ongoing = db.BooleanProperty(default=False)
    home = db.BooleanProperty(default=True)

    @property
    def get_all_photos(self):
        listOfPhotos = []
        for photoKey in self.photos:
            listOfPhotos.append(FS_Photo.get_by_key_name(photoKey))
        if self.home == False:
            listOfPhotos.reverse()
        return listOfPhotos
