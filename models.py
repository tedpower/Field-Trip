from google.appengine.ext import db
import datetime

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
    trips = db.StringListProperty()
    friends_trips = db.StringListProperty()
    twitter = db.StringProperty()
    last_updated = db.DateTimeProperty(auto_now_add=True)
    complete_stage = db.IntegerProperty()
    ongoingTrip = db.StringProperty()
    lastTripWithPhotos = db.StringProperty()

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

    @property
    def get_all_trips(self):
        listOfTrips = []
        for tripKey in self.trips:
            listOfTrips.append(Trip.get_by_key_name(tripKey))
        return listOfTrips


class PhotoIndex(db.Model):
    photos = db.StringListProperty()

class Photo(db.Model):
    # key is photo id
    key_id = db.StringProperty()
    fs_checkin_id = db.StringProperty()
    photo_url = db.StringProperty()
    fs_300 = db.StringProperty()
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
    hearted = db.StringListProperty()
    hidden = db.BooleanProperty(default=False)
    trip_parent = db.ReferenceProperty()

class Trip(db.Model):
    # key is the checkin id of the first checkin
    key_id = db.StringProperty()
    user_id = db.StringProperty()
    photos = db.StringListProperty()
    title = db.StringProperty()
    start_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    ongoing = db.BooleanProperty(default=False)
    home = db.BooleanProperty()

    @property
    def get_all_photos(self):
        listOfPhotos = []
        thisUser = User.get_by_key_name(self.user_id)
        for photoKey in self.photos:
            thisPhoto = Photo.get_by_key_name(photoKey)
            if (not thisPhoto.ig_pushed_to_fs) or (thisUser.ig_id == None):
                if thisPhoto.hidden is False:
                    listOfPhotos.append(thisPhoto)
        if self.home is False and self.ongoing is False:
            listOfPhotos.reverse()
        if len(listOfPhotos) == 0:
            return False
        else:
            return listOfPhotos

    @property
    def get_photos_mini(self):
        thisUser = User.get_by_key_name(self.user_id)
        thisPhoto = Photo.get_by_key_name(self.photos[0])
        return thisPhoto

        # maxPhotos = 5
        # thisUser = User.get_by_key_name(self.user_id)
        # totalPhotos = 0
        # listOfPhotos = []
        # for photoKey in self.photos:
        #     thisPhoto = Photo.get_by_key_name(photoKey)
        #     if (not thisPhoto.ig_pushed_to_fs) or (thisUser.ig_id == None):
        #         if thisPhoto.hidden is False:
        #             if len(listOfPhotos) <= maxPhotos:
        #                 listOfPhotos.append(thisPhoto)
        #             totalPhotos += 1

        # if self.home is False and self.ongoing is False:
        #     listOfPhotos.reverse()

        # remainingPhotos = totalPhotos - maxPhotos

        # tripWidth = None
        # if totalPhotos == 1:
        #     tripWidth = 164
        # elif 1 < totalPhotos < 4:
        #     tripWidth = 246
        # elif 3 < totalPhotos < 6:
        #     tripWidth = 328
        # elif 5 < totalPhotos < 8:
        #     tripWidth = 410
        # elif 7 < totalPhotos < 10:
        #     tripWidth = 492
        # elif 9 < totalPhotos < 12:
        #     tripWidth = 574
        # elif 11 < totalPhotos < 14:
        #     tripWidth = 656
        # elif 13 < totalPhotos < 16:
        #     tripWidth = 738
        # elif totalPhotos > 15:
        #     tripWidth = 820

        # if remainingPhotos > 1:
        #     listOfPhotos.pop()

        # if totalPhotos == 0:
        #     return False
        # else:
        #     return (listOfPhotos, remainingPhotos, tripWidth)

    @property
    def get_mini_user(self):
        thisUser = User.get_by_key_name(self.user_id)
        return thisUser
