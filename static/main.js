var currentPhoto = null;
var currentTrip = null;
var friendsTab = true;
var youNext = 0;
var youDone = false;
var hasRun = false;
var friendNext = 0;
var friendDone = false;
var friendHasRun = false;
var lightboxOpen = false;

$(document).ready(function(){

  if (friendsTab) {
    updateFriendPhotos();
  } else {
    updatePhotos();
  }

  $(window).scroll(function () {
    if (friendsTab) {
      updateFriendPhotos();
    } else {
      updatePhotos();
    }
  });

  $('#friends').click(function() {
    $('#friends').addClass('selected');
    $('#you').removeClass('selected');
    $('#friendPhotos').css({'display':'block'});
    $('#photos').css({'display':'none'});
    friendsTab = true;
    updateFriendPhotos();
    updateLine();
    return false;
  });

  $('#you').click(function() {
    $('#you').addClass('selected');
    $('#friends').removeClass('selected');
    $('#friendPhotos').css({'display':'none'});
    $('#photos').css({'display':'block'});
    friendsTab = false;
    updatePhotos();
    updateLine();
    return false;
  });

  $('html').click(function() {
    $('#menubox').hide();
    if (lightboxOpen) {
      closeLightbox();
    }
  });

  $('#menubox').click(function(event){
    event.stopPropagation();
  });

  $('#menu').click(function(event){
    event.stopPropagation();
    $('#menubox').toggle();
  });
});


$(document).keydown(function(e){

if (e.keyCode == 37) {
  $(currentPhoto).addClass('hidden');
  if ($(currentPhoto).prev().attr("class") == "lightbox hidden") {
    prevPhoto = $(currentPhoto).prev().attr('id');
  } else {
    prevPhoto = $(currentPhoto).parent().children(":last").attr('id');
  }
  currentPhoto = "#" + prevPhoto;
  $(currentPhoto).removeClass('hidden');
  centerLB();
  var photoID = prevPhoto.substring(2);
  getComments(photoID);
  return false;
}

if (e.keyCode == 39) {
  $(currentPhoto).addClass('hidden');
  if ($(currentPhoto).next().attr("class") == "lightbox hidden") {
    nextPhoto = $(currentPhoto).next().attr('id');
  } else {
    nextPhoto = $(currentPhoto).parent().children(":first").attr('id');
  }
  currentPhoto = "#" + nextPhoto;
  $(currentPhoto).removeClass('hidden');
  centerLB();
  var photoID = nextPhoto.substring(2);
  getComments(photoID);
  return false;
}

if (e.keyCode == 27) {
  closeLightbox();
 }
});

function updatePhotos() {
  if (!hasRun) {
    if ($(window).scrollTop() >= $("#photos").height() - $(window).height() - 1000) {
      hasRun = true;
      if (!youDone) {
        $("#loading").toggle();
        updateLine();
        $.ajax({
          url: "/tripLoad?startAt="  + youNext,
          cache: false,
          success: function(html){
            $("#ajax").append(html);
            hasRun = false;
            updateLine();
            $("#loading").toggle();
            if ($(window).scrollTop() >= $("#photos").height() - $(window).height() - 1000) {
              updatePhotos();
            } else {
              if (friendNext < 2) {
                updateFriendPhotos();
              }
            }
          }
        });
        tripIndx = youNext - 1;
        $("#y_trip" + tripIndx).find(".y_photo").click(function() {
          event.stopPropagation();
          var photoID = $(this).attr('id');
          photoID = photoID.substring(2);
          currentPhoto = "#l_" + photoID;
          var thisTrip = $(this).parent().attr('id');
          if (thisTrip != currentTrip) {
            $.ajax({
              url: "/lightboxLoad?photo="  + photoID,
              cache: false,
              success: function(html){
                $("#hide").html(html);
                currentTrip = thisTrip;
                $(currentPhoto).removeClass('hidden');
                $('#hide').removeClass('invisible');
                $('body').addClass('theaterMode');
                getComments(photoID);
                lightboxOpen = true;
                centerLB();
              }
            });
          } else {
            $(currentPhoto).removeClass('hidden');
            $('#hide').removeClass('invisible');
            $('body').addClass('theaterMode');
            getComments(photoID);
            lightboxOpen = true;
            centerLB();
          }
        });
      }
    }
  }
}

function updateFriendPhotos() {
  if (!friendHasRun) {
    if ($(window).scrollTop() >= $("#friendPhotos").height() - $(window).height() - 1000) {
      friendHasRun = true;
      if (!friendDone) {
        updateLine();
        $.ajax({
          url: "/friendTripLoad?startAt="  + friendNext,
          cache: false,
          success: function(html){
            if ($("#rightCol").height() < $("#leftCol").height()) {
              $("#rightCol").append(html);
            } else {
              $("#leftCol").append(html);
            }
            friendHasRun = false;
            friendNext = friendNext + 1;
            updateLine();
            if ($(window).scrollTop() >= $("#friendPhotos").height() - $(window).height() - 1000) {
              updateFriendPhotos();
            } else {
              if (youNext < 2) {
                updatePhotos();
              }
            }
          }
        });

        tripIndx = friendNext - 1;
        $("#f_trip" + tripIndx).find(".f_photo").click(function() {
          event.stopPropagation();
          var photoID = $(this).attr('id');
          photoID = photoID.substring(2);
          currentPhoto = "#l_" + photoID;
          var thisTrip = $(this).parent().attr('id');
          if (thisTrip != currentTrip) {
            $.ajax({
              url: "/lightboxLoad?photo="  + photoID,
              cache: false,
              success: function(html){
                $("#hide").html(html);
                currentTrip = thisTrip;
                $(currentPhoto).removeClass('hidden');
                $('#hide').removeClass('invisible');
                $('body').addClass('theaterMode');
                getComments(photoID);
                lightboxOpen = true;
                centerLB();
                // do this only for this batch
                $('.metaWrap').click(function(event){
                  event.stopPropagation();
                });
                $('.bigWrap').click(function(event){
                  event.stopPropagation();
                });
              }
            });
          } else {
            $(currentPhoto).removeClass('hidden');
            $('#hide').removeClass('invisible');
            $('body').addClass('theaterMode');
            getComments(photoID);
            lightboxOpen = true;
            centerLB();
          }
        });

      }
    }
  }
}

function updateLine() {
  if (friendsTab) {
    $('#line').height($("#friendPhotos").height() - 150);
    $('#bgHack').height($("#friendPhotos").height());
  } else {
    $('#line').height($("#photos").height() - 150);
    $('#bgHack').height($("#photos").height());
  }
}


function closeLightbox() {
  $(currentPhoto).addClass('hidden');
  currentPhoto = null;
  $('#hide').addClass('invisible');
  $('body').removeClass('theaterMode');
  lightboxOpen = false;
  return false;
}

function getComments(photoID) {
  var parent = "#l_" + photoID;
  if ($(parent).find(".comments").length == 0) {
    $(parent).find(".meta .inner").append('<div class="comments"></div>');
    $.ajax({
      url: "/getComments?photo="  + photoID,
      cache: false,
      success: function(html){
        $(parent).find(".comments").append(html);
      }
    });
  }
}

$(window).resize(function() {
  if (lightboxOpen) {
    centerLB();
  }
});

function centerLB() {
  lbHeight = $(currentPhoto).find(".zoomContentWrap").height() + 38;
  if ($(window).height() > lbHeight) {
    paddingCalc = ($(window).height() - lbHeight) / 2;
    paddingCalc = String(paddingCalc) + "px";
    $(currentPhoto).css("padding-top",paddingCalc);
  } else {
    $(currentPhoto).css("padding-top",0);
  }
}