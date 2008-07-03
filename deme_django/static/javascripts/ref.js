
// XPATH := ID : PATH : OFFSET
// ID := <JavaScript identifier>
// PATH := / TAG PATH
// TAG := <html tagname> | <html tagname>[<integer>]
// OFFSET := <integer>

/* Function getOwnerDoc(hint)
 * --------------------------
 * If you're used to creating DOM elements using document.createElement,
 * you should stop.  If the document whose createElement method you use
 * differs from the document into which you ultimately append the element
 * (say, if you're working with iframes or popup windows), Internet
 * Explorer won't let you append the element.
 *
 * This function aims to ameliorate the problem by making it easy to
 * determine which document contains a given node.  Suppose you want to
 * append a new div into a node called "parent".  Since the new node must
 * be created by the document that contains parent, you should write the
 * following code:
 *
 *     var div = getOwnerDoc(parent).createElement('div');
 *     parent.appendChild(div);
 *
 * You may not yet appreciate the convenience of this function, but in
 * time you certainly will!
 */

var getOwnerDoc = function(hint) {
    if (!hint) return document; // lame!
    if (/document$/i.test(hint.nodeName))
        return hint; // hint *is* a document object
    else if (hint.ownerDocument)
        return hint.ownerDocument;
    else // rare case: eventually hit the document root
        return getOwnerDoc(hint.parentNode);
};

var mapWindows = function(iter) {
    var win, queue = [window];
    while (queue.length > 0) {
        iter(win = queue.shift());
        var iframes = win.document.getElementsByTagName('iframe');
        iframes = $A(iframes).each(function(f) { queue.push(f.contentWindow) });
    }
};

var ixnay = function(win) {
    if (win.getSelection) // Mozilla
        win.getSelection().removeAllRanges();
    else if (win.document.selection) // IE
        win.document.selection.createRange().collapse(true);
};
function clearAllSelections() { mapWindows(ixnay) }

var g$ = function(id) {
    var results = [];
    mapWindows(function(w) {
        var elem = w.document.getElementById(id);
        if (elem) results.push(elem);
    });
    switch (results.length) {
        case 0: return null;
        case 1: return results[0];
        default: return results;
    }
}

var del = function(obj, prop) {
    var value = obj[prop];
    try { delete obj[prop] }
    catch (IESUCKS) { obj[prop] = undefined }
    return value;
};

// e.g., eval(swap('var1', 'var2'))
var swap = function(var1, var2) {
  return ('{ var temp = ' + var1 + '; ' +
             var1 + ' = ' + var2 + '; ' +
             var2 + ' = temp; }');
};

if (!Object.extend) {
    Object.extend = function(dst, src) {
        for (var i in src) {
            try { dst[i] = src[i] }
            catch (e) { /*pass*/ }
        }
        return dst;
    };
}

/* Function: makeRegistry(obj)
 * ---------------------------
 * A facility for keeping track of arbitrary "registered" objects in a
 * container that supports constant-time lookup.  This provides a
 * substitute for hashing when the objects do not have unique string
 * representations that could be used as hash keys.  In order to register an
 * object called obj, first create a registry like so:
 *
 *     var registry = makeRegistry();
 *
 * and then invoke the register method:
 *
 *     registry.register(obj);
 *
 * Now registry.registered(obj) will return true unless you decide to
 * unregister the object by calling
 *
 *     registry.register(obj, false);
 *
 * or, equivalently,
 *
 *     registry.unregister(obj);
 *
 * In order to turn an existing object into a registry, just pass that
 * object to makeRegistry like so:
 *
 *     makeRegistry(myNamespaceObject);
 *
 * The result need not be reassigned to myNamespaceObject, since the register
 * and registered methods will be added to the object within makeRegistry.
 */
var makeRegistry = (function(registry_uid) {

    var _remove = Array.prototype.remove = function(i) {
        return this.slice(0, i).concat(this.slice(i + 1));
    };

    // NOTE: This is the function which will be assigned to the variable
    // makeRegistry.  The function with argument registry_uid is enclosed in
    // parentheses because we call it immediately, so that it returns the
    // following function as its result:
    
    return function(/*optional:*/ obj) {

        obj = obj || {};
        var mark = '_mark_' + (registry_uid++) + '_id';
        var _registered = [];
        
        obj.register = function(node, /*optional:*/ value) {
            if (value || typeof value == 'undefined') {
                if (!this.registered(node)) {
                    _registered.push(node);
                    node[mark] = _registered.length - 1;
                }
            } else {
                var pos = node[mark];
                _registered = _remove.call(_registered, pos);
                del(node, mark);
            }
            return node;
        }
        
        obj.unregister = function(node) {
            obj.register(node, false);
        }
        
        obj.registered = function(node) {
            var id = node[mark];
            return (typeof id == 'number' &&
                    _registered[id] === node);
        }

        obj.registered.map = function(iter) {
            for (var i = 0; i < _registered.length; ++i)
                iter(_registered[i]);
        }

        return obj;
    
    };
    
})(0); // the first registry will have id 0


var Element = Object.extend(Element || {}, {

    isTextNode: function(e) {
        return (e && e.nodeName &&
                /text$/i.test(e.nodeName));
    },

    infertile: function(node) {
        // I.e., declared EMPTY in the HTML 4 DTD:
        // http://www.w3.org/TR/html401/sgml/dtd.html
        switch (node.nodeName.toLowerCase()) {
        case "img": case "br": case "hr": case "input":
        case "area": case "link": case "param":
        case "col": case "base": case "meta":
            return true;
        default:
            return false;
        }
    },

    insertBefore: function(what, beforeWhat) {
        beforeWhat.parentNode.insertBefore(what, beforeWhat);
        return what;
    },

    insertAfter: function(what, afterWhat) {
        afterWhat.parentNode.replaceChild(what, afterWhat);
        Element.insertBefore(afterWhat, what);
        return what;
    },

    getChildrenByTagName: function(node, tagName) {
        var result = [], child = node.firstChild;
        tagName = tagName.toLowerCase();
        do if ((child.tagName || '').toLowerCase() == tagName)
            result.push(child);
        while ((child = child.nextSibling));
        return result;
    },

    // Given a DOM node, find its first or last descendant.
    // Finds the first by default.
    getLeaf: function(node, /*optional:*/ last) {
        var which = last ? 'lastChild' : 'firstChild';
        while (node[which])
            node = node[which];
        return node;
    },            

    // Replaces a node with its children.  If the node has no children,
    // simply removes the node from the DOM.
    unpack: function(container) {
        var parent = container.parentNode, children = [];
        if (!parent) return container;
        for (var child = container.firstChild; !!child; child = child.nextSibling)
            children.push(child);
        while ((child = children.shift()))
            Element.insertBefore(container.removeChild(child), container);
        return parent.removeChild(container);
    }

});

var StyleParent = makeRegistry({

    // Encapsulates a text node with a span.  The span can be assigned CSS
    // style properties, whereas a text node cannot.    
    add: function(textNode) {
        StyleParent.remove(textNode);        
        var sp = getOwnerDoc(textNode).createElement('span');
        if (textNode.parentNode)
            textNode.parentNode.replaceChild(sp, textNode);
        sp.appendChild(textNode);
        sp._style_child = textNode;
        return StyleParent.register(sp);
    },
    
    remove: function(textNode) {
        var sp = StyleParent.get(textNode);
        if (sp) Element.unpack(sp);
        return sp;
    },
    
    get: function(textNode) {
        var parent = textNode.parentNode;
        return (parent && parent._style_child === textNode
                ? parent : null);
    }
    
});


/* Class Region(xPath_start, xPath_end)
 * ----------------------------------------------
 * The model representation of a single highlighted area, as defined by
 * two endpoint positions.  The xPaths can be objects or strings.
 */
var Region = function(xPath_start, /*optional:*/ xPath_end) {
    this.xPath_start = new XPath(xPath_start);
    this.xPath_end = (xPath_end ? new XPath(xPath_end) : this.xPath_start);
    if (this.xPath_start.getBaseNode() !== this.xPath_end.getBaseNode())
        throw "Endpoints not contained by a valid common ancestor: " +
            this.xPath_start + ", " + this.xPath_end;
};

Object.extend(Region, {
    
    fromSelection: function() {
        endpoints = Region.fromBrowserRange();
        if (!endpoints) return null;
        clearAllSelections();
        return new Region(endpoints.start, endpoints.end);
    },
    
    fromBrowserRange: function() {

        var endpoints = Region.getEndpoints();
        if (!endpoints)
            return endpoints;

        /* The range representation returned by the browser is too fragile
         * to survive changes to the DOM.  If the endpoint of a
         * highlighted region falls within a text node, the browser will
         * specify that position by giving the text node and a character
         * offset.  If the endpoint falls between two DOM nodes, however,
         * the browser gives the parent node and the childNodes index of
         * the node immediately following the endpoint position.  The
         * crucial asymmetry between these two representations is that one
         * counts characters while the other counts whole nodes (note that
         * a text node counts as one node).
         *
         * Counting characters is ultimately more robust, so we want a
         * representation that always specifies two pieces of information:
         *
         *     1.  a parent node that is never a text node (since text
         *         nodes are prone to splitting), and
         *     2.  the textual offset of the endpoint computed relative to
         *         the parent node
         *
         * The offset will be the sum of the lengths of all leaves in the
         * DOM that precede the endpoint position and are descendants of
         * the parent node.  The length of a text node is just its textual
         * length, and the length of DOM nodes is computed recursively.
         * If a DOM node has no children, its length will therefore be 0,
         * unless it happens to be one of those nodes that should never
         * have children (like IMG nodes; see Element.infertile for a
         * complete list), in which case it contributes a length of 1 to
         * the sum.  The intuition here is that we need to keep track of
         * whether a region starts/ends before or after an IMG or BR or HR
         * tag, since those tags correspond to visible, non-textual HTML
         * elements.
         */

        return { start: XPath.normalize(endpoints.start),
                 end:   XPath.normalize(endpoints.end) };
    
    },

    getEndpoints: function() {
        function anyRange(test, factory) {
            try { mapWindows(test) }
            catch (range) {
                var result = factory(range);
                return result;
            }
        }
        
        if (document.all) {
            return anyRange(function(w) {
                var range = w.document.selection.createRange();
                if (range.htmlText != "") throw range;
            }, Region.IERange);
        } else { // TODO Safari doesn't quite conform to this in the handling of images.
            return anyRange(function(w) {
                var range = w.getSelection();
                var endpointsDiffer = (range.anchorNode  !== range.focusNode ||
                                       range.anchorOffset != range.focusOffset);
                if (!range.isCollapsed && endpointsDiffer)
                    throw range;
            }, Region.W3CRange);
        }  
    },

    W3CRange: function(range) {
        var endpoints = { start: { node:   range.anchorNode,
                                   offset: range.anchorOffset },
                          end:   { node:   range.focusNode,
                                   offset: range.focusOffset } };
        
        try { range.collapseToStart(); }
        catch (nothingSelected) { return null; }
        if (endpoints.start.node !== range.anchorNode ||
            endpoints.start.offset != range.anchorOffset)
            eval(swap('endpoints.start', 'endpoints.end'));

        function fixOffset(tuple) {
            if (Element.isTextNode(tuple.node))
                tuple.offset = XPath.renderedOffset(tuple.node, tuple.offset);
            else if (tuple.offset > 0) {
                var child = tuple.node.childNodes[tuple.offset - 1];
                tuple.offset = XPath.cumOffsetTo(child, true);
            } else tuple.offset = 0;
        }

        fixOffset(endpoints.start);
        fixOffset(endpoints.end);
        
        return endpoints;
    },
            
    IERange: function(range) {

        function offset(r) {
            r.move('Character', 1);
            r.move('Character', -1);
            var id = (Math.random() + '').split('.')[1];
            r.pasteHTML("<span id='" + id + "'></span>");
            var span = getOwnerDoc(r.parentElement()).getElementById(id);
            var result = XPath.cumOffsetTo(span);
            span.parentNode.removeChild(span);
            return result;
        }
        
        function makeSpot(r) {
            return { node: r.parentElement(), offset: offset(r) };
        }
            
        var r1 = range;
        var r2 = r1.duplicate();
        r1.collapse(true);
        r2.collapse(false);

        try { return { start: makeSpot(r1), end: makeSpot(r2) } }
        catch (e) { throw e; return null }
        
    }
    
});

Region.prototype = {

    toString: function() {
        return ('["'   + this.xPath_start +
                '", "' + this.xPath_end   + '"]');
    },

    textContents: function() {
        var result = "";
        this.placeEndPoints();
        LeafIterator(this.start_tag, this.end_tag, function(l) {
            if (Element.isTextNode(l))
                result += l.nodeValue;
        });
        //this.removeEndPoints();
        return result;
    },

    // This assumes the base_nodes for xPath_start and xPath_end are the same.    
    getOwnerDoc: function() {
        return getOwnerDoc(this.xPath_start.getBaseNode());
    },

    makeEndPoint: function() {
        return this.getOwnerDoc().createElement('span');
    },
    
    placeEndPoints: function() {
        this.removeEndPoints();
        this.start_tag = this.makeEndPoint();
        this.end_tag = this.makeEndPoint();
        // This order of insertion reduces the complexity of calculating
        // renderedOffsets correctly.  Note that the end tag always occurs 
        // textually after the start tag.
        this.xPath_end.insertAt(this.end_tag);
        this.xPath_start.insertAt(this.start_tag);
    },

    removeEndPoints: function() {
        
        function remove(obj, prop, xPathToUpdate) {
            if (typeof obj[prop] == 'undefined') return false;
            
            xPathToUpdate.updateWith(obj[prop]);
            
            var parent = obj[prop].parentNode;
            if (parent) {
                parent.removeChild(obj[prop]);
                parent.normalize(); // merges adjacent text nodes
            }
            
            LeafIterator.unregister(obj[prop]); // possibly unnecessary
            return del(obj, prop); // returns deleted property
        }
        
        return !!(remove(this, 'start_tag', this.xPath_start) &&
                  remove(this, 'end_tag', this.xPath_end));
    },

    ensureHighlightCss: function() {
        // XXX TODO this doesn't work in Safari.  CSS rules noneditable?
        try {
            var doc = getOwnerDoc(this.xPath_start.getBaseNode());
            var head = doc.getElementsByTagName('head')[0];
            // TODO avoid needless additions
            var ss = head.appendChild(doc.createElement('style'));
            ss.type = 'text/css';
            ss.innerHTML = '.highlighted { background: lightgreen }';
        } catch (whatever) {}
    },

    highlight: function(/*optional:*/ val) {
        
        this.ensureHighlightCss();
        
        if (typeof val == 'undefined')
            val = true;
        
        if (val)
            this.placeEndPoints();

        // XXX TODO do this with classnames somehow...
        var leaf, leaves = [], color = val ? 'lightgreen' : '';
        LeafIterator(this.start_tag, this.end_tag,
                     function(l) { leaves.push(l); });
        while ((leaf = leaves.shift())) {
            if (Element.isTextNode(leaf)) {
                if (!val) StyleParent.remove(leaf);
                else StyleParent.add(leaf).style.background = color;
            } else leaf.style.background = color;
        }
        
        if (!val)
            this.removeEndPoints();
    }

};

/* Class XPath(spot)
 * ---------------------------
 * The model representation of a position within the DOM.  The spot
 * argument can be a string or an object with node and offset properties.
 */
var XPath = function(spot) {
    spot = XPath.parse(spot);
    this.spot = new XPath.Spot(spot.node, spot.offset);
};

Object.extend(XPath, {
        
    /* Class XPath.Spot(node, offset)
     * ------------------------------
     * This class exists only to enforce the desired structure for the spot
     * argument supplied to the XPath constructor.
     */
    Spot: function(node, offset) {
        this.node = node;
        this.offset = offset;
    },
        
    // Computes the appropriate spot given a string XPath:
    parse: function(xPath) {
        if (typeof xPath != 'string') return xPath;
        var idPathAndOffset = xPath.split(':');
        var node = g$(idPathAndOffset[0]),
            path = idPathAndOffset[1],
            offset = idPathAndOffset[2];
        var tag, tags = path.split('/').slice(1);
        while ((tag = tags.shift())) {
            var match = /(\w+)\[(\d+)\]/.exec(tag);
            var index =   match ? match[2] : 0;
            var tagName = match ? match[1] : tag;
            node = Element.getChildrenByTagName(node, tagName)[index];
        }
        return { node: node, offset: offset };
    },
        
    textualLength: function(node) {
        var result = 0;
        function sumLengths(leaf, length) { result += length; }
        XPath.Counter(node, sumLengths);
        return result;
    },

    cumOffsetTo: function(node, /*optional:*/ andInclude) {
        var result = andInclude ? XPath.textualLength(node) : 0;
        while ((node = node.previousSibling))
            result += XPath.textualLength(node);
        return result;
    },

    // NOTE: Since IE operates in terms of renderedOffsets by default, we
    // should convert to renderedOffsets when generating XPaths, and
    // always assume that an offset is of the rendered kind.  We only need
    // to convert back to rawOffsets when we're trying to splice something
    // into a textNode in a non-IE browser.

    // ALSO NOTE: This function should effectively return rawOffset in
    // IE!!  TODO test this assumption!
    renderedOffset: function(textNode, rawOffset, /*optional:*/ prev) {
        if (Element.getStyle(textNode.parentNode, 'white-space') != 'pre') {
            prev = prev || LeafIterator.getSuccessor(textNode, true);
            var text = textNode.nodeValue.slice(0, rawOffset);
            text = text.replace(/\s+/g, ' ');
            if (Element.isTextNode(prev) && /\s$/.test(prev.nodeValue))
                text = text.replace(/^\s+/, '');
            return text.length;
        } else return rawOffset;
    },

    // NOTE: this rawOffset function is not a perfect inverse of
    // renderedOffset, since information is lost in generating the
    // renderedOffset.
    rawOffset: function(textNode, renderedOffset, /*optional:*/ prev) {
        prev = prev || LeafIterator.getSuccessor(textNode, true);
        var rendered = 0, rawLength = textNode.nodeValue.length;
        // A renderedOffset cannot be greater than its corresponding
        // rawOffset, so no need to try rawOffsets less than renderedOffset.
        for (var raw = renderedOffset; raw <= rawLength; ++raw) {
            rendered = XPath.renderedOffset(textNode, raw, prev);
            if (rendered >= renderedOffset) return raw;
        }
    },

    validXPathNode: function(node) {
        var contentful = !!(Element.infertile(node) || node.firstChild);
        var shouldIgnore = (Element.isTextNode(node) ||
            StyleParent.registered(node));
        return contentful && !shouldIgnore;
    },

    normalize: function(tuple) {
        if (!XPath.validXPathNode(tuple.node)) {
            tuple.offset += XPath.cumOffsetTo(tuple.node);
            tuple.node = tuple.node.parentNode;
            return arguments.callee(tuple);
        } else return tuple;
    },

    Counter: function(node, iter) {
        var start = Element.getLeaf(node);
        var end = Element.getLeaf(node, true);
        return LeafIterator(start, end, iter) || null;
    }
    
});

XPath.prototype = {
    
    locate: function() {
        return this._basicPath().concat(this.spot.offset);
    },

    toString: function() {
        return this.locate().join(':');
    },

    // The string representation is canonical, so we can use it to test
    // equality of XPaths:
    equals: function(other) {
        return (other instanceof XPath &&
                this+'' == other+'');
    },
        
    insertAt: function(node) {
        LeafIterator.register(node);
        var place = this._findInsertionPlace();
        if (!place)
            return this.spot.node.appendChild(node);
        
        if (Element.isTextNode(place.leaf)) {
            var rawOffset = XPath.rawOffset(place.leaf, place.offset);
            this._spliceIntoText(node, place.leaf, rawOffset);
        } else if (place.offset == 0)
            Element.insertBefore(node, place.leaf);
        else Element.insertAfter(node, place.leaf);

        return node;
    },
    
    getBaseNode: function(/*optional:*/ id_regex) {
        id_regex = id_regex || /^refbase_/;
        var node = this.spot.node;
        do if (id_regex.test(node.id)) return node;
        while ((node = node.parentNode));
        throw "XPath not contained by valid DOM element " + 
            "(some ancestor's id must match the regular expression " + 
            id_regex + ")."
    },
    
    updateWith: function(pointElement) {
        var tuple = { node: pointElement, offset: 0 };
        if (pointElement.parentNode)
            XPath.call(this, XPath.normalize(tuple));
    },
    
    _xIndex: function(node) {
        var n = 0, curr = node, tagName = node.tagName;
        while ((curr = curr.previousSibling))
            if (curr.tagName == tagName) ++n;
        return n > 0 ? '[' + n + ']' : '';
    },
    
    _basicPath: function() {
        var node = this.spot.node, result = '',
            base_node = this.getBaseNode();
        while (node && node !== base_node) {
            result = '/' + node.tagName +
                this._xIndex(node) + result;
            node = node.parentNode;
        }
        return [base_node.id, result];
    },

    _spliceIntoText: function(node, textNode, offset) {

        // This function assumes that the offset has been converted to a
        // rawOffset.  That conversion is done in XPath::insertAt.
        
        var prop, ownerDoc = getOwnerDoc(textNode);
        var pre = textNode.nodeValue.slice(0, offset),
            preNode = ownerDoc.createTextNode(pre);
        var post = textNode.nodeValue.slice(offset),
            postNode = ownerDoc.createTextNode(post);

        // Make sure that styleParents "hug" their children.  More
        // precisely, when we split the child of a styleParent, kill the
        // original styleParent and assign brand new styleParents to the
        // split parts (pre and post).
        
        var origSP = StyleParent.remove(textNode);
        textNode.parentNode.replaceChild(node, textNode);
        
        if (origSP) { // all style achieved through classNames
            var preNode = StyleParent.add(preNode);
            var postNode = StyleParent.add(postNode);
            preNode.className = postNode.className =
                origSP.className;
        }

        // refusing to create empty textNodes
        if (pre != '') Element.insertBefore(preNode, node);
        if (post != '') Element.insertAfter(postNode, node);
        
        return node;
    },

    _findInsertionPlace: function() {
        var cumOffset = this.spot.offset;
        return XPath.Counter(this.spot.node, function(leaf, length) {
            if (cumOffset - length <= 0)
                return { leaf: leaf, offset: cumOffset };
            cumOffset -= length;
        }) || null;
    }
    
};

// NOTE: start and end need to be leaves themselves; otherwise the
// behavior can be a little surprising!  Use Element.getLeaf to determine
// the first or last leaf descendant of a given non-leaf.
var LeafIterator = makeRegistry(function(start, end, iter) {
    var node, result, successors = LeafIterator.getSuccessors(start, end);
    while ((node = successors.shift()))
        if (!LeafIterator.registered(node)) {
            result = iter(node, LeafIterator.leafLength(node));
            if (typeof result != 'undefined')
                return result;
        }
});

// This registry will track the spans used to denote XPath endpoints, so
// that they can be ignored during leaf iteration.
Object.extend(LeafIterator, {
    
    leafLength: function(leaf) {
        if (Element.isTextNode(leaf))
            return XPath.renderedOffset(leaf, leaf.nodeValue.length);
        if (Element.infertile(leaf))
            return 1;
        return 0;
    },

    // includes node itself; use getSuccessors(node, stop).slice(1) if
    // this behavior is not desired
    getSuccessors: function(node, stop, backward) {
        var start = node, successors = [];
        while (node) {
            successors.push(node);
            if (node === stop) break;
            node = LeafIterator.getSuccessor(node, backward);
        }
        return successors;
    },
    
    getSuccessor: function(node, backward) {
        var whichSib = (backward ? 'previous' : 'next') + 'Sibling',
            startAt =  (backward ? 'last' : 'first') + 'Child';

        while (node && !node[whichSib])
            node = node.parentNode;

        if (node && node[whichSib])
            node = node[whichSib];

        while (node && node[startAt])
            node = node[startAt];
    
        return node;
    }
    
});
