$(function(){$("#metadata_content_related_items").on("contentload",function(){function e(){$("input[name='metadata_content_related_items_switcher']:checked").val()=="all"?content_section.find(".relationship").show():content_section.find(".relationship").each(function(){if($(this).find(".type-related-item-add").first().attr("data-count")==0){$(this).hide();$(this).addClass("empty")}})}content_section=$(this);title=content_section.find("h3").first();toggleButtons=$('<div class="btn-group btn-group-justified metadata_content_related_items_switcher_wrap" data-toggle="buttons-radio"><label class="btn btn-sm btn-info active"><input type="radio" name="metadata_content_related_items_switcher" value="existing" checked="checked"> Existing</label><label class="btn btn-sm btn-info"><input type="radio" name="metadata_content_related_items_switcher" value="all"> All</label></div>').insertAfter(title);toggleButtons.find("input").change(function(t){e()});e();content_section.find(".type-related-item-add").each(function(){var e=$(this),t=e.find(".action-wrap"),n=e.attr("data-new-modal-url"),r=$('<a href="#" class="newbtn btn btn-info btn-sm" title="New Item"><i class="glyphicon glyphicon-plus"></i></a>').appendTo(t);r.click(function(e){e.preventDefault();var t=Math.floor(Math.random()*1e6+1);window.open(n,"embedform-"+t,"width=600,toolbar=1,location=yes,resizable=1,scrollbars=yes,height=600,top=100,left=100")})})})});