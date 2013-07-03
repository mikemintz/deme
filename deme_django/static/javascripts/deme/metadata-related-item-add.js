$(function(){
  $('#metadata_content_related_items').on('contentload', function(){
    // add toggle to top of section
    content_section = $(this);
    title = content_section.find('h3').first();
    toggleButtons = $('<div class="btn-group btn-group-justified metadata_content_related_items_switcher_wrap" data-toggle="buttons-radio"><label class="btn btn-small btn-info active"><input type="radio" name="metadata_content_related_items_switcher" value="existing" checked="checked"> Existing</label><label class="btn btn-small btn-info"><input type="radio" name="metadata_content_related_items_switcher" value="all"> All</label></div>').insertAfter(title);

    toggleButtons.find('input').change(function(e){
      toggleButtonChange();
    });

    function toggleButtonChange() {
      if ($("input[name='metadata_content_related_items_switcher']:checked").val() == 'all') {
        content_section.find('.relationship').show();
      } else {
        content_section.find('.relationship').each(function(){
          if ($(this).find('.type-related-item-add').first().attr('data-count') == 0) {
            $(this).hide();
            $(this).addClass('empty');
          }
        });
      }
    }
    toggleButtonChange();

    // append add buttons
    content_section.find('.type-related-item-add').each(function(){
      var type = $(this);
      var action_wrap = type.find('.action-wrap');
      var new_modal_url = type.attr('data-new-modal-url');

      // add button
      var newbtn = $('<a href="#" class="newbtn btn btn-info btn-small" title="New Item"><i class="glyphicon glyphicon-plus"></i></a>').appendTo(action_wrap);
      newbtn.click(function(e){
        e.preventDefault();
        var random_num = Math.floor((Math.random()*1000000)+1);
        window.open(new_modal_url, 'embedform-' + random_num, 'width=400,toolbar=1,resizable=1,scrollbars=yes,height=500,top=100,left=100');
      });
    });
  });
});