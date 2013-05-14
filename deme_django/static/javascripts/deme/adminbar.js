$.cookie.defaults.path = '/';

// check user agent
var ua = navigator.userAgent;
var checker = {
  iphone: ua.match(/(iPhone|iPod)/),
  ipad: ua.match(/(iPad)/),
  blackberry: ua.match(/BlackBerry/),
  android: ua.match(/Android/),
  ie: ua.match(/MSIE/)
};

if (checker.android) {
  $('html').addClass('ua-android');
}

$(function(){
  // if actions menu is empty, remove it
  if ($.trim($('#actions-btn .actions-menu').text()) == '') {
    $('#actions-btn').remove();
  }

  $('.textsize-btn a').click(function(e){
    e.preventDefault();
    hideAdminbarIfMobile(this);
  });

  // attach focus to search button
  $('.search-btn a').click(function(e){
    e.preventDefault();
    hideAdminbarIfMobile(this);
    $dropdown = $(this).closest('.dropdown');
    setTimeout(function(){
      $dropdown.find('input.search_box').focus();
    }, 1);
  });

  function hideAdminbarIfMobile(elem) {
    if(checker.iphone || checker.ipad) {
      setAdminbar(false);
      if ($(elem).closest('.dropdown').hasClass('open')) {

      } else {
        setTimeout(function(){
          // we are swtiching dom structurs so we need to find out what dropdown to show on the new navbar
          var classes = $(elem).closest('.dropdown').attr('class').split(' ');
          var classSelector = '';
          var ignoreList = ['open'];
          for (var i = 0; i < classes.length; i++) {
            var testClass = classes[i];
            if ($.inArray(testClass, ignoreList) === -1) {
              classSelector += '.' + testClass;
            }
          }
          $(classSelector).addClass('open');
        }, 1);
      }
    }
  }

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

  // show/hide advanced adminbar
  function setAdminbar(visible) {
    // check to make sure there is an admin bar
    var adminbar = $('.adminbar:not(.nonadminbar)');
    if (adminbar.length == 0) {
      $('body').addClass('nonadmin');
    } else {
      if (visible) {
        $('body').removeClass('nonadmin');
        $.cookie('ADMINBAR_VISIBLE', true);
        $('.adminbar a.advanced').addClass('active');
      } else {
        $('body').addClass('nonadmin');
        $.removeCookie('ADMINBAR_VISIBLE');
        $('.page-layout').css('max-width', '');
        $('.adminbar a.advanced').removeClass('active');
      }
    }
  }
  var visible = $.cookie('ADMINBAR_VISIBLE');
  if (visible) {
    setAdminbar(visible);
  } else {
    setAdminbar(false);
  }
  $('.adminbar a.advanced').click(function(e){
    e.preventDefault();
    if ($(this).closest('.nonadminbar').length) {
      setAdminbar(true);
    } else {
      setAdminbar(false);
    }
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
