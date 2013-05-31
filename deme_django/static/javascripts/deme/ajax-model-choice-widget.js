$(function() {
  $('.ajax-model-choice-widget').each(function(){
    var hidden_input = $(this);
    var id = hidden_input.attr('data-input-id');
    var ajax_url = hidden_input.attr('data-ajax-url');
    var search_input = $("#"+id);
    var cache = {};
    var last_xhr;
    search_input.autocomplete({
        minLength: 0,
        select: function(event, ui) {
            search_input[0].value = ui.item.value;
            hidden_input[0].value = ui.item.id;
            return false;
        },
        source: function(request, response) {
            var term = request.term;
            if (term in cache) {
                response(cache[term]);
                return;
            }
            last_xhr = $.getJSON(ajax_url, {q:term}, function(data, status, xhr) {
                var normalized_data = $.map(data, function(x){ return {value: x[0], id: x[1]} });
                normalized_data.splice(0, 0, {value: "[None]", id: ""});
                cache[term] = normalized_data;
                response(normalized_data);
            });
        },
    });

    // set up new button
    var newbtn = $('<span class="input-group-btn"><a href="#" class="btn btn-default newbtn" title="New Item"><i class="glyphicon glyphicon-plus"></i></a></span>').insertAfter(search_input);
    newbtn.find('a').click(function(e){
      e.preventDefault();
      var new_modal_url = hidden_input.attr('data-new-modal-url');
      var random_num = Math.floor((Math.random()*1000000)+1);
      window.open(new_modal_url, 'embedform-' + random_num, 'width=400,toolbar=1,resizable=1,scrollbars=yes,height=400,top=100,left=100');
    })
  });

  function ajaxModelChoiceWidgetUpdateValue(id, dict) {
    var itemid = dict['id'];
    var itemname = dict['name'];
    var input = $('#' + id);
    var hidden_input = $('[data-input-id="'+id+'"]');
    hidden_input.val(itemid);
    input.val(itemname);
  }
  window.ajaxModelChoiceWidgetUpdateValue = ajaxModelChoiceWidgetUpdateValue;
});
