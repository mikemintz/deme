var DemeHighlighting = function(){
    var pub = {};

    pub.scan_for_offsets = function(docbody, body_str, is_escaped, parse_error, whitespace_regex, token_wrapper_callback, element_callback, wrap_text){
        var body_str_index = 0;
        var remaining_body_str = body_str;
        var increment_body_str = function(n){
            body_str_index += n;
            remaining_body_str = remaining_body_str.substring(n);
        };
        //TODO better error handling when we call parse_error()
        var traverse_text = function(text, wrapper){
            while (text.length > 0) {
                if (!is_escaped) {
                    //TODO we don't skip over <script> and <style> sections
                    while (remaining_body_str.length > 0 && remaining_body_str[0] == '<') {
                        if (remaining_body_str.substring(0, 4) == '<!--') {
                            increment_body_str(remaining_body_str.indexOf('-->') + 3);
                        } else {
                            increment_body_str(remaining_body_str.indexOf('>') + 1);
                        }
                    }
                }
                var whiteSpaceBodyMatch = whitespace_regex.exec(remaining_body_str);
                var whiteSpaceTextMatch = whitespace_regex.exec(text);
                var bodyStartsWithWhiteSpace = (whiteSpaceBodyMatch != null && whiteSpaceBodyMatch.index == 0);
                var textStartsWithWhiteSpace = (whiteSpaceTextMatch != null && whiteSpaceTextMatch.index == 0);
                if (bodyStartsWithWhiteSpace && textStartsWithWhiteSpace) {
                    increment_body_str(whiteSpaceBodyMatch[0].length);
                    if (whiteSpaceTextMatch != null) {
                        if (wrap_text) {
                            var whiteSpaceTextNode = document.createTextNode(text.substring(0, whiteSpaceTextMatch[0].length));
                            wrapper.appendChild(whiteSpaceTextNode);
                        }
                        text = text.substring(whiteSpaceTextMatch[0].length);
                    }
                } else if (bodyStartsWithWhiteSpace) {
                    increment_body_str(whiteSpaceBodyMatch[0].length);
                } else if (textStartsWithWhiteSpace) {
                    if (wrap_text) {
                        var whiteSpaceTextNode = document.createTextNode(text.substring(0, whiteSpaceTextMatch[0].length));
                        wrapper.appendChild(whiteSpaceTextNode);
                    }
                    text = text.substring(whiteSpaceTextMatch[0].length);
                } else {
                    var token;
                    if (whiteSpaceTextMatch == null) {
                        token = text;
                    } else {
                        token = text.substring(0, whiteSpaceTextMatch.index);
                    }
                    if (wrap_text) {
                        var tokenWrapper = document.createElement('span');
                        var tokenTextNode = document.createTextNode(token);
                        tokenWrapper.appendChild(tokenTextNode);
                        token_wrapper_callback(tokenWrapper, body_str_index);
                        wrapper.appendChild(tokenWrapper);
                    }
                    var body_i = 0;
                    for (var i = 0; i < token.length; i++) {
                        if (remaining_body_str.length <= 0) {
                            parse_error('error @ ' + body_str_index + ': out of remaining_body_str');
                            return false;
                        }
                        var bodyChar = remaining_body_str.substring(body_i, body_i+1);
                        if (!is_escaped && bodyChar == '&') {
                            var semicolonIndex = remaining_body_str.indexOf(';', body_i+1);
                            if (semicolonIndex == -1) {
                                parse_error('error @ ' + body_str_index + ': found ampersand without semicolon');
                                return false;
                            }
                            body_i = semicolonIndex + 1;
                        } else {
                            var tokenChar = token.substring(i, i+1);
                            if (bodyChar != tokenChar) {
                                parse_error('error @ ' + body_str_index + ': bodyChar (' + bodyChar + ') != tokenChar (' + tokenChar + ')');
                                return false;
                            }
                            body_i += 1;
                        }
                    }
                    increment_body_str(body_i);
                    text = text.substring(token.length);
                }
            }
            return true;
        };
        var traverse_fn = function(nodes, inside_commentref){
            for (var i = 0; i < nodes.length; i++) {
                var node = $(nodes[i]);
                if (inside_commentref || (node.nodeType == Node.ELEMENT_NODE && node.hasClassName('commentref'))) {
                    var success = traverse_fn(node.childNodes, true);
                    if (!success) return false;
                } else if (node.nodeType == Node.TEXT_NODE) {
                    if (wrap_text) {
                        var wrapper = $(document.createElement('span'));
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
                    if (!node.hasClassName('commentref')) {
                        // match the start tag
                        if (!is_escaped) {
                            if (node.tagName == 'IMG') {
                                var startTagPattern = new RegExp("[.\\s]*<\\s*" + node.tagName + "((\\s*)|(\\s+[^>]+))>", "i");
                                var startTagMatch = startTagPattern.exec(remaining_body_str);
                                if (startTagMatch) {
                                    token_wrapper_callback(node, body_str_index - startTagMatch[0].length);
                                }
                            }
                        }
                        var success = traverse_fn(node.childNodes, false);
                        if (!success) return false;
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
        var docbody_clone = $(docbody.cloneNode(true));
        var token_wrapper_callback = function(tokenWrapper, body_str_index){
            tokenWrapper.deme_text_offset = body_str_index;
            tokenWrapper.className = token_classname;
            tokenWrapper.onclick = token_click;
        };
        var element_callback = function(node, body_str_index){
        };
        var whitespace_regex = (is_escaped ? /\s+/ : /((&nbsp;)|(\s))+/i);
        return pub.scan_for_offsets(docbody_clone, body_str, is_escaped, parse_error, whitespace_regex, token_wrapper_callback, element_callback, true);
    };

    pub.tag_highlight_endpoints_with_offset = function(docbody, body_str, is_escaped, start_id, end_id){
        var docbody_clone = $(docbody);
        var token_wrapper_callback = function(tokenWrapper, body_str_index){
        };
        var element_callback = function(node, body_str_index){
            if (node.id == start_id || node.id == end_id) {
                node.deme_text_offset = body_str_index;
            }
        };
        var whitespace_regex = (is_escaped ? /\s+/ : /((&nbsp;)|(\s))+/i);
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
        if (Prototype.Browser.IE) {
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
