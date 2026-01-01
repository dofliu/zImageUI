"""
Prompt Routes - 提示詞助手相關路由
"""
import os
import json
import re
from flask import Blueprint, request, jsonify


prompt_bp = Blueprint('prompt', __name__)

# 關鍵字檔案路徑
KEYWORDS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompt_keywords.json")


@prompt_bp.route('/prompt/suggestions', methods=['POST'])
def get_prompt_suggestions():
    """獲取提示詞建議"""
    try:
        data = request.get_json()
        input_text = data.get('input', '').lower().strip()

        if len(input_text) < 2:
            return jsonify({'suggestions': []})

        # 載入關鍵字資料庫
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            keywords = json.load(f)

        # 搜尋所有類別的關鍵字
        suggestions = []
        categories = ['subjects', 'styles', 'quality', 'lighting', 'camera', 'mood', 'composition']

        for category in categories:
            if category in keywords:
                for keyword in keywords[category]:
                    if input_text in keyword.lower():
                        suggestions.append({
                            'text': keyword,
                            'category': category,
                            'display': f"{keyword} ({category})"
                        })

        # 限制返回數量
        suggestions = suggestions[:15]

        return jsonify({'suggestions': suggestions})

    except Exception as e:
        print(f"獲取建議錯誤：{str(e)}")
        return jsonify({'suggestions': []}), 500


@prompt_bp.route('/prompt/enhance', methods=['POST'])
def enhance_prompt():
    """增強提示詞"""
    try:
        data = request.get_json()
        original_prompt = data.get('prompt', '').strip()

        if not original_prompt:
            return jsonify({'error': '提示詞不能為空'}), 400

        # 載入關鍵字資料庫
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            keywords = json.load(f)

        # 分析提示詞並增強
        enhanced = original_prompt
        added_keywords = []

        # 根據規則添加關鍵字
        if 'enhancement_rules' in keywords:
            for rule in keywords['enhancement_rules']:
                pattern = rule['pattern']
                if re.search(pattern, original_prompt, re.IGNORECASE):
                    # 添加建議的關鍵字
                    for keyword in rule.get('add', []):
                        if keyword.lower() not in enhanced.lower():
                            added_keywords.append(keyword)

        # 檢查是否缺少品質關鍵字
        quality_keywords = keywords.get('quality', [])
        has_quality = any(q.lower() in original_prompt.lower() for q in quality_keywords[:5])
        if not has_quality:
            added_keywords.insert(0, 'high quality')

        # 組合增強後的提示詞
        if added_keywords:
            enhanced = f"{original_prompt}, {', '.join(added_keywords)}"

        return jsonify({
            'original': original_prompt,
            'enhanced': enhanced,
            'added_keywords': added_keywords,
            'improvements': len(added_keywords)
        })

    except Exception as e:
        print(f"增強提示詞錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/prompt/templates', methods=['GET'])
def get_prompt_templates():
    """獲取提示詞範本列表"""
    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            keywords = json.load(f)

        templates = keywords.get('templates', [])

        # 按分類組織
        categories = {}
        for template in templates:
            category = template.get('category', '其他')
            if category not in categories:
                categories[category] = []
            categories[category].append(template)

        return jsonify({
            'templates': templates,
            'categories': categories,
            'total': len(templates)
        })

    except Exception as e:
        print(f"獲取範本錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/prompt/apply-template', methods=['POST'])
def apply_prompt_template():
    """應用提示詞範本"""
    try:
        data = request.get_json()
        template_id = data.get('template_id')
        subject = data.get('subject', '').strip()

        if not template_id:
            return jsonify({'error': '請選擇範本'}), 400

        # 載入範本
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            keywords = json.load(f)

        # 尋找範本
        template = None
        for t in keywords.get('templates', []):
            if t.get('id') == template_id:
                template = t
                break

        if not template:
            return jsonify({'error': '範本不存在'}), 404

        # 應用範本
        prompt_template = template.get('prompt', '')
        placeholder = template.get('placeholder', 'subject')

        # 如果用戶沒有輸入主題，使用範本的預設值
        if not subject:
            subject = placeholder

        # 替換佔位符
        generated_prompt = prompt_template.replace('{subject}', subject)

        return jsonify({
            'template_name': template.get('name'),
            'template_category': template.get('category'),
            'generated_prompt': generated_prompt,
            'subject': subject
        })

    except Exception as e:
        print(f"應用範本錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500
