Class = {
  create: function(/*optional:*/ decl) {
    function ctor() {
      if (typeof this.initialize == 'function')
        this.initialize.apply(this, arguments);
    }
    decl = decl || {};
    ctor.prototype = (typeof decl == 'function')
      ? new decl() : decl;
    Class.inherit(ctor.prototype, decl.prototype || {});
    ctor.prototype.constructor = ctor;
    ctor.extend = Class._extend;
    ctor.inject = Class._inject;
    ctor.remove = Class._remove;
    return ctor;
  },

  inherit: function(self, parent) {
    for (var f in self)
      if (self[f] !== Object.prototype[f] && self[f] !== parent[f]
          && typeof self[f] == 'function')
        self[f] = Class.wrap(self[f], f, parent);
  },

  supRegExp: /\Wsup\s*(\(|[\'\"\[\.][^=]*?\()/,

  wrap: function(override, name, parent) {
    return Class.supRegExp.test(override) ? function() {
      var saved = this.sup; this.sup = parent[name];
      try { return override.apply(this, arguments); }
      finally { this.sup = saved; }
    } : override;
  },

  _extend: function(sub) {
    if (typeof sub != 'function')
      sub = Class.fnFromObj(sub);
    sub.prototype = this.prototype;
    return Class.create(sub);
  },

  _inject: function(name, value) {
    var old = this.prototype[name];
    this.prototype[name] = Class.wrap(value, 'prop', { prop: old });
    this.prototype[name]._base = old;
  },

  _remove: function(name) {
    var old = this.prototype[name]._base;
    delete this.prototype[name];
    if (old && old !== this.prototype[name])
      this.prototype[name] = old;
  },

  fnFromObj: function(obj) {
    return function() {
      for (var p in obj) this[p] = obj[p];
      this.toString = obj.toString;
      this.valueOf = obj.valueOf;
    }
  }
};
