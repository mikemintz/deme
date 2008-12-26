var DemeHighlighting = function(){
    var pub = {};
    pub.tokenize = function(docbody, body_str, is_escaped, parse_error, token_mouseover, token_mouseout, token_click){
        var docbody_clone = $(docbody.cloneNode(true));

        var body_str_index = 0;
        var remaining_body_str = body_str;
        var increment_body_str = function(n){
            body_str_index += n;
            remaining_body_str = remaining_body_str.substring(n);
        };
        //TODO better error handling when we call parse_error()
        var traverse_text = function(text, wrapper){
            while (text.length > 0) {
                var whiteSpaceBodyMatch = /((&nbsp;)|(\s))+/i.exec(remaining_body_str);
                var whiteSpaceTextMatch = /((&nbsp;)|(\s))+/i.exec(text);
                var bodyStartsWithWhiteSpace = (whiteSpaceBodyMatch != null && whiteSpaceBodyMatch.index == 0);
                var textStartsWithWhiteSpace = (whiteSpaceTextMatch != null && whiteSpaceTextMatch.index == 0);
                if (bodyStartsWithWhiteSpace && textStartsWithWhiteSpace) {
                    increment_body_str(whiteSpaceBodyMatch[0].length);
                    if (whiteSpaceTextMatch != null) {
                        var whiteSpaceTextNode = document.createTextNode(text.substring(0, whiteSpaceTextMatch[0].length));
                        wrapper.appendChild(whiteSpaceTextNode);
                        text = text.substring(whiteSpaceTextMatch[0].length);
                    }
                } else if (bodyStartsWithWhiteSpace) {
                    increment_body_str(whiteSpaceBodyMatch[0].length);
                } else if (textStartsWithWhiteSpace) {
                    var whiteSpaceTextNode = document.createTextNode(text.substring(0, whiteSpaceTextMatch[0].length));
                    wrapper.appendChild(whiteSpaceTextNode);
                    text = text.substring(whiteSpaceTextMatch[0].length);
                } else {
                    var token;
                    if (whiteSpaceTextMatch == null) {
                        token = text;
                    } else {
                        token = text.substring(0, whiteSpaceTextMatch.index);
                    }
                    var tokenWrapper = document.createElement('span');
                    tokenWrapper.deme_text_offset = body_str_index;
                    tokenWrapper.onmouseover = token_mouseover;
                    tokenWrapper.onmouseout = token_mouseout;
                    tokenWrapper.onclick = token_click;
                    var tokenTextNode = document.createTextNode(token);
                    tokenWrapper.appendChild(tokenTextNode);
                    wrapper.appendChild(tokenWrapper);
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
        var traverse_fn = function(nodes){
            for (var i = 0; i < nodes.length; i++) {
                var node = $(nodes[i]);
                if (node.nodeType == Node.TEXT_NODE) {
                    var wrapper = $(document.createElement('span'));
                    node.parentNode.insertBefore(wrapper, node);
                    var success = traverse_text(node.data, wrapper);
                    node.parentNode.removeChild(node);
                    if (!success) return false;
                } else {
                    if (!node.hasClassName('commentref')) {
                        // match the start tag
                        var startTagPattern = new RegExp("[.\\s]*<\\s*" + node.tagName + "((\\s*)|(\\s+[^>]+))>", "i");
                        var startTagMatch = startTagPattern.exec(remaining_body_str);
                        if (is_escaped || startTagMatch == null) {
                            var success = traverse_fn(node.childNodes);
                            if (!success) return false;
                        } else {
                            increment_body_str(startTagMatch.index + startTagMatch[0].length);
                            if (node.tagName == 'IMG') {
                                node.deme_text_offset = body_str_index - startTagMatch[0].length;
                                node.onmouseover = token_mouseover;
                                node.onmouseout = token_mouseout;
                                node.onclick = token_click;
                            }
                            var success = traverse_fn(node.childNodes);
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
                }
            }
            return true;
        };
        traverse_fn(docbody_clone.childNodes);
        return docbody_clone;
    };
    return pub;
}();
