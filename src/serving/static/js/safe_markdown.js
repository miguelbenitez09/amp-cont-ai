(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.SafeMarkdown = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function inline(value) {
    let text = escapeHtml(value);
    text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    return text;
  }

  function render(markdown) {
    const lines = String(markdown == null ? "" : markdown).replace(/\r\n?/g, "\n").split("\n");
    const output = [];
    let inCode = false;
    let code = [];
    let listType = null;

    function closeList() {
      if (listType) output.push(`</${listType}>`);
      listType = null;
    }

    lines.forEach(function (line) {
      if (/^```/.test(line)) {
        closeList();
        if (inCode) {
          output.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
          code = [];
        }
        inCode = !inCode;
        return;
      }
      if (inCode) { code.push(line); return; }

      const heading = line.match(/^(#{1,4})\s+(.+)$/);
      if (heading) {
        closeList();
        const level = heading[1].length;
        output.push(`<h${level}>${inline(heading[2])}</h${level}>`);
        return;
      }
      const unordered = line.match(/^\s*[-*]\s+(.+)$/);
      const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
      if (unordered || ordered) {
        const wanted = ordered ? "ol" : "ul";
        if (listType !== wanted) { closeList(); output.push(`<${wanted}>`); listType = wanted; }
        output.push(`<li>${inline((ordered || unordered)[1])}</li>`);
        return;
      }
      closeList();
      if (!line.trim()) output.push("");
      else output.push(`<p>${inline(line)}</p>`);
    });
    if (inCode) output.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
    closeList();
    return output.join("\n");
  }

  return { escapeHtml: escapeHtml, render: render };
});
