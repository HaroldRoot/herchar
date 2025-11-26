document.addEventListener('DOMContentLoaded', () => {
    // DOM 元素获取
    const inputText = document.getElementById('inputText');
    const outputText = document.getElementById('outputText');

    // 按钮
    const convertButton = document.getElementById('convertButton');
    const clearInputButton = document.getElementById('clearInputButton'); // 新增
    const copyButton = document.getElementById('copyButton');
    const generateImageButton = document.getElementById('generateImageButton'); // 新增

    // 状态与选项
    const loadingStatus = document.getElementById('loadingStatus');
    const compatibilityModeCheckbox = document.getElementById('compatibilityMode'); // 新增

    // 存储两个映射表
    let mappings = {
        full: null, // web_mapping.json
        less: null  // web_mapping_less.json
    };

    // 并行加载两个字典文件
    Promise.all([
        fetch('web_mapping.json').then(res => {
            if (!res.ok) throw new Error("无法读取标准字典");
            return res.json();
        }),
        fetch('web_mapping_less.json').then(res => {
            if (!res.ok) throw new Error("无法读取兼容字典");
            return res.json();
        })
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

    // 转换按钮点击事件
    convertButton.addEventListener('click', () => {
        // 检查数据是否加载完成
        if (!mappings.full || !mappings.less) return;

        const originalText = inputText.value;
        if (!originalText) {
            showMessage('请输入需要转换的文字', 'error');
            return;
        }

        // 根据复选框状态选择字典
        const useLess = compatibilityModeCheckbox.checked;
        const currentMapping = useLess ? mappings.less : mappings.full;

        console.log(`开始转换，当前模式: ${useLess ? '兼容模式' : '标准模式'}`);

        const convertedText = Array.from(originalText).map(char => {
            return currentMapping[char] || char;
        }).join('');

        outputText.value = convertedText;

        if (originalText === convertedText) {
            showMessage('没有检测到可转换的字符', 'error');
        } else {
            showMessage('转换完成！');
        }
    });

    // 清空输入按钮点击事件
    clearInputButton.addEventListener('click', () => {
        if (!inputText.value && !outputText.value) return;
        inputText.value = '';
        outputText.value = '';
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
    copyButton.addEventListener('click', function () {
        if (!outputText.value) {
            showMessage('输出内容为空，无需复制。', 'error');
            return;
        }
        outputText.select();
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
    });

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