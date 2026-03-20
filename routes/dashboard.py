"""
Dashboard Routes - 使用量儀表板與統計路由
"""
from flask import Blueprint, request, jsonify, render_template
from services.analytics_service import get_analytics_service

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def dashboard_page():
    """儀表板頁面"""
    return render_template('dashboard.html')


@dashboard_bp.route('/api/analytics/overview', methods=['GET'])
def analytics_overview():
    """統計總覽"""
    analytics = get_analytics_service()
    return jsonify({'success': True, 'data': analytics.get_overview()})


@dashboard_bp.route('/api/analytics/daily', methods=['GET'])
def analytics_daily():
    """每日統計圖表資料"""
    days = request.args.get('days', 30, type=int)
    analytics = get_analytics_service()
    return jsonify({'success': True, 'data': analytics.get_daily_chart(days)})


@dashboard_bp.route('/api/analytics/models', methods=['GET'])
def analytics_models():
    """模型使用量統計"""
    analytics = get_analytics_service()
    return jsonify({'success': True, 'data': analytics.get_model_usage()})


@dashboard_bp.route('/api/analytics/resolutions', methods=['GET'])
def analytics_resolutions():
    """解析度使用統計"""
    analytics = get_analytics_service()
    return jsonify({'success': True, 'data': analytics.get_popular_resolutions()})


@dashboard_bp.route('/api/analytics/modes', methods=['GET'])
def analytics_modes():
    """生成模式分佈"""
    analytics = get_analytics_service()
    return jsonify({'success': True, 'data': analytics.get_mode_distribution()})


@dashboard_bp.route('/api/analytics/speed', methods=['GET'])
def analytics_speed():
    """生成速度統計"""
    analytics = get_analytics_service()
    return jsonify({'success': True, 'data': analytics.get_generation_speed()})


@dashboard_bp.route('/api/analytics/activity', methods=['GET'])
def analytics_activity():
    """最近活動"""
    limit = request.args.get('limit', 20, type=int)
    analytics = get_analytics_service()
    return jsonify({'success': True, 'data': analytics.get_recent_activity(limit)})
