function renderMathText(node, text, errorLabel) {
  node.replaceChildren();
  const parts = text.split(/(`[^`\n]+`|\\\$|\$\$[\s\S]+?\$\$|\$(?:\\.|[^$\\\n])+\$)/g);
  for (const [index, part] of parts.entries()) {
    if (index % 2 === 0) {
      node.append(document.createTextNode(part));
    } else if (part.startsWith('`')) {
      const code = document.createElement('code');
      code.textContent = part.slice(1, -1);
      node.append(code);
    } else if (part === '\\$') {
      node.append(document.createTextNode('$'));
    } else {
      const displayMode = part.startsWith('$$');
      const delimiter = displayMode ? 2 : 1;
      const math = document.createElement('span');
      math.className = displayMode ? 'fc-math fc-math-display' : 'fc-math';
      try {
        // The string renderer supports MathML in standards and quirks mode.
        math.innerHTML = katex.renderToString(part.slice(delimiter, -delimiter), {
          output: 'mathml', displayMode, trust: false, strict: 'error',
          throwOnError: true, maxExpand: 1000, maxSize: 20, macros: {}
        });
      } catch (_) {
        math.textContent = part;
        math.dataset.mathError = 'true';
        math.setAttribute('aria-label', errorLabel);
      }
      node.append(math);
    }
  }
}
