$.cookie.defaults.path="/";var ua=navigator.userAgent,checker={iphone:ua.match(/(iPhone|iPod)/),ipad:ua.match(/(iPad)/),blackberry:ua.match(/BlackBerry/),android:ua.match(/Android/),ie:ua.match(/MSIE/)};checker.android&&$("html").addClass("ua-android");$(function(){function e(e){if(checker.iphone||checker.ipad){o(!1);$(e).closest(".dropdown").hasClass("open")||setTimeout(function(){var t=$(e).closest(".dropdown").attr("class").split(" "),n="",r=["open"];for(var i=0;i<t.length;i++){var s=t[i];$.inArray(s,r)===-1&&(n+="."+s)}$(n).addClass("open")},1)}}function r(e){document.body.style.fontSize==""&&(document.body.style.fontSize=t+"px");current_size=parseFloat(document.body.style.fontSize);pos=n.indexOf(current_size);default_pos=n.indexOf(t);if(pos<0||e==0)pos=default_pos;pos+=e;pos<=0&&(pos=0);pos>=n.length&&(pos=n.length-1);var r=n[pos]+"px";$.cookie("ADMINBAR_TEXTSIZE_SIZE",r);i(r)}function i(e){$(".textsize-btn").addClass("resized");parseFloat(e)==t&&$(".textsize-btn").removeClass("resized");document.body.style.fontSize=e}function o(e){var t=$(".adminbar:not(.nonadminbar)");if(t.length==0)$("body").addClass("nonadmin");else if(e){$("body").removeClass("nonadmin");$.cookie("ADMINBAR_VISIBLE",!0);typeof window.metabarWidthAdjust=="function"&&metabarWidthAdjust();$(".adminbar a.advanced").addClass("active")}else{$("body").addClass("nonadmin");$.removeCookie("ADMINBAR_VISIBLE");$("#overall").css("max-width","");$(".adminbar a.advanced").removeClass("active")}}function a(e,t){t.length>0?e.click(function(e){e.preventDefault();t.attr("href")=="#"?t.click():window.location=t.attr("href")}):e.remove()}$.trim($("#actions-btn .actions-menu").text())==""&&$("#actions-btn").remove();$(".textsize-btn a").click(function(t){t.preventDefault();e(this)});$(".search-btn a.dropdown-toggle").click(function(t){t.preventDefault();e(this);$dropdown=$(this).closest(".dropdown");setTimeout(function(){$dropdown.find("input.search_box").focus()},1)});var t=14,n=[8,9,10,12,14,16,18,20,24,30];window.resizeText=i;var s=$.cookie("ADMINBAR_TEXTSIZE_SIZE");s&&i(s);$(".textsize-btn .btn").click(function(e){e.preventDefault();e.stopPropagation();var t=0;$(this).hasClass("smaller")?t=-1:$(this).hasClass("bigger")&&(t=1);r(t)});var u=$.cookie("ADMINBAR_VISIBLE");u?o(u):o(!1);$(".adminbar a.advanced").click(function(e){e.preventDefault();$(this).closest(".nonadminbar").length?o(!0):o(!1)});a($(".actions-wrap > li > a.create"),$(".actions-menu a.create"));a($(".actions-wrap > li > a.edit"),$(".actions-menu a.edit"));if($("h1.title").text().indexOf("» Edit")!==-1){$(".actions-wrap > li > a.edit").remove();$(".actions-menu a.edit").remove()}$("a.insert-item").each(function(){var e=$(this).attr("data-target");$("#"+e).length==0&&$(this).remove()})});