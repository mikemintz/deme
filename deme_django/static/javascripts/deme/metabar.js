$.cookie.defaults.path = '/';

$(function(){
  var $metabar = $('#metabar');
  var metabar_width = 200;

  // sets metabar sizing styles based on window dimensions
  function metabar_sizing(){
    $metabar.css('min-height', $(window).height());
  }
  $(window).resize(function(){ metabar_sizing(); metabarWidthAdjust(); });
  metabar_sizing();

  // attach resizable to entire metabar
  $metabar.resizable({
    minWidth: metabar_width,
    handles: 'w',
    start: function() {
      $metabar.addClass('noanim');
    },
    stop: function(ev, ui) {
      $metabar.removeClass('noanim');
      var width = ui.size.width;
      metabar_width = width;
      // save cookie
      $.cookie('METABAR_WIDTH', width);
      metabarWidthAdjust(metabar_width);
    }
  });

  var past_width = $.cookie('METABAR_WIDTH');
  if (past_width) {
    metabar_width = past_width;
    $metabar.css('width', past_width);
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
    var width = '';
    if (typeof(metabar_width) == 'undefined') {
      metabar_width = $metabar.width();
    }
    // if visible, then calculate
    if (!$metabar.hasClass('closed')) {
      width = $(window).width() - metabar_width - 10 + 'px'; // buffer
    }
    $('.page-layout').css('max-width',width)
  }

  // attach event to adminbar
  $('.metabar-toggle').click(function(e){
    e.preventDefault();
    toggleMetabar();
  });

  // set open/close state on cookie
  if ($.cookie('METABAR_VISIBLE')) {
    toggleMetabar('open');
  } else {
    toggleMetabar('close');
  }

  // attach opening/closing of metadata sections
  $metabar.on('show', '.section .collapse', function(){
    metabar_load_section($(this));
    // set cookie to remember this particular section was open
    var name = $(this).attr('id').replace('metadata_content_', '');
    $.cookie('METABAR_SECTION_' + name, true);
  });

  $metabar.on('hide', '.section .collapse', function(){
    // unset cookie to open this section
    var name = $(this).attr('id').replace('metadata_content_', '');
    $.removeCookie('METABAR_SECTION_' + name);
  });

  // on load, open up all visible sections if is set
  $metabar.find('.section .collapse').each(function(){
    var name = $(this).attr('id').replace('metadata_content_', '');
    if ($.cookie('METABAR_SECTION_' + name)) {
      metabar_show_section($(this))
    }
  });

  function metabar_show_section(collapse) {
    metabar_load_section(collapse, function(collapse){
      collapse.collapse('show');
      // manually remove "collapsed" from link
      collapse.closest('.section').find('.header').removeClass('collapsed');
    });
  }
  window.metabar_show_section = metabar_show_section;

  function metabar_load_section(collapse, cb) {
    if (!collapse.hasClass('ajax-loaded')) {
      var name = collapse.attr('id').replace('metadata_content_', '');
      var url = metabar_ajax_url(name);
      collapse.find('.content').html('Loading&hellip;');
      $.ajax({
        url: url,
        success: function(data) {
          collapse.find('.content').html(data);
          if (typeof(cb) == 'function') {
            cb(collapse);
          }
        }
      })
      collapse.addClass('ajax-loaded');
    }
  }


  // set up comment button
  $('.actions-wrap > li > a.comment, .actions-menu a.comment').click(function(){
    // open metadata menu
    toggleMetabar('open');
    // load and open comments in metadata
    metabar_show_section($("#metadata_content_comments"));
  });
});
