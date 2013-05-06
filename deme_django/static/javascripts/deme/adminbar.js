$.cookie.defaults.path = '/';

$(function(){
  // if actions menu is empty, remove it
  if ($.trim($('#actions-btn .actions-menu').text()) == '') {
    $('#actions-btn').remove();
  }

  // attach focus to search button
  $('.search-btn a').click(function(){
    $dropdown = $(this).closest('.dropdown');
    setTimeout(function(){
      $dropdown.find('input.search_box').focus();
    }, 1);
  });

  var defaultFontSize = 14;
  var validFontSizes = [8,9,10,12,14,16,18,20,24,30];

  // user set text size
  function resizeTextDelta(delta) {
    // have a list of preset font sizes, probably something like 10 of them. circulate amongst those.
    if (document.body.style.fontSize == "") {
      document.body.style.fontSize = defaultFontSize + "px";
    }
    current_size = parseFloat(document.body.style.fontSize);
    pos = validFontSizes.indexOf(current_size);
    default_pos = validFontSizes.indexOf(defaultFontSize);
    if (pos < 0 || delta == 0) {
      pos = default_pos;
    }
    pos = pos + delta;
    if (pos <= 0) {
      pos = 0;
    }
    if (pos >= validFontSizes.length) {
      pos = validFontSizes.length - 1;
    }
    var size = validFontSizes[pos] + 'px';
    $.cookie('ADMINBAR_TEXTSIZE_SIZE', size);
    resizeText(size);
  }

  function resizeText(size) {
    $('.textsize-btn').addClass('resized');
    if (parseFloat(size) == defaultFontSize) {
      $('.textsize-btn').removeClass('resized');
    }
    document.body.style.fontSize = size;
  }

  window.resizeText = resizeText;
  // load font size
  var size = $.cookie('ADMINBAR_TEXTSIZE_SIZE');
  if (size) {
    resizeText(size);
  }
  $('.textsize-btn .btn').click(function(e){
    e.preventDefault();
    e.stopPropagation();
    var delta = 0;
    if ($(this).hasClass('smaller')) {
      delta = -1;
    } else if ($(this).hasClass('bigger')) {
      delta = 1;
    }
    resizeTextDelta(delta);
  });

  // set up create, edit, and comment buttons based on existing markup elsewhere
  function linkOrRemove(dependent, target) {
    if (target.length > 0) {
      dependent.click(function(e){
        e.preventDefault();
        if (target.attr('href') == '#') {
          target.click();
        } else {
          window.location = target.attr('href');
        }
      });
    } else {
      dependent.remove();
    }
  }
  linkOrRemove($('.actions-wrap > li > a.create'), $('.actions-menu a.create'));
  linkOrRemove($('.actions-wrap > li > a.edit'), $('.actions-menu a.edit'));

});
