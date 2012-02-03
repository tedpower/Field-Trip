var currentPhoto = null;
var hasRun = false;
var friendsTab = false;
var youNext = 0;

$(document).ready(function(){

  console.log('test');

  $(window).scroll(function () {
    if (friendsTab) {
      if (!hasRun) {
        updateFriendPhotos();
      }
    } else {
      if (!hasRun) {
        updatePhotos();
      }
    }
  });

  if (friendsTab) {
    if ($(window).scrollTop() >= $("#friendPhotos").height() - $(window).height() - 1000) {
      updatePhotos();
    }
  } else {
    if ($(window).scrollTop() >= $("#photos").height() - $(window).height() - 1000) {
      updatePhotos();
    }
  }

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
  prevPhoto = $(currentPhoto).prevAll('.lightbox').first().attr('id');
  if (!prevPhoto) {
    prevTrip = $(currentPhoto).parent().parent().prev();
    if (prevTrip.children('.tripPhotos').length == 0) {
      console.log('hey');
      closeLightbox();
      return false;
    }
    prevPhoto = prevTrip.children('.tripPhotos').children('.lightbox').last().attr('id');
  }
  currentPhoto = "#" + prevPhoto;
  $(currentPhoto).removeClass('hidden');
  return false;

 }

 if (e.keyCode == 39) {
   if ($(currentPhoto).next().attr('id') != 'end') {
    $(currentPhoto).addClass('hidden');
    nextPhoto = $(currentPhoto).nextAll('.lightbox').first().attr('id');
    if (!nextPhoto) {
      nextTrip = $(currentPhoto).parent().parent().next();
      if (nextTrip.children('.tripPhotos').length == 0) {
        console.log('hey');
        closeLightbox(); // load more
        return false;
      }
      nextPhoto = nextTrip.children('.tripPhotos').children('.lightbox').first().attr('id');
    }
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
  if ($(window).scrollTop() >= $("#photos").height() - $(window).height() - 1000) {
    $("#loading").toggle();
    updateLine();
    $.ajax({
      url: "/tripLoad?startAt="  + youNext,
      cache: false,
      success: function(html){
        $("#ajax").replaceWith(html);
        hasRun = false;
        youNext = youNext + 1;
        updateLine();
      }
    });
    hasRun = true;
    currentTrip = youNext - 1;
    $("#trip" + currentTrip).find(".photo").click(function() {
      currentPhoto = "#l" + $(this).attr('id');
      $(currentPhoto).removeClass('hidden');
      $('#hide').removeClass('invisible');
      $('body').addClass('theaterMode');
    });
    $("#trip" + currentTrip).find(".lightbox").click(function() {
      $(this).addClass('hidden');
      currentPhoto = null;
      $('#hide').addClass('invisible');
      $('body').removeClass('theaterMode');
    });
  }
}

function updateFriendPhotos() {
  if ($(window).scrollTop() >= $("#friendPhotos").height() - $(window).height() - 1000) {
    $("#friendLoading").toggle();
    var nextTrip = $('#friendNext').text();
    $.ajax({
      url: "/friendTripLoad?startAt="  + nextTrip,
      cache: false,
      success: function(html){
        $("#friendAjax").replaceWith(html);
      }
    });
    hasRun = true;
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
