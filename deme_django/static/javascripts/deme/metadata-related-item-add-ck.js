$(function(){$("#metadata_content_related_items").on("contentload",function(){$(this).find(".type-related-item-add").each(function(){var e=$(this),t=e.find("a"),n=e.attr("data-new-modal-url"),r=$('<a href="#" class="btn btn-default btn-small newbtn" title="New Item"><i class="glyphicon glyphicon-plus"></i></a>').insertAfter(t);r.click(function(e){e.preventDefault();var t=Math.floor(Math.random()*1e6+1);window.open(n,"embedform-"+t,"width=400,toolbar=1,resizable=1,scrollbars=yes,height=400,top=100,left=100")})})})});