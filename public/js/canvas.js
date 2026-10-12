// "Redraw from memory": a small drawing canvas (pen, colours, eraser). Renox has no drawing
// component. On submit the canvas becomes a PNG in the form's file input; no CDN, no library.
(function () {
  function init(canvas) {
    var ctx = canvas.getContext("2d", { willReadFrequently: true });
    var form = canvas.closest("form");
    var state = { tool: "pen", color: "#111827", size: 3, drawing: false, dirty: false, undo: [] };
    function blank() { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, canvas.width, canvas.height); }
    blank();
    function pos(e) {
      var r = canvas.getBoundingClientRect();
      return [(e.clientX - r.left) * canvas.width / r.width, (e.clientY - r.top) * canvas.height / r.height];
    }
    function snapshot() {
      if (state.undo.length > 20) state.undo.shift();
      state.undo.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
    }
    function begin(e) {
      snapshot();
      state.drawing = true;
      canvas.setPointerCapture(e.pointerId);
      var p = pos(e);
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      ctx.strokeStyle = state.tool === "eraser" ? "#fff" : state.color;
      ctx.lineWidth = state.tool === "eraser" ? state.size * 4 : state.size;
      ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(p[0] + 0.01, p[1]); ctx.stroke();
      state.dirty = true;
      e.preventDefault();
    }
    function move(e) {
      if (!state.drawing) return;
      var p = pos(e); ctx.lineTo(p[0], p[1]); ctx.stroke();
    }
    function end() { state.drawing = false; }
    canvas.addEventListener("pointerdown", begin);
    canvas.addEventListener("pointermove", move);
    canvas.addEventListener("pointerup", end);
    canvas.addEventListener("pointercancel", end);

    function setTool(t) {
      state.tool = t;
      form.querySelectorAll("[data-tool]").forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-tool") === t ? "true" : "false");
      });
    }
    function pick(selector, attr, apply) {
      form.querySelectorAll(selector).forEach(function (b) {
        b.addEventListener("click", function () {
          form.querySelectorAll(selector).forEach(function (o) { o.setAttribute("aria-pressed", "false"); });
          b.setAttribute("aria-pressed", "true");
          apply(b.getAttribute(attr));
        });
      });
    }
    pick("[data-color]", "data-color", function (v) { state.color = v; setTool("pen"); });
    pick("[data-size]", "data-size", function (v) { state.size = parseInt(v, 10); });
    form.querySelectorAll("[data-tool]").forEach(function (b) {
      b.addEventListener("click", function () { setTool(b.getAttribute("data-tool")); });
    });
    form.querySelector("[data-undo]").addEventListener("click", function () {
      var last = state.undo.pop();
      if (last) ctx.putImageData(last, 0, 0);
    });
    form.querySelector("[data-clear]").addEventListener("click", function () {
      snapshot(); blank(); state.dirty = false;
    });

    // Turn the canvas into a PNG file in the form's file input, then send the form.
    form.addEventListener("submit", function (e) {
      var input = form.querySelector('input[type="file"][name="image"]');
      if (!state.dirty || !input || (input.files && input.files.length)) return; // a photo wins
      e.preventDefault();
      canvas.toBlob(function (blob) {
        var dt = new DataTransfer();
        dt.items.add(new File([blob], "drawing.png", { type: "image/png" }));
        input.files = dt.files;
        form.submit();
      }, "image/png");
    });
  }

  function timer(el) {
    var left = parseInt(el.getAttribute("data-seconds"), 10), id = null;
    var start = document.querySelector("[data-redraw-timer-start]");
    if (!start) return;
    start.addEventListener("click", function () {
      if (id) return;
      id = setInterval(function () {
        left -= 1;
        if (left <= 0) { clearInterval(id); el.textContent = "Time is up!"; return; }
        var s = left % 60;
        el.textContent = Math.floor(left / 60) + ":" + (s < 10 ? "0" : "") + s;
      }, 1000);
    });
  }

  document.querySelectorAll("[data-redraw-canvas]").forEach(init);
  document.querySelectorAll("[data-redraw-timer]").forEach(timer);
})();
