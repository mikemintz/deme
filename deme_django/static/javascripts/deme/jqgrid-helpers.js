$(function(){
  // watch for the window resizing, then resize all jqgrids on page
  $(window).resize(function(){
    $('.ui-jqgrid').each(function(){
      var btable = $(this).find('.ui-jqgrid-btable');
      var width = $(this).parent().width();
      btable.setGridWidth(width);
    });
  });
});