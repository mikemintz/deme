$(function(){
  $('a.sidebar-toggle').click(function(e){
    e.preventDefault();
    $('body').toggleClass('nomobilesidebar');
  });
});