$.cookie.defaults.path="/";$(function(){function i(){t.css("min-height",$(window).height())}function s(e){e<min_metabar_width?e=min_metabar_width:e>r&&(e=r);$.cookie("METABAR_WIDTH",e);a(e);n=e}function u(e){typeof e=="undefined"?t.toggleClass("closed"):e=="close"?t.addClass("closed"):t.removeClass("closed");if(t.hasClass("closed")){$("a.metabar-toggle").removeClass("active");$.removeCookie("METABAR_VISIBLE")}else{$("a.metabar-toggle").addClass("active");$.cookie("METABAR_VISIBLE",!0)}a(n)}function a(e){var n="";typeof e=="undefined"&&(e=t.width());!$("body").hasClass("nonadmin")&&!t.hasClass("closed")&&(n=$(window).width()-e-10+"px");t.css("width",e);$(".page-layout").css("max-width",n)}function f(){$.cookie("METABAR_VISIBLE")?u("open"):u("close")}function l(e){c(e,function(e){e.collapse("show");e.closest(".section").find(".header").removeClass("collapsed")})}function c(e,t){if(!e.hasClass("ajax-loaded")){var n=e.attr("id").replace("metadata_content_",""),r=metabar_ajax_url(n);e.find(".content").html("Loading&hellip;");$.ajax({url:r,success:function(n){e.addClass("ajax-loaded");e.find(".content").html(n);$("body").hasClass("nonadmin")&&e.css("height","auto");typeof t=="function"&&t(e)}})}else typeof t=="function"&&t(e)}var e=50,t=$("#metabar"),n=min_metabar_width=200,r=800;$(window).resize(function(){i();a()});i();t.resizable({minWidth:min_metabar_width,maxWidth:r,handles:"w",start:function(){t.addClass("noanim")},stop:function(e,n){t.removeClass("noanim");var r=n.size.width;s(r)}});$("#metabar").on("click","button.resize",function(t){var r=n*1-e;$(this).hasClass("resize-left")&&(r=n*1+e);s(r)});var o=$.cookie("METABAR_WIDTH");o&&s(o);$(".metabar-toggle").click(function(e){e.preventDefault();u()});f();t.on("show",".section .collapse",function(){c($(this));var e=$(this).attr("id").replace("metadata_content_","");$.cookie("METABAR_SECTION_"+e,!0)});t.on("hide",".section .collapse",function(){var e=$(this).attr("id").replace("metadata_content_","");$.removeCookie("METABAR_SECTION_"+e)});t.find(".section .collapse").each(function(){var e=$(this).attr("id").replace("metadata_content_","");$.cookie("METABAR_SECTION_"+e)&&l($(this))});window.metabar_show_section=l;$(".actions-wrap > li > a.comment, .actions-menu a.comment").click(function(){u("open");l($("#metadata_content_comments"))});$(".actions-wrap > li > a.permissions, .actions-menu a.permissions").click(function(){u("open");l($("#metadata_content_permissions"))})});