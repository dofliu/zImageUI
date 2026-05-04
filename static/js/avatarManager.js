/**
 * Avatar Manager - Avatar Studio 前端邏輯
 *
 * 功能：
 *  - 動態渲染功能清單
 *  - 圖片上傳 / 預覽 / 遮罩繪製
 *  - 各功能的參數表單
 *  - 呼叫 /avatar/generate API
 */
(function () {
    'use strict';

    // ── 狀態 ────────────────────────────────────────────────────
    let currentFeature = null;
    let allFeatures = [];
    let imageData = { img1: null, img2: null };  // { dataUrl, mimeType }
    let maskCanvas = null;
    let maskCtx = null;
    let isDrawing = false;

    // ── 初始化 ──────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        loadFeatures();
        bindStaticEvents();
        checkCloudModel();
    });

    async function loadFeatures() {
        try {
            const res = await fetch('/avatar/features');
            const data = await res.json();
            if (data.success) {
                allFeatures = data.features;
                renderFeatureGrid();
            }
        } catch (e) {
            document.getElementById('featureGrid').innerHTML =
                '<div class="feature-loading" style="color:var(--at-err,#ef4444)">載入失敗，請重新整理</div>';
        }
    }

    function checkCloudModel() {
        // 若沒有雲端模型就緒，顯示提示
        setTimeout(() => {
            const ms = window.ModelSelector;
            if (!ms) return;
            const active = ms.getActiveModel?.();
            const hint = document.getElementById('cloudModelHint');
            if (hint) {
                hint.style.display = (!active || active.provider_type === 'local') ? 'block' : 'none';
            }
        }, 1500);
    }

    // ── 功能網格 ─────────────────────────────────────────────────
    function renderFeatureGrid() {
        const grid = document.getElementById('featureGrid');
        if (!grid) return;
        grid.innerHTML = allFeatures.map(f => `
            <div class="feature-card" data-id="${f.id}" title="${f.description}">
                <div class="feature-card-icon">${f.icon}</div>
                <div class="feature-card-name">${f.name}</div>
                <div class="feature-card-desc">${f.description}</div>
            </div>
        `).join('');

        grid.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('click', () => selectFeature(card.dataset.id));
        });
    }

    // ── 功能選擇 ─────────────────────────────────────────────────
    function selectFeature(featureId) {
        const feature = allFeatures.find(f => f.id === featureId);
        if (!feature) return;

        currentFeature = feature;

        // 更新 sidebar active 狀態
        document.querySelectorAll('.feature-card').forEach(c => {
            c.classList.toggle('active', c.dataset.id === featureId);
        });

        // 顯示工作區
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('workArea').style.display = 'flex';

        // 更新標題
        document.getElementById('featureIcon').textContent = feature.icon;
        document.getElementById('featureName').textContent = feature.name;
        document.getElementById('featureDesc').textContent = feature.description;

        // 上傳區顯示邏輯
        const img1Card = document.getElementById('imageUploadCard');
        const img2Card = document.getElementById('image2UploadCard');
        const maskSection = document.getElementById('maskSection');

        img1Card.style.display = feature.needs_image !== false ? 'flex' : 'none';
        img2Card.style.display = feature.needs_image2 ? 'flex' : 'none';
        maskSection.style.display = feature.needs_mask ? 'block' : 'none';

        // 第二張圖標籤
        const labelMap = {
            'tryon': '服裝圖片',
            'fusion': '第二位人物',
            'figure': '第二位人物（雙人模式）',
        };
        document.getElementById('image2Label').textContent = labelMap[featureId] || '第二張圖片';

        // 重置上傳（切換功能時清空）
        resetImages();

        // 渲染參數表單
        renderParams(feature);

        // 如果是 inpaint，初始化遮罩
        if (featureId === 'inpaint') {
            setTimeout(initMaskCanvas, 100);
        }

        // 更新按鈕狀態
        updateGenerateBtn();
    }

    function resetImages() {
        clearImage(1);
        clearImage(2);
        const result = document.getElementById('resultSection');
        if (result) result.style.display = 'none';
    }

    // ── 圖片上傳 ─────────────────────────────────────────────────
    function bindStaticEvents() {
        // 返回按鈕
        document.getElementById('backBtn')?.addEventListener('click', () => {
            document.getElementById('emptyState').style.display = 'flex';
            document.getElementById('workArea').style.display = 'none';
            document.querySelectorAll('.feature-card').forEach(c => c.classList.remove('active'));
            currentFeature = null;
        });

        // 前往設定
        document.getElementById('gotoSettingsLink')?.addEventListener('click', (e) => {
            e.preventDefault();
            window.ModelSelector?.openSettings?.();
        });

        // 上傳區
        bindDropZone(1);
        bindDropZone(2);

        // 生成按鈕
        document.getElementById('generateBtn')?.addEventListener('click', generate);

        // 結果操作
        document.getElementById('useAsInputBtn')?.addEventListener('click', useResultAsInput);
    }

    function bindDropZone(num) {
        const zone = document.getElementById(`dropZone${num}`);
        const input = document.getElementById(`fileInput${num}`);
        const clear = document.getElementById(`clearImg${num}`);

        if (!zone || !input) return;

        zone.addEventListener('click', () => input.click());
        input.addEventListener('change', (e) => {
            if (e.target.files[0]) loadImage(e.target.files[0], num);
        });
        zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('drag-over'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) loadImage(file, num);
        });

        clear?.addEventListener('click', (e) => { e.stopPropagation(); clearImage(num); });
    }

    function loadImage(file, num) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const dataUrl = e.target.result;
            const mime = file.type;
            imageData[`img${num}`] = { dataUrl, mimeType: mime };
            showPreview(dataUrl, num);

            // inpaint 模式：更新遮罩底圖
            if (num === 1 && currentFeature?.id === 'inpaint') {
                setTimeout(initMaskCanvas, 100);
            }
            updateGenerateBtn();
        };
        reader.readAsDataURL(file);
    }

    function showPreview(dataUrl, num) {
        const placeholder = document.getElementById(`placeholder${num}`);
        const preview = document.getElementById(`preview${num}`);
        const clear = document.getElementById(`clearImg${num}`);
        if (placeholder) placeholder.style.display = 'none';
        if (preview) { preview.src = dataUrl; preview.style.display = 'block'; }
        if (clear) clear.style.display = 'flex';
    }

    function clearImage(num) {
        imageData[`img${num}`] = null;
        const placeholder = document.getElementById(`placeholder${num}`);
        const preview = document.getElementById(`preview${num}`);
        const clear = document.getElementById(`clearImg${num}`);
        const input = document.getElementById(`fileInput${num}`);
        if (placeholder) placeholder.style.display = 'flex';
        if (preview) { preview.src = ''; preview.style.display = 'none'; }
        if (clear) clear.style.display = 'none';
        if (input) input.value = '';
        updateGenerateBtn();
    }

    function updateGenerateBtn() {
        const btn = document.getElementById('generateBtn');
        if (!btn || !currentFeature) { if (btn) btn.disabled = true; return; }
        const needImg1 = currentFeature.needs_image !== false;
        const needImg2 = currentFeature.needs_image2;
        const ok = (!needImg1 || imageData.img1) && (!needImg2 || imageData.img2);
        btn.disabled = !ok;
    }

    // ── 遮罩畫布（Inpainting 用）────────────────────────────────
    function initMaskCanvas() {
        const canvas = document.getElementById('maskCanvas');
        if (!canvas) return;
        maskCanvas = canvas;
        maskCtx = canvas.getContext('2d');

        const img = imageData.img1;
        if (img) {
            const image = new Image();
            image.onload = () => {
                canvas.width = image.naturalWidth;
                canvas.height = image.naturalHeight;
                canvas.style.maxHeight = '320px';
                maskCtx.drawImage(image, 0, 0);
            };
            image.src = img.dataUrl;
        } else {
            canvas.width = 512;
            canvas.height = 512;
            maskCtx.fillStyle = '#1a1a1a';
            maskCtx.fillRect(0, 0, 512, 512);
        }

        canvas.addEventListener('mousedown', startDraw);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDraw);
        canvas.addEventListener('mouseleave', stopDraw);

        document.getElementById('clearMaskBtn')?.addEventListener('click', () => {
            if (imageData.img1) {
                const image = new Image();
                image.onload = () => maskCtx.drawImage(image, 0, 0);
                image.src = imageData.img1.dataUrl;
            } else {
                maskCtx.clearRect(0, 0, canvas.width, canvas.height);
            }
        });
    }

    function startDraw(e) {
        isDrawing = true;
        drawAt(e);
    }

    function draw(e) {
        if (!isDrawing) return;
        drawAt(e);
    }

    function stopDraw() { isDrawing = false; }

    function drawAt(e) {
        const rect = maskCanvas.getBoundingClientRect();
        const scaleX = maskCanvas.width / rect.width;
        const scaleY = maskCanvas.height / rect.height;
        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;
        const size = parseInt(document.getElementById('brushSize')?.value || '20');

        maskCtx.globalCompositeOperation = 'source-over';
        maskCtx.fillStyle = 'rgba(255,255,255,0.85)';
        maskCtx.beginPath();
        maskCtx.arc(x, y, size, 0, Math.PI * 2);
        maskCtx.fill();
    }

    function getMaskBase64() {
        if (!maskCanvas) return null;
        // 建立純遮罩（白=重繪區，黑=保留區）
        const tmpCanvas = document.createElement('canvas');
        tmpCanvas.width = maskCanvas.width;
        tmpCanvas.height = maskCanvas.height;
        const tmpCtx = tmpCanvas.getContext('2d');
        tmpCtx.fillStyle = '#000';
        tmpCtx.fillRect(0, 0, tmpCanvas.width, tmpCanvas.height);

        // 從 maskCanvas 抽出白色區域
        const srcData = maskCtx.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
        const dstData = tmpCtx.getImageData(0, 0, tmpCanvas.width, tmpCanvas.height);

        // 原圖的每個畫素若明度 > 200，視為遮罩區域
        if (imageData.img1) {
            // 如果有底圖，需要 diff，簡化處理：把白色半透明畫素視為遮罩
            const img = new Image();
            img.src = imageData.img1.dataUrl;
            // 同步畫到臨時 canvas 比較
            const baseCtx = document.createElement('canvas').getContext('2d');
        }

        // 簡化：直接從 canvas 取出白色高亮部分
        for (let i = 0; i < srcData.data.length; i += 4) {
            const r = srcData.data[i], g = srcData.data[i+1], b = srcData.data[i+2];
            // 亮度高（被畫筆塗到）→ 白色
            const bright = (r + g + b) / 3;
            if (bright > 200) {
                dstData.data[i] = 255;
                dstData.data[i+1] = 255;
                dstData.data[i+2] = 255;
                dstData.data[i+3] = 255;
            }
        }

        tmpCtx.putImageData(dstData, 0, 0);
        return tmpCanvas.toDataURL('image/png').split(',')[1];
    }

    // ── 參數表單 ─────────────────────────────────────────────────
    function renderParams(feature) {
        const section = document.getElementById('paramsSection');
        if (!section) return;

        const builders = {
            professional: buildProfessionalParams,
            anime: buildAnimeParams,
            figure: buildFigureParams,
            sticker: buildStickerParams,
            passport: buildPassportParams,
            scene: buildSceneParams,
            inpaint: buildInpaintParams,
            outpaint: buildOutpaintParams,
            doodle: buildDoodleParams,
            logo: buildLogoParams,
            gif: buildGifParams,
            fusion: buildFusionParams,
        };

        const builder = builders[feature.id];
        section.innerHTML = builder ? builder() : '';
    }

    function row(label, content) {
        return `<div class="param-row"><div class="param-label">${label}</div>${content}</div>`;
    }

    function chips(id, options, defaultVal) {
        return `<div class="param-chip-group" id="${id}">
            ${options.map(o => `<button class="param-chip ${o.value === defaultVal ? 'selected' : ''}" data-value="${o.value}">${o.label}</button>`).join('')}
        </div>`;
    }

    function select(id, options, defaultVal) {
        return `<select id="${id}" class="param-select">
            ${options.map(o => `<option value="${o.value}" ${o.value === defaultVal ? 'selected' : ''}>${o.label}</option>`).join('')}
        </select>`;
    }

    function buildProfessionalParams() {
        return `
        <div class="param-grid">
            ${row('背景', select('p_background', [
                {value:'a clean, professional office background', label:'辦公室'},
                {value:'a light gray studio background', label:'灰色攝影棚'},
                {value:'a soft white background', label:'純白'},
                {value:'a modern cityscape background', label:'城市夜景'},
                {value:'a library or bookshelf background', label:'書房'},
            ], 'a clean, professional office background'))}
            ${row('服裝', select('p_attire', [
                {value:'a professional business suit', label:'西裝'},
                {value:'a business casual shirt and blazer', label:'商務休閒'},
                {value:'a formal dress shirt', label:'正式白襯衫'},
                {value:'a medical white coat', label:'白袍'},
                {value:'a creative casual outfit', label:'創意休閒'},
            ], 'a professional business suit'))}
        </div>
        ${row('表情', chips('p_expression', [
            {value:'a confident, professional smile', label:'自信微笑'},
            {value:'a natural, friendly smile', label:'自然友善'},
            {value:'a serious, focused expression', label:'認真專注'},
            {value:'a warm and approachable expression', label:'親切'},
        ], 'a confident, professional smile'))}
        <div class="param-row">
            <label class="param-checkbox-row">
                <input type="checkbox" id="p_preserve" style="accent-color:var(--at-accent,#6366f1)">
                保留原有臉部特徵（精確模式）
            </label>
        </div>`;
    }

    function buildAnimeParams() {
        const styles = [
            '現代動漫 (Modern Anime)', 'Ghibli 宮崎駿', '少年漫畫 (Shonen)',
            '少女漫畫 (Shojo)', '賽博龐克', '水彩插畫', '像素藝術',
        ];
        return `
        ${row('動漫風格', `<div class="param-chip-group" id="a_style">
            ${styles.map((s,i) => `<button class="param-chip ${i===0?'selected':''}" data-value="${s}">${s}</button>`).join('')}
        </div>`)}
        ${row('風格強度', `<div class="param-strength-row">
            <input type="range" id="a_strength" min="1" max="5" value="3"
                oninput="document.getElementById('a_strength_val').textContent=this.value">
            <span id="a_strength_val" class="param-strength-val">3</span>
        </div>`)}
        ${row('排除元素（選填）', `<input type="text" id="a_negative" class="param-input" placeholder="例如：glasses, hat">`)}`;
    }

    function buildFigureParams() {
        return `
        ${row('展示底座', select('f_base', [
            {value:'on a simple round display stand with gradient background', label:'圓形展示台'},
            {value:'on a themed diorama base', label:'主題場景台'},
            {value:'floating in a white studio space', label:'白色工作室'},
            {value:'on a wooden shelf display', label:'木質展示架'},
        ], 'on a simple round display stand with gradient background'))}
        ${row('模式', chips('f_mode', [
            {value:'single', label:'單人'},
            {value:'duo_new', label:'雙人（需上傳第二張）'},
        ], 'single'))}`;
    }

    function buildStickerParams() {
        return `
        ${row('貼紙風格', chips('s_style', [
            {value:'cute_chibi', label:'可愛 Q 版'},
            {value:'pixel_art', label:'像素藝術'},
            {value:'watercolor', label:'水彩插畫'},
            {value:'bold_line', label:'粗線條漫畫'},
            {value:'holographic', label:'全息閃亮'},
        ], 'cute_chibi'))}
        ${row('主題（選填）', `<input type="text" id="s_theme" class="param-input" placeholder="例如：聖誕節、生日、運動">`)}
        <div class="param-row">
            <label class="param-checkbox-row">
                <input type="checkbox" id="s_text" style="accent-color:var(--at-accent,#6366f1)">
                加入文字標籤
            </label>
        </div>`;
    }

    function buildPassportParams() {
        return row('照片類型', chips('pp_type', [
            {value:'id', label:'護照 / 身分證'},
            {value:'resume', label:'履歷用照'},
        ], 'id'));
    }

    function buildSceneParams() {
        const presets = [
            {value:'', label:'自訂…'},
            {value:'cherry blossom park in spring, soft sunlight', label:'🌸 春日公園'},
            {value:'modern minimalist office with floor-to-ceiling windows', label:'🏢 現代辦公室'},
            {value:'tropical beach at golden hour sunset', label:'🏖️ 黃昏海灘'},
            {value:'cozy coffee shop with warm lighting', label:'☕ 咖啡廳'},
            {value:'snowy mountain landscape with blue sky', label:'⛰️ 雪山'},
        ];
        return `
        ${row('場景預設', `<select id="sc_preset" class="param-select" onchange="applyScenePreset(this.value)">
            ${presets.map(p => `<option value="${p.value}">${p.label}</option>`).join('')}
        </select>`)}
        ${row('自訂場景描述', `<textarea id="sc_prompt" class="param-textarea" placeholder="描述你想要的背景場景…"></textarea>`)}
        <div class="param-row">
            <label class="param-checkbox-row">
                <input type="checkbox" id="sc_hair" style="accent-color:var(--at-accent,#6366f1)">
                保留原始髮型
            </label>
        </div>`;
    }

    function buildInpaintParams() {
        return row('重繪內容描述', `<textarea id="ip_prompt" class="param-textarea" placeholder="描述想在遮罩區域生成的內容…\n例如：a red rose, sunglasses, a tattoo"></textarea>`);
    }

    function buildOutpaintParams() {
        return `
        ${row('延伸比例', chips('op_ratio', [
            {value:'16:9', label:'16:9 橫式'},
            {value:'9:16', label:'9:16 直式'},
            {value:'4:3', label:'4:3'},
            {value:'1:1', label:'1:1 方形'},
        ], '16:9'))}
        ${row('延伸方向描述（選填）', `<textarea id="op_prompt" class="param-textarea" placeholder="描述延伸區域的內容，不填則自動延伸…" style="min-height:50px"></textarea>`)}`;
    }

    function buildDoodleParams() {
        return `
        ${row('目標風格', chips('dd_style', [
            {value:'photorealistic', label:'寫實照片'},
            {value:'oil painting', label:'油畫'},
            {value:'watercolor', label:'水彩'},
            {value:'anime illustration', label:'動漫插畫'},
            {value:'3D render', label:'3D 渲染'},
        ], 'photorealistic'))}
        ${row('補充描述（選填）', `<input type="text" id="dd_prompt" class="param-input" placeholder="例如：a cozy cafe interior, detailed lighting">`)}`;
    }

    function buildLogoParams() {
        return `
        <div class="param-grid">
            ${row('品牌名稱 *', `<input type="text" id="lg_brand" class="param-input" placeholder="例如：Nova Tech">`)}
            ${row('Logo 類型', select('lg_type', [
                {value:'modern minimalist', label:'現代簡約'},
                {value:'bold geometric', label:'幾何粗體'},
                {value:'elegant serif', label:'優雅襯線'},
                {value:'playful friendly', label:'活潑友善'},
                {value:'tech futuristic', label:'科技未來感'},
            ], 'modern minimalist'))}
        </div>
        ${row('品牌理念', `<input type="text" id="lg_concept" class="param-input" placeholder="例如：創新 · 環保 · 科技">`)}
        ${row('色彩偏好', chips('lg_color', [
            {value:'', label:'不指定'},
            {value:'blue and white', label:'藍白'},
            {value:'green and gold', label:'綠金'},
            {value:'black and red', label:'黑紅'},
            {value:'purple and silver', label:'紫銀'},
            {value:'orange and dark', label:'橙深'},
        ], ''))}
        ${row('特定元素（選填）', `<input type="text" id="lg_elements" class="param-input" placeholder="例如：leaf, circuit board, mountain">`)}`;
    }

    function buildGifParams() {
        return row('動畫描述', `<textarea id="gf_prompt" class="param-textarea"
            placeholder="描述動畫內容…\n例如：a person waving hello with a smile\n或：spinning logo animation with sparkle effects"></textarea>`);
    }

    function buildFusionParams() {
        const presets = [
            {value:'', label:'自訂…'},
            {value:'a scenic mountain trail at sunrise', label:'⛰️ 山間小徑'},
            {value:'a cozy home living room', label:'🏠 溫馨客廳'},
            {value:'a busy city street in Tokyo', label:'🗼 東京街道'},
            {value:'a beach at golden hour', label:'🌅 黃昏海灘'},
        ];
        return `
        ${row('場景預設', `<select id="fu_preset" class="param-select" onchange="applyFusionPreset(this.value)">
            ${presets.map(p => `<option value="${p.value}">${p.label}</option>`).join('')}
        </select>`)}
        ${row('自訂場景', `<textarea id="fu_prompt" class="param-textarea" placeholder="描述兩人合影的場景…"></textarea>`)}`;
    }

    // 場景預設 helper（暴露到 window）
    window.applyScenePreset = function(val) {
        const ta = document.getElementById('sc_prompt');
        if (ta && val) ta.value = val;
    };
    window.applyFusionPreset = function(val) {
        const ta = document.getElementById('fu_prompt');
        if (ta && val) ta.value = val;
    };

    // Chip 選擇邏輯（事件委託）
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('param-chip')) {
            const group = e.target.closest('.param-chip-group');
            if (group) {
                group.querySelectorAll('.param-chip').forEach(c => c.classList.remove('selected'));
                e.target.classList.add('selected');
            }
        }
    });

    // ── 收集參數 ─────────────────────────────────────────────────
    function collectParams() {
        const f = currentFeature?.id;
        const p = {};
        const g = (id) => document.getElementById(id);
        const chip = (gid) => g(gid)?.querySelector('.param-chip.selected')?.dataset.value || '';

        if (f === 'professional') {
            p.background = g('p_background')?.value;
            p.attire = g('p_attire')?.value;
            p.expression = chip('p_expression');
            p.preserve_features = g('p_preserve')?.checked || false;
        } else if (f === 'anime') {
            p.style = chip('a_style') || '現代動漫 (Modern Anime)';
            p.strength = parseInt(g('a_strength')?.value || '3');
            p.negative_prompt = g('a_negative')?.value || '';
        } else if (f === 'figure') {
            p.figure_base = g('f_base')?.value;
            p.team_mode = chip('f_mode') || 'single';
        } else if (f === 'sticker') {
            p.sticker_style = chip('s_style') || 'cute_chibi';
            p.theme = g('s_theme')?.value || '';
            p.add_text = g('s_text')?.checked || false;
        } else if (f === 'passport') {
            p.photo_type = chip('pp_type') || 'id';
        } else if (f === 'scene') {
            p.scene_prompt = g('sc_prompt')?.value || g('sc_preset')?.value || 'a beautiful outdoor scene';
            p.keep_hairstyle = g('sc_hair')?.checked || false;
        } else if (f === 'inpaint') {
            p.inpaint_prompt = g('ip_prompt')?.value || 'fill naturally';
        } else if (f === 'outpaint') {
            p.aspect_ratio = chip('op_ratio') || '16:9';
            p.outpaint_prompt = g('op_prompt')?.value || '';
        } else if (f === 'doodle') {
            p.doodle_style = chip('dd_style') || 'photorealistic';
            p.doodle_prompt = g('dd_prompt')?.value || '';
        } else if (f === 'logo') {
            p.brand = g('lg_brand')?.value || '';
            p.logo_type = g('lg_type')?.value || 'modern minimalist';
            p.concept = g('lg_concept')?.value || '';
            p.color = chip('lg_color') || '';
            p.elements = g('lg_elements')?.value || '';
        } else if (f === 'gif') {
            p.gif_prompt = g('gf_prompt')?.value || 'animation';
        } else if (f === 'fusion') {
            p.scene_prompt = g('fu_prompt')?.value || g('fu_preset')?.value || 'a beautiful outdoor scene';
        }

        return p;
    }

    // ── 生成 ─────────────────────────────────────────────────────
    async function generate() {
        if (!currentFeature) return;

        const btn = document.getElementById('generateBtn');
        const status = document.getElementById('generateStatus');

        btn.disabled = true;
        btn.classList.add('loading');
        btn.innerHTML = `<span style="animation:spin 1s linear infinite;display:inline-block">⟳</span> 生成中…`;
        if (status) status.textContent = '正在呼叫 AI，請稍候（雲端模型約 10-30 秒）…';

        // 隱藏舊結果
        const resultSection = document.getElementById('resultSection');
        if (resultSection) resultSection.style.display = 'none';

        try {
            const body = {
                feature: currentFeature.id,
                image: imageData.img1?.dataUrl || null,
                image2: imageData.img2?.dataUrl || null,
                mask: currentFeature.id === 'inpaint' && maskCanvas
                    ? 'data:image/png;base64,' + getMaskBase64()
                    : null,
                params: collectParams(),
            };

            const res = await fetch('/avatar/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            const data = await res.json();

            if (data.success) {
                showResult(data.image, data.filename);
                if (status) status.textContent = `✓ 完成！已儲存為 ${data.filename}`;
            } else {
                if (status) {
                    status.textContent = `✗ ${data.error || '生成失敗'}`;
                    status.style.color = 'var(--at-err,#ef4444)';
                }
            }
        } catch (e) {
            if (status) {
                status.textContent = `✗ 網路錯誤：${e.message}`;
                status.style.color = 'var(--at-err,#ef4444)';
            }
        } finally {
            btn.disabled = false;
            btn.classList.remove('loading');
            btn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> 開始生成`;
            updateGenerateBtn();
        }
    }

    function showResult(imageSrc, filename) {
        const section = document.getElementById('resultSection');
        const img = document.getElementById('resultImage');
        const dl = document.getElementById('downloadBtn');

        if (img) img.src = imageSrc;
        if (dl) { dl.href = imageSrc; dl.download = filename || 'avatar_result.png'; }
        if (section) section.style.display = 'flex';

        // 捲動到結果
        section?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function useResultAsInput() {
        const img = document.getElementById('resultImage');
        if (!img || !img.src) return;

        // 轉成 File 並設為 img1
        fetch(img.src)
            .then(r => r.blob())
            .then(blob => {
                const file = new File([blob], 'result.png', { type: 'image/png' });
                loadImage(file, 1);
            });
    }

    // 旋轉動畫
    const style = document.createElement('style');
    style.textContent = `@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`;
    document.head.appendChild(style);

})();
