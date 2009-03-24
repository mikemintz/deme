var DemeHighlighting = function(){
    var pub = {};

    pub.scan_for_offsets = function(docbody, body_str, is_escaped, parse_error, whitespace_regex, token_wrapper_callback, element_callback, wrap_text){
        var body_str_index = 0;
        //TODO better error handling when we call parse_error()
        var traverse_text = function(text, wrapper){
            var text_index = 0;
            while (text_index < text.length) {
                if (!is_escaped) {
                    while (body_str_index < body_str.length && body_str.substring(body_str_index, body_str_index + 1) == '<') {
                        if (body_str.substring(body_str_index + 1, body_str_index + 4) == '!--') {
                            body_str_index = body_str.indexOf('-->', body_str_index + 4) + 3;
                        } else {
                            body_str_index = body_str.indexOf('>', body_str_index + 1) + 1;
                        }
                    }
                }
                whitespace_regex.lastIndex = body_str_index;
                var whiteSpaceBodyMatch = whitespace_regex.exec(body_str);
                whitespace_regex.lastIndex = text_index;
                var whiteSpaceTextMatch = whitespace_regex.exec(text);
                var bodyStartsWithWhiteSpace = (whiteSpaceBodyMatch != null && whiteSpaceBodyMatch.index == body_str_index);
                var textStartsWithWhiteSpace = (whiteSpaceTextMatch != null && whiteSpaceTextMatch.index == text_index);
                if (bodyStartsWithWhiteSpace && textStartsWithWhiteSpace) {
                    body_str_index += whiteSpaceBodyMatch[0].length;
                    if (whiteSpaceTextMatch != null) {
                        if (wrap_text) {
                            var whiteSpaceTextNode = document.createTextNode(text.substring(text_index, text_index + whiteSpaceTextMatch[0].length));
                            wrapper.appendChild(whiteSpaceTextNode);
                        }
                        text_index += whiteSpaceTextMatch[0].length;
                    }
                } else if (bodyStartsWithWhiteSpace) {
                    body_str_index += whiteSpaceBodyMatch[0].length;
                } else if (textStartsWithWhiteSpace) {
                    if (wrap_text) {
                        var whiteSpaceTextNode = document.createTextNode(text.substring(text_index, text_index + whiteSpaceTextMatch[0].length));
                        wrapper.appendChild(whiteSpaceTextNode);
                    }
                    text_index += whiteSpaceTextMatch[0].length;
                } else {
                    var token;
                    if (whiteSpaceTextMatch == null) {
                        token = text.substring(text_index);
                    } else {
                        token = text.substring(text_index, whiteSpaceTextMatch.index);
                    }
                    if (wrap_text) {
                        var tokenWrapper = document.createElement('span');
                        var tokenTextNode = document.createTextNode(token);
                        tokenWrapper.appendChild(tokenTextNode);
                        token_wrapper_callback(tokenWrapper, body_str_index);
                        wrapper.appendChild(tokenWrapper);
                    }
                    for (var i = 0; i < token.length; i++) {
                        if (body_str_index >= body_str.length) {
                            parse_error('error @ ' + body_str_index + ': out of body_str');
                            return false;
                        }
                        var bodyChar = body_str.substring(body_str_index, body_str_index+1);
                        if (!is_escaped && bodyChar == '&') {
                            var semicolonIndex = body_str.indexOf(';', body_str_index+1);
                            if (semicolonIndex == -1) {
                                parse_error('error @ ' + body_str_index + ': found ampersand without semicolon');
                                return false;
                            }
                            body_str_index = semicolonIndex + 1;
                        } else {
                            var tokenChar = token.substring(i, i+1);
                            if (bodyChar != tokenChar) {
                                parse_error('error @ ' + body_str_index + ': bodyChar (' + bodyChar + ') != tokenChar (' + tokenChar + ')');
                                return false;
                            }
                            body_str_index += 1;
                        }
                    }
                    text_index += token.length;
                }
            }
            return true;
        };
        var traverse_fn = function(nodes, inside_commentref){
            for (var i = 0; i < nodes.length; i++) {
                var node = nodes[i];
                if (inside_commentref || (node.nodeType == Node.ELEMENT_NODE && $(node).hasClass('commentref'))) {
                    var success = traverse_fn(node.childNodes, true);
                    if (!success) return false;
                } else if (node.nodeType == Node.TEXT_NODE) {
                    if (wrap_text) {
                        var wrapper = document.createElement('span');
                        node.parentNode.insertBefore(wrapper, node);
                        var success = traverse_text(node.data, wrapper);
                        node.parentNode.removeChild(node);
                        if (!success) return false;
                    } else {
                        var success = traverse_text(node.data, null);
                        if (!success) return false;
                    }
                } else if (node.nodeType == Node.ELEMENT_NODE) {
                    element_callback(node, body_str_index);
                    if (!$(node).hasClass('commentref')) {
                        //TODO are there others besides SCRIPT and STYLE that we must skip the body for?
                        //TODO can we unify some of the code for SCRIPT/STYLE and IMG?
                        if (!is_escaped && (node.tagName == 'SCRIPT' || node.tagName == 'STYLE')) {
                            var tagPattern = new RegExp("[\\S\\s]*?<\\s*" + node.tagName + "((\\s*)|(\\s+[^>]+))((/\\s*>)|(>[\\S\\s]*?<\\s*/\\s*" + node.tagName + "\\s*>))", "ig");
                            tagPattern.lastIndex = body_str_index;
                            var tagMatch = tagPattern.exec(body_str);
                            if (tagMatch) {
                                body_str_index += tagMatch[0].length;
                            } else {
                                parse_error('error @ ' + body_str_index + ': could not find ' + node.tagName + ' tag in body_str');
                                return false;
                            }
                        } else if (!is_escaped && node.tagName == 'IMG') {
                            var startTagPattern = new RegExp("([\\S\\s]*?)<\\s*" + node.tagName + "((\\s*)|(\\s+[^>]+))>", "ig");
                            startTagPattern.lastIndex = body_str_index;
                            var startTagMatch = startTagPattern.exec(body_str);
                            if (startTagMatch) {
                                token_wrapper_callback(node, body_str_index + startTagMatch[1].length);
                                body_str_index += startTagMatch[0].length;
                            } else {
                                parse_error('error @ ' + body_str_index + ': could not find ' + node.tagName + ' tag in body_str');
                                return false;
                            }
                        } else {
                            var success = traverse_fn(node.childNodes, false);
                            if (!success) return false;
                        }
                    }
                } else if (node.nodeType == Node.COMMENT_NODE) {
                    // We can safely ignore comment nodes, since they are skipped over in body_str
                } else if (node.nodeType == Node.ATTRIBUTE_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.ATTRIBUTE_NODE');
                } else if (node.nodeType == Node.CDATA_SECTION_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.CDATA_SECTION_NODE');
                } else if (node.nodeType == Node.ENTITY_REFERENCE_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.ENTITY_REFERENCE_NODE');
                } else if (node.nodeType == Node.ENTITY_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.ENTITY_NODE');
                } else if (node.nodeType == Node.PROCESSING_INSTRUCTION_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.PROCESSING_INSTRUCTION_NODE');
                } else if (node.nodeType == Node.DOCUMENT_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.DOCUMENT_NODE');
                } else if (node.nodeType == Node.DOCUMENT_TYPE_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.DOCUMENT_TYPE_NODE');
                } else if (node.nodeType == Node.DOCUMENT_FRAGMENT_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.DOCUMENT_FRAGMENT_NODE');
                } else if (node.nodeType == Node.NOTATION_NODE) {
                    parse_error('error @ ' + body_str_index + ': do not know how to process Node.NOTATION_NODE');
                } else {
                    parse_error('error @ ' + body_str_index + ': do not know how to process node.nodeType = ' + node.nodeType);
                }
            }
            return true;
        };
        traverse_fn(docbody.childNodes, false);
        return docbody;
    };

    pub.tokenize = function(docbody, body_str, is_escaped, parse_error, token_classname, token_click){
        var docbody_clone = docbody.cloneNode(true);
        var token_wrapper_callback = function(tokenWrapper, body_str_index){
            tokenWrapper.deme_text_offset = body_str_index;
            tokenWrapper.className = token_classname;
            tokenWrapper.onclick = token_click;
        };
        var element_callback = function(node, body_str_index){
        };
        var whitespace_regex = (is_escaped ? /\s+/g : /((&nbsp;)|(\s))+/ig);
        return pub.scan_for_offsets(docbody_clone, body_str, is_escaped, parse_error, whitespace_regex, token_wrapper_callback, element_callback, true);
    };

    pub.tag_highlight_endpoints_with_offset = function(docbody, body_str, is_escaped, start_id, end_id){
        var docbody_clone = docbody;
        var token_wrapper_callback = function(tokenWrapper, body_str_index){
        };
        var element_callback = function(node, body_str_index){
            if (node.id == start_id || node.id == end_id) {
                node.deme_text_offset = body_str_index;
            }
        };
        var whitespace_regex = (is_escaped ? /\s+/g : /((&nbsp;)|(\s))+/ig);
        return pub.scan_for_offsets(docbody_clone, body_str, is_escaped, parse_error, whitespace_regex, token_wrapper_callback, element_callback, false);
    };

    pub.get_current_highlight = function(docbody, body_str){
        //TODO: we should clone the whole body before doing any of this so we don't screw anything up by splitting text and inserting spans
        var id = (Math.random() + '').split('.')[1];
        var start_id = "deme_highlight_start_" + id;
        var end_id = "deme_highlight_end_" + id;
        var start_span = null;
        var end_span = null;
        var contents = null;
        if ($.browser.msie) {
            var range = window.document.selection.createRange();
            if (range.htmlText != "") {
                function offset(r, id) {
                    r.move('Character', 1);
                    r.move('Character', -1);
                    r.pasteHTML("<span id='" + id + "'></span>");
                }
                
                var r1 = range.duplicate();
                var r2 = range.duplicate();
                r1.collapse(true);
                r2.collapse(false);

                try { offset(r1, start_id); offset(r2, end_id); }
                catch (e) { alert("ERROR! 12398123"); return null; }
                start_span = document.getElementById(start_id);
                end_span = document.getElementById(end_id);
                contents = document.createElement('div');
                contents.innerHTML = range.htmlText;
            } else {
                return null;
            }
            window.document.selection.createRange().collapse(true);
        } else {
            // Get the endpoints
            var range = window.getSelection();
            var endpointsDiffer = (range.anchorNode !== range.focusNode || range.anchorOffset != range.focusOffset);
            if (range.isCollapsed || !endpointsDiffer) {
                return null;
            }
            var endpoints = {start: {node:range.anchorNode, offset:range.anchorOffset}, end: {node:range.focusNode, offset:range.focusOffset}};
            try { range.collapseToStart(); }
            catch (nothingSelected) { return null; }
            if (endpoints.start.node !== range.anchorNode || endpoints.start.offset != range.anchorOffset) {
                var tmp = endpoints.start;
                endpoints.start = endpoints.end;
                endpoints.end = tmp;
            }

            // Set contents
            var contentsRange = document.createRange();
            contentsRange.setStart(endpoints.start.node, endpoints.start.offset);
            contentsRange.setEnd(endpoints.end.node, endpoints.end.offset);
            contents = contentsRange.cloneContents();

            // Insert invisible span nodes at the start and end.
            var insert_span = function(span, node, offset){
                if (node.nodeType == Node.TEXT_NODE) {
                    var leftString = node.data.substring(0, offset);
                    var rightString = node.data.substring(offset);
                    var leftNode = document.createTextNode(leftString);
                    var rightNode = document.createTextNode(rightString);
                    node.parentNode.insertBefore(leftNode, node);
                    node.parentNode.insertBefore(span, node);
                    node.parentNode.insertBefore(rightNode, node);
                    node.parentNode.removeChild(node);
                    return rightNode;
                } else if (node.nodeType == Node.ELEMENT_NODE) {
                    var child = node.childNodes[offset];
                    node.insertBefore(span, child);
                    return node;
                } else {
                    //TODO handle this better? I'm pretty sure it's impossible here
                    alert("error 13131914: encountered node that wasn't an element or a text node");
                }
            };
            start_span = document.createElement('span');
            end_span = document.createElement('span');
            start_span.id = start_id;
            end_span.id = end_id;
            var rightNode = insert_span(start_span, endpoints.start.node, endpoints.start.offset);
            if (endpoints.start.node == endpoints.end.node) {
                if (endpoints.start.node.nodeType == Node.TEXT_NODE) {
                    insert_span(end_span, rightNode, endpoints.end.offset - endpoints.start.offset);
                } else {
                    insert_span(end_span, rightNode, endpoints.end.offset + 1);
                }
            } else {
                insert_span(end_span, endpoints.end.node, endpoints.end.offset);
            }
            window.getSelection().removeAllRanges();
        }

        // Get the deme offset for the invisible spans
        DemeHighlighting.tag_highlight_endpoints_with_offset(docbody, body_str, is_escaped, start_id, end_id);

        var node_cmp = function(x, y){
            var node_array = function(node){
                if (!node || !node.parentNode) return [];
                var result = node_array(node.parentNode);
                for (var i in node.parentNode.childNodes) {
                    if (node.parentNode.childNodes[i] == node) {
                        result.push(i);
                        break;
                    }
                }
                return result;
            };
            var x_arr = node_array(x);
            var y_arr = node_array(y);
            for (var i in x_arr) {
                if (i >= y_arr.length) {
                    return 0; // one is inside the other
                } else if (x_arr[i] < y_arr[i]) {
                    return -1; // x is before y
                } else if (x_arr[i] > y_arr[i]) {
                    return 1; // y is before x
                }
            }
            return 0; // one is inside the other
        };

        if (!start_span.deme_text_offset) {
            if (node_cmp(start_span, docbody) == 1) {
                return null; // start_span is after docbody
            } else {
                start_span.deme_text_offset = 0;
            }
        }

        if (!end_span.deme_text_offset) {
            if (node_cmp(end_span, docbody) == -1) {
                return null; // end_span is before docbody
            } else {
                end_span.deme_text_offset = body_str.length;
            }
        }

        //TODO we should probably get rid of all things like commentref from contents. alternatively, construct contents ourselves since we know start_span and end_span
        //TODO it would definitely be best if we just constructed contents ourselves
        return {start_offset: start_span.deme_text_offset, end_offset: end_span.deme_text_offset, contents: contents};
    };
 
    return pub;
}();

