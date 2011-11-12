$(document).ready(function(){

    var currentPhoto = null;
    
    $("#logout").click(function(){
    	$.cookies.del('corpoCookie');
        window.location.href = "/";
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
    
    $(".photo").click(function() {
        currentPhoto = "#l" + $(this).attr('id');
        $(currentPhoto).removeClass('hidden');
        $('#hide').removeClass('invisible');
        $('body').addClass('theaterMode');
    });
    
    $(".lightbox").click(function() {
        $(this).addClass('hidden');
        currentPhoto = null;
        $('#hide').addClass('invisible');
        $('body').removeClass('theaterMode');
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
 // 
 // $(window).scroll(function () { 
 //     if ($(window).scrollTop() >= $(document).height() - $(window).height() - 10) {
 //           alert('at bottom');
 //     }
 // });
});