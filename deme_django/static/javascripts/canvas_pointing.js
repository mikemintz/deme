var DemeCanvasPointing = function() {
    var pub = {};

    var srcJq = null;
    var trgJq = null;

    function clear() {
    }

    function redraw() {
        var canvasJq = $("#pointing_canvas");
		var canvasEl = canvasJq[0];
		canvasEl.width = document.documentElement.scrollWidth;
		canvasEl.height = document.documentElement.scrollHeight;
		var cOffset = canvasJq.offset();
		var ctx = canvasEl.getContext("2d");
		ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
        if (srcJq != null && trgJq != null && srcJq.length && trgJq.length && srcJq.is(":visible") && trgJq.is(":visible")) {
            ctx.beginPath();
            var srcOffset = srcJq.offset();
            var srcMidHeight = srcJq.height() / 2;
            var trgOffset = trgJq.offset();
            var trgMidHeight = srcJq.height() / 2;
            ctx.strokeStyle = "#c00";
            ctx.moveTo(srcOffset.left - cOffset.left, srcOffset.top - cOffset.top + srcMidHeight);
            ctx.lineTo(trgOffset.left - cOffset.left, trgOffset.top - cOffset.top + trgMidHeight);
            ctx.stroke();
            ctx.closePath();
        }
    }

    function redrawIfActive() {
        if (srcJq != null && trgJq != null) {
            redraw();
        }
    }

    function redrawTimer() {
        redrawIfActive();
        setTimeout(redrawTimer, 250);
    }

	pub.drawLine = function(newSrcJq, newTrgJq) {
        srcJq = newSrcJq;
        trgJq = newTrgJq;
        redraw();
	};

    pub.clearLine = function() {
        srcJq = null;
        trgJq = null;
        redraw();
    }

    pub.setup = function() {
        $(document).ready(function(){
            $('body').prepend('<canvas id="pointing_canvas" style="position: absolute; z-index: -100;"></canvas>');
        });
        redrawTimer();
    };

    return pub;
}();

