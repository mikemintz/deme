$(function(){
  var $metabar = $('#metabar');

  // sets metabar sizing styles based on window dimensions
  function metabar_sizing(){
    $metabar.css('min-height', $(window).height());
  }
  $(window).resize(function(){ metabar_sizing(); });
  metabar_sizing();

  // attach resizable to entire metabar
  $metabar.resizable({
    minWidth: 200,
    handles: 'w',
    start: function() {
      $metabar.addClass('noanim');
    },
    stop: function(ev, ui) {
      $metabar.removeClass('noanim');
      var width = ui.size.width;
      // save cookie
      $.cookie('METABAR_WIDTH', width);
    }
  });

  var past_width = $.cookie('METABAR_WIDTH');
  if (past_width) {
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
  $metabar.on('click', '.section button.header', function(){
    metabar_load_section($(this));
  });

  function metabar_load_section($this) {
    if (!$this.hasClass('ajax-loaded')) {
      var target = $this.attr('data-target');
      var name = target.replace('#metadata_content_', '');
      var url = metabar_ajax_url(name);
      $this.next('.collapse').html('Loading&hellip;');
      $.ajax({
        url: url,
        success: function(data) {
          $this.next('.collapse').html(data);
        }
      })
      $this.addClass('ajax-loaded');
    }
  }
});
