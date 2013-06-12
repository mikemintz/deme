function openDialogBox(name) {
    var dialogBox = $("#" + name);
    dialogBox.dialog({
        autoOpen: false,
        bgiframe: true,
        modal: true,
        close: function(event, ui) {dialogBox.dialog('destroy')}
    });
    dialogBox.dialog('open');
}
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