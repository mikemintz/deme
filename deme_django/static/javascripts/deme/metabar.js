$(function(){
  var $metabar = $('#metabar');

  // sets metabar sizing styles based on window dimensions
  function metabar_sizing(){
    $metabar.css('min-height', $(window).height());
  }
  $(window).resize(function(){ metabar_sizing(); });
  metabar_sizing();

  // attach resizable
  $metabar.resizable({
    minWidth: 200,
    handles: 'w',
    start: function() {
      $metabar.addClass('noanim');
    },
    stop: function() {
      $metabar.removeClass('noanim');
    }
  });
});
