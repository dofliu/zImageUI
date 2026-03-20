"""
Project Service - 工作區/專案管理服務
將生成的圖片組織到不同的專案中，支援專案級別的配置和匯出
"""
import os
import json
import uuid
from datetime import datetime
import config


PROJECTS_FILE = os.path.join(config.OUTPUT_PATH, "projects.json")


class ProjectService:
    """專案管理服務"""

    def __init__(self):
        self.projects = self._load()

    def _load(self):
        """載入專案列表"""
        if os.path.exists(PROJECTS_FILE):
            try:
                with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        """儲存專案"""
        try:
            os.makedirs(os.path.dirname(PROJECTS_FILE), exist_ok=True)
            with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.projects, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存專案失敗: {e}")

    def _find(self, project_id):
        """尋找專案"""
        for p in self.projects:
            if p['id'] == project_id:
                return p
        return None

    def create(self, name, description='', default_model=None, default_style=None,
               default_size=None, default_negative_prompt=''):
        """建立新專案"""
        project = {
            'id': str(uuid.uuid4())[:8],
            'name': name.strip(),
            'description': description.strip(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'images': [],
            'image_count': 0,
            'settings': {
                'default_model': default_model,
                'default_style': default_style,
                'default_size': default_size,
                'default_negative_prompt': default_negative_prompt
            },
            'tags': [],
            'status': 'active',  # active, archived, completed
            'notes': ''
        }

        self.projects.insert(0, project)
        self._save()
        return project

    def list_all(self, status=None):
        """列出所有專案"""
        if status:
            return [p for p in self.projects if p.get('status') == status]
        return self.projects

    def get(self, project_id):
        """取得特定專案"""
        return self._find(project_id)

    def update(self, project_id, **kwargs):
        """更新專案資訊"""
        project = self._find(project_id)
        if not project:
            return None

        allowed_fields = ['name', 'description', 'tags', 'status', 'notes', 'settings']
        for key, value in kwargs.items():
            if key in allowed_fields:
                project[key] = value

        project['updated_at'] = datetime.now().isoformat()
        self._save()
        return project

    def delete(self, project_id):
        """刪除專案（不刪除圖片檔案）"""
        self.projects = [p for p in self.projects if p['id'] != project_id]
        self._save()
        return True

    def add_image(self, project_id, filename, prompt, seed=None, model_id=None, metadata=None):
        """將圖片加入專案"""
        project = self._find(project_id)
        if not project:
            return None

        image_entry = {
            'filename': filename,
            'image_url': f'/images/{filename}',
            'prompt': prompt,
            'seed': seed,
            'model': model_id,
            'added_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'rating': None,  # 1-5 星評分
            'notes': ''
        }

        project['images'].append(image_entry)
        project['image_count'] = len(project['images'])
        project['updated_at'] = datetime.now().isoformat()
        self._save()
        return image_entry

    def remove_image(self, project_id, filename):
        """從專案中移除圖片"""
        project = self._find(project_id)
        if not project:
            return False

        project['images'] = [img for img in project['images'] if img['filename'] != filename]
        project['image_count'] = len(project['images'])
        project['updated_at'] = datetime.now().isoformat()
        self._save()
        return True

    def rate_image(self, project_id, filename, rating):
        """為專案中的圖片評分 (1-5)"""
        project = self._find(project_id)
        if not project:
            return False

        rating = max(1, min(5, int(rating)))
        for img in project['images']:
            if img['filename'] == filename:
                img['rating'] = rating
                project['updated_at'] = datetime.now().isoformat()
                self._save()
                return True
        return False

    def get_project_stats(self, project_id):
        """取得專案統計"""
        project = self._find(project_id)
        if not project:
            return None

        images = project.get('images', [])
        rated = [img for img in images if img.get('rating') is not None]
        models_used = set(img.get('model') for img in images if img.get('model'))

        return {
            'total_images': len(images),
            'rated_images': len(rated),
            'avg_rating': round(sum(img['rating'] for img in rated) / len(rated), 1) if rated else None,
            'models_used': list(models_used),
            'created_at': project['created_at'],
            'updated_at': project['updated_at'],
            'status': project['status']
        }

    def duplicate(self, project_id):
        """複製專案（不含圖片）"""
        original = self._find(project_id)
        if not original:
            return None

        new_project = {
            'id': str(uuid.uuid4())[:8],
            'name': f"{original['name']} (副本)",
            'description': original.get('description', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'images': [],
            'image_count': 0,
            'settings': dict(original.get('settings', {})),
            'tags': list(original.get('tags', [])),
            'status': 'active',
            'notes': ''
        }

        self.projects.insert(0, new_project)
        self._save()
        return new_project


# 全域單例
_project_service = None


def get_project_service():
    """取得專案服務單例"""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
    return _project_service
