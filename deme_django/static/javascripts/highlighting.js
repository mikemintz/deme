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
                        if (bodyChar == '&') {
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
                        var startTagPattern = new RegExp("[.\\s]*<\\s*" + node.tagName + "((\\s*)|(\\s+[^>]+))>", "i");
                        var startTagMatch = startTagPattern.exec(remaining_body_str);
                        if (is_escaped || startTagMatch == null) {
                            var success = traverse_fn(node.childNodes, false);
                            if (!success) return false;
                        } else {
                            increment_body_str(startTagMatch.index + startTagMatch[0].length);
                            //TODO maybe there are tags besides img, like object or embed
                            if (node.tagName == 'IMG') {
                                token_wrapper_callback(node, body_str_index - startTagMatch[0].length);
                            }
                            var success = traverse_fn(node.childNodes, false);
                            if (!success) return false;

                            // match the optional end tag
                            var endTagPattern = new RegExp("\\s*<\\s*/\\s*" + node.tagName + "[^>]*>", "i");
                            var endTagMatch = endTagPattern.exec(remaining_body_str);
                            // we only want to match the end tag if it occurs RIGHT here
                            if (endTagMatch != null && endTagMatch.index == 0) {
                                increment_body_str(endTagMatch[0].length);
                            }
                        }
                    }
                } else {
                    /* TODO we need to handle all possible element types (comments are known to be possible), both here and highlighting
                        ELEMENT_NODE
                        ATTRIBUTE_NODE
                        TEXT_NODE
                        CDATA_SECTION_NODE
                        ENTITY_REFERENCE_NODE
                        ENTITY_NODE
                        PROCESSING_INSTRUCTION_NODE
                        COMMENT_NODE
                        DOCUMENT_NODE
                        DOCUMENT_TYPE_NODE
                        DOCUMENT_FRAGMENT_NODE
                        NOTATION_NODE
                    */
                }
            }
            return true;
        };
        traverse_fn(docbody.childNodes, false);
        return docbody;
    };

    pub.tokenize = function(docbody, body_str, is_escaped, parse_error, token_mouseover, token_mouseout, token_click){
        var docbody_clone = $(docbody.cloneNode(true));
        var token_wrapper_callback = function(tokenWrapper, body_str_index){
            tokenWrapper.deme_text_offset = body_str_index;
            tokenWrapper.onmouseover = token_mouseover;
            tokenWrapper.onmouseout = token_mouseout;
            tokenWrapper.onclick = token_click;
        };
        var element_callback = function(node, body_str_index){
        };
        var whitespace_regex = /((&nbsp;)|(\s))+/i;
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
        var whitespace_regex = /((&nbsp;)|(\s))+/i;
        return pub.scan_for_offsets(docbody_clone, body_str, is_escaped, parse_error, whitespace_regex, token_wrapper_callback, element_callback, false);
    };

    pub.get_current_highlight = function() {
        //TODO: we should clone the whole body before doing any of this so we don't screw anything up by splitting text and inserting spans
        var id = (Math.random() + '').split('.')[1];
        var start_id = "deme_highlight_start_" + id;
        var end_id = "deme_highlight_end_" + id;
        var start_span = null;
        var end_span = null;
        var contents = null;
        if (Prototype.Browser.IE) {
            //TODO: understand getOwnerDoc
            var getOwnerDoc = function(hint) {
                if (!hint) return document; // lame!
                if (/document$/i.test(hint.nodeName))
                    return hint; // hint *is* a document object
                else if (hint.ownerDocument)
                    return hint.ownerDocument;
                else // rare case: eventually hit the document root
                    return getOwnerDoc(hint.parentNode);
            };
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
                start_span = getOwnerDoc(r1.parentElement()).getElementById(start_id);
                end_span = getOwnerDoc(r2.parentElement()).getElementById(end_id);
                contents = document.createElement('div');
                contents.innerHTML = range.htmlText;
            } else {
                return null;
            }
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
        }

        // Get the deme offset for the invisible spans
        DemeHighlighting.tag_highlight_endpoints_with_offset($('docbody'), body_str, is_escaped, start_id, end_id);

        //TODO we should probably get rid of all things like commentref from contents. alternatively, construct contents ourselves since we know start_span and end_span
        return {start_offset: start_span.deme_text_offset, end_offset: end_span.deme_text_offset, contents: contents};
    };
 
    return pub;
}();