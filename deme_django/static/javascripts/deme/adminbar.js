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
});
