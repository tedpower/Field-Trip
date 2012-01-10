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
  }
}

$(document).ready(function(){

  var hasRun = false;

  var currentPhoto = null;

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
         if ($(currentPhoto).prev().attr('id') != 'hide') {
            $(currentPhoto).addClass('hidden');
            currentPhoto = "#" + $(currentPhoto).prev().attr('id');
            $(currentPhoto).removeClass('hidden');
            return false;
        }
     }
     if (e.keyCode == 39) {
         if ($(currentPhoto).next().attr('id') != 'end') {
            $(currentPhoto).addClass('hidden');
            currentPhoto = "#" + $(currentPhoto).next().attr('id');
            $(currentPhoto).removeClass('hidden');
            return false;
        }
     }
     if (e.keyCode == 27) {
        $(currentPhoto).addClass('hidden');
        currentPhoto = null;
        $('#hide').addClass('invisible');
        $('body').removeClass('theaterMode');
        return false;
     }
 });
});