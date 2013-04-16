$.cookie.defaults.path = '/';

$(function(){
  // if actions menu is empty, remove it
  if ($.trim($('#actions-btn .actions-menu').text()) == '') {
    $('#actions-btn').remove();
  }

  // attach focus to search button
  $('#search-btn a').click(function(){
    setTimeout(function(){
      $('#search_box').focus();
    }, 1);
  });

  // user set text size
  function resizeText(delta) {
    // TODO: have a list of preset font sizes, probably something like 10 of them. circulate amongst those.
    if (document.body.style.fontSize == "") {
      document.body.style.fontSize = "14px";
    }
    var size = parseFloat(document.body.style.fontSize) + (delta) + "px";
    document.body.style.fontSize = size;
    $.cookie('ADMINBAR_TEXTSIZE_SIZE', size);
  }
  window.resizeText = resizeText;
  // load font size
  var size = $.cookie('ADMINBAR_TEXTSIZE_SIZE');
  if (size) {
    document.body.style.fontSize = size;
  }
  $('#textsize-btn .btn').click(function(e){
    e.preventDefault();
    e.stopPropagation();
    var delta = 1;
    if ($(this).hasClass('smaller')) {
      delta = -1;
    }
    resizeText(delta);
  });

});
