$(function(){
  // show/hide meta bar
  $('.adminbar a.metadata').click(function(e){
    e.preventDefault();
    $('#metabar').toggleClass('closed');
  });

});