document.addEventListener('DOMContentLoaded', () => {
  const inputText           = document.getElementById('inputText');
  const outputContainer     = document.getElementById('outputContainer');
  const convertButton       = document.getElementById('convertButton');
  const clearInputButton    = document.getElementById('clearInputButton');
  const copyButton          = document.getElementById('copyButton');
  const generateImageButton = document.getElementById('generateImageButton');
  const loadingStatus       = document.getElementById('loadingStatus');
  const compatMode          = document.getElementById('compatibilityMode');
  const modal               = document.getElementById('infoModal');
  const helpTrigger         = document.getElementById('helpTrigger');
  const closeModal          = document.getElementById('closeModal');
  const closeModalBtn       = document.getElementById('closeModalBtn');
  const modalOverlay        = document.getElementById('modalOverlay');
  const toast               = document.getElementById('toast');

  let mappings = { full: null, less: null };
  let currentRawResult = '';

  // 字典加载
  Promise.all([
    fetch('web_mapping.json').then(r => r.ok ? r.json() : Promise.reject('标准字典加载失败')),
    fetch('web_mapping_less.json').then(r => r.ok ? r.json() : Promise.reject('兼容字典加载失败')),
  ])
    .then(([full, less]) => {
      mappings.full = full;
      mappings.less = less;
      loadingStatus.style.display = 'none';
      convertButton.disabled = false;
      outputContainer.innerHTML =
        '<span class="output-placeholder">在此输入文字，点击转换</span>';
    })
    .catch(err => {
      loadingStatus.innerHTML =
        `<span style="color:var(--accent);font-size:0.82rem">${err}</span>`;
    });

  // 缺字集合（需要 SVG fallback 的生僻字）
  const missingCharsSet = new Set(Array.from(
    "𲛯𮱅𲛣𲛍𭒘𭒩𮱛𭒬𭒴𭒣𮱌𲛰𰌆𲛢𭑷𰋶𰌖𲛐𲛧𲛋𭒨𭒵𰋺𲛵𱙭𭒅𱙯𱙅𭶃𮰿𱙂𰌉𭒙𰌇𱙤𭒕𭒢𮱇𭒈𲡱𱙃𭒃𮱂𲛊𰌐𭒗𲛒𰌄𱙘𭤇𮱄𱙕𲛷𱻲𭑾𰋵𱙏𰋸𭒳𭒡𱙮𭒟𮰾𰌁𭒠𭒯𭑵𰌋𱙇𰌈𰗻𭒪𭒭𲛭𭒤𮱉𰋿𰿧𮰽𮰻𱙣𲛞𰇭𰌍𭑩𱙨𮱏𭒏𭑴𱙓𰌃𲛛𭑼𭒫𰌌𱙪𮱎𭒛𱙱𭒖𮱒𱙆𲛙𭒮𭒦𮱆𱙈𰌙𱙟𭂾𭒁𰌊𮱍𭑲𮆝𲛗𲛴𱙐𰋷𲛤𮱙𱨌𮱘𮱐𮰹𲛺𭑪𲽐𲛨𲛲𱙩𮓃𲛳𱙢𲛘𱙑𱦢𲛱𮰸𭑫𱙦𭔖𭒝𲛜𰌒𭑭𲛑𲛓𮱈𱙛𭒂𮱁𱙖𰋾𲛻𱙴𭒥𮍳𮱃𲛬𰌅𮱑𰋽𭑺𭑸𮱕𭒎𲛌𱙫𲛸𰋻𮱖𲛪𭑨𭒐𭒑𭑹𰌔𲛏𰌛𭒧𭑳𱙒𱙡𲛥𮱋𱙄𱙝𱙔𲛖𭒓𮱀𰌀𱙍𮱓𲛕𱙋𭑱𱙎𲛎𭒄𱙙𭒌𮰷𮱚𲛝𭑽𲛔𭤋𱙠𰋹𮰺𲛶𭒇𲛠𮱊𱙞𭑰𭑬𭒚𰌂𭒜𰌎𭑯𭑧𭒆𱙊𲛡𮱔𭑶𰌘𱼰𰌚𮰼𭴇𰋼𲛮𱆶𲛟𰐈𮣭𱀤𱙗𲛩𭑮𱙌𭒔𱙰𭑻𰌑𲍣𲛫𮱗𭒉𱙧𱙚𱙉𮡎𭒀𱙥𭒞𱙲𱙁"
  ));

  function getGlyphHtml(char) {
    const hex = char.codePointAt(0).toString(16).toLowerCase();
    const url = `https://glyphwiki.org/glyph/u${hex}.svg`;
    return `<span class="svg-icon" title="${char}" style="-webkit-mask-image:url('${url}');mask-image:url('${url}');"></span>`;
  }

  // ── 转换 ──────────────────────────────────────────
  convertButton.addEventListener('click', () => {
    if (!mappings.full || !mappings.less) return;

    const original = inputText.value;
    if (!original) { showToast('请输入需要转换的文字', true); return; }

    const mapping = compatMode.checked ? mappings.less : mappings.full;
    const rawParts = [];

    const htmlParts = Array.from(original).map(char => {
      const target = mapping[char] !== undefined ? mapping[char] : char;
      rawParts.push(target);

      if (missingCharsSet.has(target)) return getGlyphHtml(target);
      if (target === '<') return '&lt;';
      if (target === '>') return '&gt;';
      if (target === '&') return '&amp;';
      if (target === '\n') return '<br>';
      return target;
    });

    currentRawResult = rawParts.join('');
    outputContainer.innerHTML = htmlParts.join('');
  });

  // ── 清空 ──────────────────────────────────────────
  clearInputButton.addEventListener('click', () => {
    inputText.value = '';
    currentRawResult = '';
    outputContainer.innerHTML =
      '<span class="output-placeholder">在此输入文字，点击转换</span>';
    inputText.focus();
  });

  // ── 复制 ──────────────────────────────────────────
  copyButton.addEventListener('click', async () => {
    if (!currentRawResult) { showToast('尚无可复制的内容', true); return; }
    try {
      await navigator.clipboard.writeText(currentRawResult);
      showToast('已复制到剪贴板');
    } catch {
      const ta = document.createElement('textarea');
      ta.value = currentRawResult;
      ta.style.cssText = 'position:fixed;left:-9999px;top:0;';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy')
        ? showToast('已复制到剪贴板')
        : showToast('复制失败，请手动选择', true);
      document.body.removeChild(ta);
    }
  });

  // ── 生成图片 ──────────────────────────────────────
  generateImageButton.addEventListener('click', async () => {
    if (!currentRawResult) { showToast('请先转换文字', true); return; }

    showToast('正在生成图片...');

    const tmp = document.createElement('div');
    tmp.style.cssText = [
      'position:fixed;left:-9999px;top:0;',
      'width:600px;',
      'background:#F7F6F3;',
      'color:#1C1917;',
      'padding:48px;',
      'font-family:"HanaMinA","HanaMinB","Noto Serif SC",serif;',
      'font-size:1.4rem;',
      'line-height:1.7;',
      'word-break:break-word;',
      'white-space:pre-wrap;',
    ].join('');
    tmp.innerText = currentRawResult;
    document.body.appendChild(tmp);

    try {
      await document.fonts.ready;
      const canvas = await html2canvas(tmp, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#F7F6F3',
      });
      const link = document.createElement('a');
      link.download = `全女文_${Date.now()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      showToast('图片已下载');
    } catch (err) {
      console.error(err);
      showToast('生成图片失败', true);
    } finally {
      document.body.removeChild(tmp);
    }
  });

  // ── 说明弹窗 ──────────────────────────────────────
  helpTrigger.addEventListener('click', () => modal.classList.add('open'));
  closeModal.addEventListener('click', () => modal.classList.remove('open'));
  closeModalBtn.addEventListener('click', () => modal.classList.remove('open'));
  modalOverlay.addEventListener('click', () => modal.classList.remove('open'));
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') modal.classList.remove('open');
  });

  // ── Toast ─────────────────────────────────────────
  let toastTimer = null;
  function showToast(msg, isError = false) {
    toast.textContent = msg;
    toast.classList.toggle('error', isError);
    toast.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('visible'), 2500);
  }
});
