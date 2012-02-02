var currentPhoto = null;
var hasRun = false;

function updatePhotos() {
  if ($(window).scrollTop() >= $("#photos").height() - $(window).height() - 1000) {
    $("#loading").toggle();
    var nextTrip = $('#next').text();
    $.ajax({
      url: "/tripLoad?startAt="  + nextTrip,
      cache: false,
      success: function(html){
        $("#ajax").replaceWith(html);
      }
    });
    hasRun = true;
    currentTrip = Number(nextTrip) - 1;
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

function updateLine() {
  $('#line').height($("#photos").height() - 150);
  $('#bgHack').height($("#photos").height());
}

function updateFriendPhotos() {
  if ($(window).scrollTop() >= $("#photos").height() - $(window).height() - 1000) {
    $("#loading").toggle();
    var nextTrip = $('#next').text();
    $.ajax({
      url: "/friendTripLoad?startAt="  + nextTrip,
      cache: false,
      success: function(html){
        $("#ajax").replaceWith(html);
      }
    });
    hasRun = true;
    currentTrip = Number(nextTrip) - 1;
    $("#trip" + currentTrip).find(".friendPhoto").click(function() {
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

function closeLightbox() {
  $(currentPhoto).addClass('hidden');
  currentPhoto = null;
  $('#hide').addClass('invisible');
  $('body').removeClass('theaterMode');
  return false;
}

$(document).ready(function(){

  $('#friends').click(function() {
    $('#friends').addClass('selected');
    $('#you').removeClass('selected');
    $('#photoWrap').addClass('flipped');
    $('#line').height(100);
    return false;
  });
  $('#you').click(function() {
    $('#you').addClass('selected');
    $('#friends').removeClass('selected');
    $('#photoWrap').removeClass('flipped');
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
});