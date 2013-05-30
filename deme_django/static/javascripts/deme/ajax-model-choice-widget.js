$(function() {
  $('.ajax-model-choice-widget').each(function(){
    var id = $(this).attr('data-input-id');
    var ajax_url = $(this).attr('data-ajax-url');
    var search_input = $("#"+id);
    var hidden_input = $(this);
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
    var newbtn = $('<span class="input-group-btn"><button class="btn btn-default">New</button></span>').insertAfter(search_input);
    newbtn.click(function(e){
      e.preventDefault();
    })
  });
});
