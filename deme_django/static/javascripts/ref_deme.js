
var highlight = makeRegistry(function(/*optional:*/ start, end) {
    var region = (start && end)
        ? new Region(start, end)
        : Region.fromSelection();
    if (!region) return;
    region.highlight();
    highlight.registered.map(function(listener) {
        listener.regionMarked(region);
    });
});

function ref_bless(refbase, /*optional*/ id) {
    refbase = $(refbase);
    if (!id || id == '') 
        id = new Date().getTime() + '' +
            (Math.random() + '').split('.').join('');
    if (!/refbase_.*/.test(refbase.id))
        refbase.id = 'refbase_' + id;
    Event.observe(refbase, 'mouseup', highlight);
}

function concoctPostBody(params, /*optional:*/ form) {
    form = form || document.createElement('form');
    function addParam(name, value) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        return form.appendChild(input);
    }
    for (var name in params) { // TODO avoid default properties
        if (params[name] !== ({})[name]) {
            if (!(params[name] instanceof Array))
                params[name] = [params[name]];
            params[name].each(function(val) { addParam(name, val); });
        }
    }
    return Form.serialize(form);
}

var RegionManager = Class.create(function(RegionManager) {
    
    this.initialize = function() {
        highlight.register(this);
        this.regions = [];
        this.cached_regions = [];
    };
    
    this.regionMarked = function(region) {
        this.regions.push(region);
        if (this._form)
            concoctPostBody({
                regions: [region]
            }, this._form);
    };
    
    this.clear = function() {
        var region;
        while ((region = this.regions.pop()))
            region.highlight(false);
    };
    
    function getActualForm(id_or_parent) {
        var form = $(id_or_parent);
        if (!/form/i.test(form.tagName))
            form = form.getElementsByTagName('form')[0];
        return form;
    }
    
    this.setForm = function(form) {
        this._form = getActualForm(form);
        this.stowRegions(this._form);
    };
    
    this.stowRegions = function(form) {
        form = getActualForm(form);
        concoctPostBody({
            regions: this.regions
        }, form);
    };
    
    this.transmit = function(callback) {
        if (this.regions.length > 0) {
            var url = '/meeting_area/register_region_set/' +
                /(\?[^?]*)$/.exec(window.location)[1];
            new Ajax.Request(url, {
                method: 'post',
                postBody: concoctPostBody({ regions: this.regions.join("\n") }),
                onSuccess: (function() {
                    this.clear();
                    callback.apply(this, arguments);
                }).bind(this)
            });
        } else alert("Please select one or more regions in the item text " + 
                     "before creating a reference link.")
    };
    
    this.hl = this.requestAndHighlight = function(ref_id) {
        var andHighlight = (function(regions) {
            this.clear();
            regions.each(function(region) {
                highlight.apply(null, region);
            });
        }).bind(this);
        
        var cached = this.cached_regions[ref_id];
        if (cached) andHighlight(cached);
        else this.request(ref_id, andHighlight);
    };
    
    this.request = function(ref_id, callback) {
        var url = '/resource/textdocument/getregions/';
        //var url = '/meeting_area/get_regions/' + ref_id +
        //    /(\?[^?]*)$/.exec(window.location)[1];
        new Ajax.Request(url, {
            method: 'get',
            onSuccess: (function(transport) { 
                callback(this.cached_regions[ref_id] =
                         eval(transport.responseText));
            }).bind(this)
        });
    };
    
    this.getLinkHtml = function(id, txt) {
        var jscmd = "gRegMgr.hl(" + id + ")";
        var linkHtml = "<a href='javascript:void(0)' onclick='" +
            jscmd + "'>" + txt + "</a>";
        return linkHtml;
    }
    
    this.interpolate = function(textarea) {
        var cb = this.getLinkHtml.bind(this);
        this.transmit(function(transport) {
            var ref_id = transport.responseText;
            _interpCb(textarea, cb.bind(null, ref_id));
        });
    };
    
    var _interpCb = function(e, callback) {
        if (document.selection) {
            e.focus();
            var range = document.selection.createRange();
            range.text = callback(range.text);
        } else {
            var start = e.selectionStart, end = e.selectionEnd,
                v = callback(e.value.slice(start, end));
                
            // XXX necessary?
            if (end == 1 || end == 2 && e.textLength != undefined)
                end = e.textLength;
                
            e.value = e.value.slice(0, start) + v + e.value.slice(end);
            e.selectionStart = start;
            e.selectionEnd = start + v.length;
        }
        e.focus();
    };
    
});

var gRegMgr = new RegionManager();
