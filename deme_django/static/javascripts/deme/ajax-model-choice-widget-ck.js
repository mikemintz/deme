$(function(){function e(e,t){var n=t.id,r=t.name,i=$("#"+e),s=$('[data-input-id="'+e+'"]');s.val(n);i.val(r)}$(".ajax-model-choice-widget").each(function(){var e=$(this),t=e.attr("data-input-id"),n=e.attr("data-ajax-url"),r=$("#"+t),i={},s;r.autocomplete({minLength:0,select:function(t,n){r[0].value=n.item.value;e[0].value=n.item.id;return!1},source:function(e,t){var r=e.term;if(r in i){t(i[r]);return}s=$.getJSON(n,{q:r},function(e,n,s){var o=$.map(e,function(e){return{value:e[0],id:e[1]}});o.splice(0,0,{value:"[None]",id:""});i[r]=o;t(o)})}});var o=$('<span class="input-group-btn"><a href="#" class="btn btn-default">New</a></span>').insertAfter(r);o.find("a").click(function(t){t.preventDefault();var n=e.attr("data-new-modal-url"),r=Math.floor(Math.random()*1e6+1);window.open(n,"embedform-"+r,"width=400,toolbar=1,resizable=1,scrollbars=yes,height=400,top=100,left=100")})});window.ajaxModelChoiceWidgetUpdateValue=e});