# 全女文转换器 / Her Character Converter

将任意汉字文本转换为含「女」部件的汉字，基于 Unicode IDS（表意文字描述序列）部件分析。

**在线体验**：[herchar.github.io/herchar](https://haroldroot.github.io/herchar)（GitHub Pages）

---

## 工作原理

1. 所有汉字都可以被分解为基本部件（如：妈 = 女 + 马）
2. 对于输入的每个汉字，在含「女」的汉字集合中寻找结构相同或相似的字
3. 匹配策略：IDS 部件精确匹配 → 单部件提取 → 拼音同音兜底

**兼容模式**：仅输出 BMP 常用汉字区的结果，避免因缺少字体而显示「豆腐块」。

---

## 本地运行

### 数据重建（可选）

原始数据来自 [CHISE IDS 数据库](https://gitlab.chise.org/CHISE/ids)，已包含于 `raw_data/`。

```bash
pip install pypinyin
python build.py           # 重建 web_mapping.json
```

### 前端预览

直接用浏览器打开 `index.html`，或：

```bash
python -m http.server 8080
# 访问 http://localhost:8080
```

---

## 部署

推送到 GitHub，在 Settings → Pages 中设置来源为 `main` 分支根目录即可。所有资源均为静态文件。

---

## 字体说明

页面通过 CDN 加载**花園明朝**（HanaMinA/HanaMinB），以覆盖尽可能多的 Unicode 汉字范围（包括 CJK Ext-B 至 Ext-J）。首次加载可能较慢。

---

## 数据来源

IDS 数据：[CHISE IDS](https://gitlab.chise.org/CHISE/ids)（LGPL）
