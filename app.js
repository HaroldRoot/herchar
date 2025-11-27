document.addEventListener('DOMContentLoaded', () => {
    // DOM 元素获取
    const inputText = document.getElementById('inputText');
    const outputContainer = document.getElementById('outputContainer');

    // 按钮
    const convertButton = document.getElementById('convertButton');
    const clearInputButton = document.getElementById('clearInputButton');
    const copyButton = document.getElementById('copyButton');
    const generateImageButton = document.getElementById('generateImageButton');

    // 状态与选项
    const loadingStatus = document.getElementById('loadingStatus');
    const compatibilityModeCheckbox = document.getElementById('compatibilityMode');

    // 存储两个映射表
    let mappings = {
        full: null, // web_mapping.json
        less: null  // web_mapping_less.json
    };

    // 用于存储转换后的纯文本结果，以便复制使用
    let currentRawResult = "";

    // 并行加载两个字典文件
    Promise.all([
        fetch('web_mapping.json').then(res => res.ok ? res.json() : Promise.reject("标准字典加载失败")),
        fetch('web_mapping_less.json').then(res => res.ok ? res.json() : Promise.reject("兼容字典加载失败"))
    ])
        .then(([fullData, lessData]) => {
            mappings.full = fullData;
            mappings.less = lessData;

            loadingStatus.style.display = 'none';
            convertButton.disabled = false;
            convertButton.textContent = "✨立即转换";
            console.log(`字典加载成功: 标准版 ${Object.keys(fullData).length} 字, 兼容版 ${Object.keys(lessData).length} 字`);
        })
        .catch(error => {
            loadingStatus.innerHTML = `<span class="text-red-500">❌ 数据加载失败: ${error.message}</span>`;
            console.error('Error loading mappings:', error);
        });

    // 定义缺失字符集
    const missingCharsString = "𲛯𮱅𲛣𲛍𭒘𭒩𮱛𭒬𭒴𭒣𮱌𲛰𰌆𲛢𭑷𰋶𰌖𲛐𲛧𲛋𭒨𭒵𰋺𲛵𱙭𭒅𱙯𱙅𭶃𮰿𱙂𰌉𭒙𰌇𱙤𭒕𭒢𮱇𭒈𲡱𱙃𭒃𮱂𲛊𰌐𭒗𲛒𰌄𱙘𭤇𮱄𱙕𲛷𱻲𭑾𰋵𱙏𰋸𭒳𭒡𱙮𭒟𮰾𰌁𭒠𭒯𭑵𰌋𱙇𰌈𰗻𭒪𭒭𲛭𭒤𮱉𰋿𰿧𮰽𮰻𱙣𲛞𰇭𰌍𭑩𱙨𮱏𭒏𭑴𱙓𰌃𲛛𭑼𭒫𰌌𱙪𮱎𭒛𱙱𭒖𮱒𱙆𲛙𭒮𭒦𮱆𱙈𰌙𱙟𭂾𭒁𰌊𮱍𭑲𮆝𲛗𲛴𱙐𰋷𲛤𮱙𱨌𮱘𮱐𮰹𲛺𭑪𲽐𲛨𲛲𱙩𮓃𲛳𱙢𲛘𱙑𱦢𲛱𮰸𭑫𱙦𭔖𭒝𲛜𰌒𭑭𲛑𲛓𮱈𱙛𭒂𮱁𱙖𰋾𲛻𱙴𭒥𮍳𮱃𲛬𰌅𮱑𰋽𭑺𭑸𮱕𭒎𲛌𱙫𲛸𰋻𮱖𲛪𭑨𭒐𭒑𭑹𰌔𲛏𰌛𭒧𭑳𱙒𱙡𲛥𮱋𱙄𱙝𱙔𲛖𭒓𮱀𰌀𱙍𮱓𲛕𱙋𭑱𱙎𲛎𭒄𱙙𭒌𮰷𮱚𲛝𭑽𲛔𭤋𱙠𰋹𮰺𲛶𭒇𲛠𮱊𱙞𭑰𭑬𭒚𰌂𭒜𰌎𭑯𭑧𭒆𱙊𲛡𮱔𭑶𰌘𱼰𰌚𮰼𭴇𰋼𲛮𱆶𲛟𰐈𮣭𱀤𱙗𲛩𭑮𱙌𭒔𱙰𭑻𰌑𲍣𲛫𮱗𭒉𱙧𱙚𱙉𮡎𭒀𱙥𭒞𱙲𱙁";
    const missingCharsSet = new Set(Array.from(missingCharsString));

    // 辅助函数：获取字符的 GlyphWiki SVG URL
    // GlyphWiki 格式通常为: https://glyphwiki.org/glyph/u[hex].svg
    function getGlyphHtml(char) {
        // 使用 codePointAt 获取正确的 Unicode 码点 (支持 4字节字符)
        const codePoint = char.codePointAt(0);
        const hexCode = codePoint.toString(16).toLowerCase();
        const url = `https://glyphwiki.org/glyph/u${hexCode}.svg`;

        return `<span class="svg-icon" title="${char}" style="-webkit-mask-image: url('${url}'); mask-image: url('${url}');"></span>`;
    }

    // 转换按钮点击事件
    convertButton.addEventListener('click', () => {
        if (!mappings.full || !mappings.less) return;

        const originalText = inputText.value;
        if (!originalText) {
            showMessage('请输入需要转换的文字', 'error');
            return;
        }

        const useLess = compatibilityModeCheckbox?.checked;
        const currentMapping = useLess ? mappings.less : mappings.full;

        console.log(`开始转换，当前模式: ${useLess ? '兼容模式' : '标准模式'}`);

        let rawResultArray = [];
        const convertedHtmlArray = Array.from(originalText).map(char => {
            let targetChar = currentMapping[char] || char;

            // 存入纯文本数组，供复制使用
            rawResultArray.push(targetChar);

            // 处理特殊显示
            if (missingCharsSet.has(targetChar)) {
                return getGlyphHtml(targetChar);
            }

            // HTML 转义
            if (targetChar === '<') return '&lt;';
            if (targetChar === '>') return '&gt;';
            if (targetChar === '&') return '&amp;';
            if (targetChar === '\n') return '<br>'; // 处理换行

            return targetChar;
        });

        // 更新全局状态
        currentRawResult = rawResultArray.join('');

        // 更新 UI
        outputContainer.innerHTML = convertedHtmlArray.join('');

        // 反馈
        if (originalText === currentRawResult && !originalText.split('').some(c => missingCharsSet.has(c))) {
            showMessage('没有检测到可转换的字符', 'error');
        } else {
            showMessage('转换完成！');
        }
    });

    // 清空输入按钮点击事件
    clearInputButton.addEventListener('click', () => {
        if (!inputText.value && outputContainer.innerHTML === '') return;

        inputText.value = '';
        outputContainer.innerHTML = ''; // 修正：div 使用 innerHTML 清空
        currentRawResult = ''; // 清空缓存的文本
        inputText.focus();
        showMessage('输入已清空', 'success');
    });

    // 生成图片按钮点击事件
    generateImageButton.addEventListener('click', async () => {
        const textContent = outputText.value;

        if (!textContent) {
            showMessage('请先转换文字后再生成图片', 'error');
            return;
        }

        showMessage('🖼️ 正在生成图片，请稍候...', 'success');

        // 创建临时容器
        const tempContainer = document.createElement('div');
        tempContainer.style.position = 'fixed';
        tempContainer.style.left = '-9999px';
        tempContainer.style.top = '0';

        const maxWidth = 500;
        const viewportWidth = Math.min(window.innerWidth, maxWidth);
        tempContainer.style.width = viewportWidth + 'px';

        // 白底黑字，无边框
        tempContainer.style.backgroundColor = '#ffffff';
        tempContainer.style.color = '#000000';
        tempContainer.style.padding = '32px';
        tempContainer.style.border = 'none';

        // 字体
        tempContainer.style.fontFamily = '"HanaMinA", "HanaMinB", serif';
        tempContainer.style.fontSize = '1.6rem';
        tempContainer.style.fontWeight = '1000';
        tempContainer.style.lineHeight = '1.4';
        tempContainer.style.wordBreak = 'break-word';
        tempContainer.style.whiteSpace = 'pre-wrap'; // 自动换行并保留换行符

        // 内容
        tempContainer.innerText = textContent;

        document.body.appendChild(tempContainer);

        try {
            await document.fonts.ready;

            const canvas = await html2canvas(tempContainer, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff'
            });

            const link = document.createElement('a');
            link.download = `全女文转换_${Date.now()}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();

            showMessage('✅ 图片已生成并下载！');
        } catch (err) {
            console.error(err);
            showMessage('生成图片失败，请重试', 'error');
        } finally {
            document.body.removeChild(tempContainer);
        }
    });


    // 复制结果按钮点击事件
    copyButton.addEventListener('click', async function () {
        // 使用 currentRawResult 确保复制的是字符本身，而不是 HTML 代码
        const textToCopy = currentRawResult;

        if (!textToCopy) {
            showMessage('输出内容为空，无需复制。', 'error');
            return;
        }

        // 使用现代 Clipboard API
        try {
            await navigator.clipboard.writeText(textToCopy);
            showMessage('✅ 成功复制到剪贴板！');
        } catch (err) {
            console.error('Clipboard API failed:', err);
            // 降级方案：创建一个临时 textarea
            fallbackCopyText(textToCopy);
        }
    });

    // 降级复制方案 (兼容旧浏览器或非 HTTPS 环境)
    function fallbackCopyText(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;

        // 确保元素不可见但存在于 DOM 中
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        document.body.appendChild(textArea);

        textArea.focus();
        textArea.select();

        try {
            const successful = document.execCommand('copy');
            if (successful) {
                showMessage('✅ 成功复制到剪贴板！');
            } else {
                showMessage('复制失败，请手动选择并复制。', 'error');
            }
        } catch (err) {
            showMessage('复制操作出现错误。', 'error');
        }

        document.body.removeChild(textArea);
    }

    const modal = document.getElementById('infoModal');
    const trigger = document.getElementById('helpTrigger');
    const closeIcon = document.getElementById('closeModal');
    const closeBtn = document.getElementById('closeModalBtn');
    const overlay = document.getElementById('modalOverlay');

    // 打开弹窗函数
    const openModal = () => {
        modal.classList.remove('hidden');
        // 简单的淡入动画逻辑
        modal.animate([
            { opacity: 0 },
            { opacity: 1 }
        ], {
            duration: 200,
            easing: 'ease-out'
        });
    };

    // 关闭弹窗函数
    const closeModal = () => {
        const animation = modal.animate([
            { opacity: 1 },
            { opacity: 0 }
        ], {
            duration: 150,
            easing: 'ease-in'
        });

        animation.onfinish = () => {
            modal.classList.add('hidden');
        };
    };

    // 绑定事件
    trigger.addEventListener('click', openModal);
    closeIcon.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', closeModal);

    // ESC 键关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });

    function showMessage(message, type = 'success') {
        const container = document.body;
        let messageBox = document.getElementById('messageBox');

        if (!messageBox) {
            messageBox = document.createElement('div');
            messageBox.id = 'messageBox';
            messageBox.className = 'fixed top-6 left-1/2 transform -translate-x-1/2 p-4 shadow-neon-pink opacity-0 transition-opacity duration-300 z-50 text-vapor-bg font-heading font-bold text-center border-2 border-white rounded-none uppercase tracking-widest min-w-[200px]';
            container.appendChild(messageBox);
        }

        let bgColor = 'bg-vapor-secondary';
        if (type === 'success') {
            bgColor = 'bg-vapor-accent';
            messageBox.style.boxShadow = '0 0 15px #05ffa1';
        } else if (type === 'error') {
            bgColor = 'bg-vapor-primary';
            messageBox.style.boxShadow = '0 0 15px #ff71ce';
        }

        messageBox.className = `fixed top-6 left-1/2 transform -translate-x-1/2 p-4 opacity-0 transition-opacity duration-300 z-50 text-vapor-bg font-heading font-bold text-center border-0 rounded-none uppercase tracking-widest min-w-[200px] ${bgColor}`;

        messageBox.textContent = message;
        messageBox.style.opacity = 1;

        clearTimeout(messageBox.timer);
        messageBox.timer = setTimeout(() => {
            messageBox.style.opacity = 0;
        }, 3000);
    }
});