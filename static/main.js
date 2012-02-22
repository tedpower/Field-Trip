var currentPhoto = null;
var friendsTab = false;
var youNext = 0;
var youDone = false;
var hasRun = false;
var friendNext = 0;
var friendDone = false;
var friendHasRun = false;

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
    $('#photoWrap').addClass('flipped');
    friendsTab = true;
    updateLine();
    updateFriendPhotos();
    return false;
  });
  $('#you').click(function() {
    $('#you').addClass('selected');
    $('#friends').removeClass('selected');
    $('#photoWrap').removeClass('flipped');
    friendsTab = false;
    updateLine();
    return false;
  });

  $('html').click(function() {
    $('#menubox').hide();
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
  prevPhoto = $(currentPhoto).prev().attr('id');
  currentPhoto = "#" + prevPhoto;
  $(currentPhoto).removeClass('hidden');
  return false;

 }

 if (e.keyCode == 39) {
   if ($(currentPhoto).next().attr('id') != 'end') {
    $(currentPhoto).addClass('hidden');
    nextPhoto = $(currentPhoto).next().attr('id');
    currentPhoto = "#" + nextPhoto;
    $(currentPhoto).removeClass('hidden');
    return false;
  }
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
        currentTrip = youNext - 1;
        $("#trip" + currentTrip).find(".photo").click(function() {
          // currentPhoto = "#l" + $(this).attr('id');
          // $(currentPhoto).removeClass('hidden');

          $.ajax({
            url: "/lightboxLoad?photo="  + $(this).attr('id'),
            cache: false,
            success: function(html){
              $("#hide").html(html);
              $('#hide').removeClass('invisible');
              $('body').addClass('theaterMode');
            }
          });

        });
        $("#hide").click(function() {
          // $(this).addClass('hidden');
          // currentPhoto = null;
          $('#hide').addClass('invisible');
          $('body').removeClass('theaterMode');
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
        // $("#friendLoading").toggle();
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
            // $("#friendLoading").toggle();
            if ($(window).scrollTop() >= $("#friendPhotos").height() - $(window).height() - 1000) {
              updateFriendPhotos();
            } else {
              if (youNext < 2) {
                updatePhotos();
              }
            }
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
  return false;
}
