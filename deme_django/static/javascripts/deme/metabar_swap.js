$.cookie.defaults.path = '/';

$(function(){
  var METABAR_RESIZE_STEP = 50;
  var $metabar = $('#metabar');
  var metabar_width = min_metabar_width = 150; // minimum/default width
  var max_metabar_width = 800;

  // sets metabar sizing styles based on window dimensions
  function metabar_sizing(){
    $metabar.css('min-height', 0);
    $metabar.css('height', 0);
    var height = $(document).height();
    $metabar.css('min-height', height);
    $metabar.css('height', 'auto');
  }

  var winWidth = $(window).width(),
      winHeight = $(window).height();

  $(window).resize(function(){
      var onResize = function() {
          //The method which sets the LEFT css property which triggers 
          //window.resize again and it was a infinite loop
          metabar_sizing(); metabarWidthAdjust();
      }

      //New height and width
      var winNewWidth = $(window).width(),
      winNewHeight = $(window).height();

      // compare the new height and width with old one
      if(winWidth!=winNewWidth || winHeight!=winNewHeight)
      {
          window.clearTimeout(resizeTimeout);
          resizeTimeout = window.setTimeout(onResize, 10);
      }
      //Update the width and height
      winWidth = winNewWidth;
      winHeight = winNewHeight;
  }).trigger('resize');

  // attach resizable to entire metabar
  $metabar.resizable({
    minWidth: min_metabar_width,
    maxWidth: max_metabar_width,
    handles: 'w',
    start: function() {
      $metabar.addClass('noanim');
    },
    stop: function(ev, ui) {
      $metabar.removeClass('noanim');
      var width = ui.size.width;
      setMetabarWidth(width);
    }
  });

  // setter for width
  function setMetabarWidth(width) {
    var max_width = max_metabar_width;
    var window_width = $(window).width() *.75; // can't be wider than 75% of screen
    if (window_width < max_width) {
      max_width = window_width;
    }
    if (width < min_metabar_width) {
      width = min_metabar_width;
    }
    if (width > max_width) {
      width = max_width;
    }
    // save cookie
    $.cookie('METABAR_WIDTH', width);
    metabarWidthAdjust(width);
    metabar_width = width;
  }

  // attach events to width changing buttons
  $('#metabar').on('click', 'button.resize', function(e){
    var new_width = metabar_width * 1.0 - METABAR_RESIZE_STEP;
    if ($(this).hasClass('resize-left')) {
      new_width = metabar_width * 1.0 + METABAR_RESIZE_STEP;
    }
    setMetabarWidth(new_width);
  });

  // load metabar width from cookie
  var past_width = $.cookie('METABAR_WIDTH');
  if (past_width) {
    setMetabarWidth(past_width);
  }

  // show/hide meta bar
  function toggleMetabar(dir) {
    if (typeof(dir) == 'undefined') {
      $metabar.toggleClass('closed');
    } else if (dir == 'close') {
      $metabar.addClass('closed');
    } else {
      $metabar.removeClass('closed');
    }
    if ($metabar.hasClass('closed')) {
      $('a.metabar-toggle').removeClass('active');
      $.removeCookie('METABAR_VISIBLE');
    } else {
      $('a.metabar-toggle').addClass('active');
      $.cookie('METABAR_VISIBLE', true);
    }
    metabarWidthAdjust(metabar_width);
  }

  // adjust width of container to take into account metadata width
  function metabarWidthAdjust(metabar_width) {
    var page_layout_width = '';
    if (typeof(metabar_width) == 'undefined') {
      metabar_width = $metabar.width();
    }
    // if visible, then calculate
    if (!$('body').hasClass('nonadmin') && !$metabar.hasClass('closed')) {
      page_layout_width = $(window).width() - metabar_width + 'px';
    }
    $metabar.css('width', metabar_width);
    $('#overall').css('max-width', page_layout_width);
  }
  window.metabarWidthAdjust = metabarWidthAdjust;

  // attach event to adminbar
  $('.metabar-toggle').click(function(e){
    e.preventDefault();
    toggleMetabar();
  });

  function loadMetabarVisibility() {
    // set open/close state on cookie
    if ($.cookie('METABAR_VISIBLE')) {
      toggleMetabar('open');
    } else {
      toggleMetabar('close');
    }
  }
  loadMetabarVisibility();

  // click on buttons to get to different sections
  $('.btn-section').click(function(e){
    e.preventDefault();
    var id = $(this).attr('data-target');
    metabar_show_section($('#' + id));
  })

  function metabar_show_section(collapse, cb) {
    $metabar.find('.block').addClass('hide');
    collapse.removeClass('hide');
    // if not metabar, then add button
    if (collapse.attr('id') != 'metadata_content_item_details') {
      $metabar.find('.btn-metadata').removeClass('hide');
    } else {
      $metabar.find('.btn-metadata').addClass('hide');
    }
    // remember what we showed
    var name = collapse.attr('id');
    $.cookie('METABAR_SECTION', name);
    metabar_load_section(collapse, function(collapse){
      if (typeof cb === "function") {
        cb();
      }
      toggleMetabar('open');
    });
  }
  window.metabar_show_section = metabar_show_section;

  var initial_section = $.cookie('METABAR_SECTION');
  if (initial_section) {
    metabar_show_section($('#' + initial_section));
  } else {
    metabar_show_section($('#metadata_content_item_details'));
  }

  function metabar_load_section(collapse, cb) {
    if (collapse.length == 0) return;
    if (!collapse.hasClass('ajax-loaded')) {
      var name = collapse.attr('id').replace('metadata_content_', '');
      var url = metabar_ajax_url(name);
      collapse.find('.content').html('Loading&hellip;');
      $.ajax({
        url: url,
        success: function(data) {
          collapse.addClass('ajax-loaded');
          collapse.find('.content').html(data);
          collapse.trigger('contentload');
          if ($('body').hasClass('nonadmin')) {
            collapse.css('height', 'auto');
          }
          if (typeof(cb) == 'function') {
            cb(collapse);
          }
        }
      })
    } else {
      if (typeof(cb) == 'function') {
        cb(collapse);
      }
    }
  }

  // set up related items button
  $('.metadata_activate_related_items').click(function(e){
    e.preventDefault();
    // open metadata menu
    toggleMetabar('open');
    // load and open related items in metadata
    metabar_show_section($("#metadata_content_related_items"));
  });

  // set up comment button
  $('.actions-wrap > li > a.comment, .actions-menu a.comment').click(function(e){
    e.preventDefault();
    // open metadata menu
    toggleMetabar('open');
    // if is navbar button and toolbar already on correct section, open new comment
    var $comments = $('#metadata_content_comments');
    if ($comments.hasClass('ajax-loaded') && !$comments.hasClass('hide')) {
      openCommentDialog('comment3');
    }
    // load and open comments in metadata
    metabar_show_section($("#metadata_content_comments"));
  });

  // set up permissions button
  $('.actions-wrap > li > a.permissions, .actions-menu a.permissions').click(function(e){
    e.preventDefault();
    // open metadata menu
    toggleMetabar('open');
    // load and open comments in metadata
    metabar_show_section($("#metadata_content_permissions"));
  });

  setTimeout(function(){
    // don't animate initial stuff
    $metabar.removeClass('noanim');
  }, 100);
});
