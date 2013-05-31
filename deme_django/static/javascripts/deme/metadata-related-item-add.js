$(function(){
  $('#metadata_content_related_items').on('contentload', function(){
    $(this).find('.type-related-item-add').each(function(){
      var type = $(this);
      var detail_link = type.find('a');
      var new_modal_url = type.attr('data-new-modal-url');

      // add button
      var newbtn = $('<a href="#" class="btn btn-default btn-small">New</a>').insertAfter(detail_link);
      newbtn.click(function(e){
        e.preventDefault();
        var random_num = Math.floor((Math.random()*1000000)+1);
        window.open(new_modal_url, 'embedform-' + random_num, 'width=400,toolbar=1,resizable=1,scrollbars=yes,height=400,top=100,left=100');
      });
    });
  });
});