from flask import Flask, send_from_directory, jsonify, request
import json
import os
import sys
import webbrowser
import threading
import traceback
from datetime import datetime

app = Flask(__name__)

# ============================================
# تعیین مسیر اصلی برنامه (در سرور ثابت است)
# ============================================

def get_base_path():
    """مسیر پوشه فعلی برنامه را برمی‌گرداند"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_data_folder():
    """یک پوشه به نام 'data' در کنار برنامه می‌سازد و مسیر آن را برمی‌گرداند"""
    base_path = get_base_path()
    data_folder = os.path.join(base_path, 'data')
    if not os.path.exists(data_folder):
        os.makedirs(data_folder, exist_ok=True)
        print(f"📁 پوشه داده ساخته شد: {data_folder}")
    return data_folder

def get_data_path():
    """مسیر فایل داده‌ها را در پوشه data برمی‌گرداند"""
    return os.path.join(get_data_folder(), 'data.json')

def get_settings_path():
    """مسیر فایل تنظیمات را در پوشه data برمی‌گرداند"""
    return os.path.join(get_data_folder(), 'settings.json')

# ============================================
# توابع مدیریت داده (همانند قبل اما با مسیر جدید)
# ============================================

def load_data():
    try:
        data_path = get_data_path()
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"📂 داده‌ها بارگذاری شدند: {len(data)} آیتم")
                    return data
        return []
    except Exception as e:
        print(f"❌ خطا در بارگذاری: {e}")
        return []

def save_data(data):
    try:
        data_path = get_data_path()
        if not isinstance(data, list):
            data = []
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ داده‌ها ذخیره شدند: {len(data)} آیتم")
        return True
    except Exception as e:
        print(f"❌ خطا در ذخیره: {e}")
        return False

def load_settings():
    try:
        settings_path = get_settings_path()
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_settings(settings):
    try:
        settings_path = get_settings_path()
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def get_next_id(data):
    if not data:
        return 1
    max_id = 0
    for item in data:
        if isinstance(item, dict) and 'id' in item:
            try:
                if item['id'] > max_id:
                    max_id = item['id']
            except:
                pass
    return max_id + 1

def create_sample_data():
    return [
        {"id": 1, "area": "پژوهش", "description": "تهیه گزارش عملکرد ماهانه", "date": "۱ فروردین ۱۴۰۴", "images": [], "time": "۱۰:۳۰"},
        {"id": 2, "area": "مدیریت", "description": "بررسی گزارش‌های سالانه", "date": "۱۵ فروردین ۱۴۰۴", "images": [], "time": "۱۴:۲۰"}
    ]

def initialize_data():
    data_path = get_data_path()
    if not os.path.exists(data_path):
        print("⚠️ ایجاد داده‌های نمونه...")
        save_data(create_sample_data())
        return create_sample_data()
    return load_data()

# ============================================
# مسیرهای اصلی
# ============================================

@app.route('/')
def index():
    try:
        return send_from_directory(get_base_path(), 'index.html')
    except Exception as e:
        return f"خطا: {e}", 500

@app.route('/favicon.ico')
def favicon():
    try:
        return send_from_directory(get_base_path(), 'favicon.ico')
    except:
        return '', 204

# ============================================
# API - مسیرها (همگی بدون تغییر باقی ماندند)
# ============================================

@app.route('/api/data', methods=['GET'])
def get_api_data():
    try:
        data = load_data()
        settings = load_settings()
        areas = settings.get('areas', ['پژوهش', 'مدیریت', 'برنامه‌ریزی', 'آموزش', 'فرهنگی'])
        return jsonify({'activities': data, 'areas': areas, 'orgName': settings.get('org_name', 'مرکز علمی کاربردی خانه کارگر شیراز')})
    except Exception as e:
        print(f"❌ خطا در /api/data: {e}")
        return jsonify({'activities': [], 'areas': [], 'orgName': ''})

@app.route('/api/areas', methods=['GET'])
def get_areas():
    settings = load_settings()
    return jsonify(settings.get('areas', ['پژوهش', 'مدیریت', 'برنامه‌ریزی', 'آموزش', 'فرهنگی']))

@app.route('/api/areas', methods=['POST'])
def add_area():
    try:
        name = request.json.get('name')
        if not name:
            return jsonify({'success': False, 'error': 'نام حوزه خالی است'}), 400
        settings = load_settings()
        areas = settings.get('areas', ['پژوهش', 'مدیریت', 'برنامه‌ریزی', 'آموزش', 'فرهنگی'])
        if name not in areas:
            areas.append(name)
            settings['areas'] = areas
            save_settings(settings)
            return jsonify({'success': True, 'areas': areas})
        return jsonify({'success': False, 'error': 'حوزه تکراری است'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/areas/<path:name>', methods=['DELETE'])
def delete_area(name):
    try:
        settings = load_settings()
        areas = settings.get('areas', ['پژوهش', 'مدیریت', 'برنامه‌ریزی', 'آموزش', 'فرهنگی'])
        data = load_data()
        if any(a.get('area') == name for a in data):
            return jsonify({'success': False, 'error': 'این حوزه در فعالیت‌ها استفاده شده است'}), 400
        if name in areas:
            areas.remove(name)
            settings['areas'] = areas
            save_settings(settings)
            return jsonify({'success': True, 'areas': areas})
        return jsonify({'success': False, 'error': 'حوزه پیدا نشد'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/activities', methods=['POST'])
def create_activity():
    try:
        data = request.json
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'داده نامعتبر'}), 400
        
        activities = load_data()
        new_id = get_next_id(activities)
        data['id'] = new_id
        data.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
        data.setdefault('status', 'در حال انجام')
        data.setdefault('category', data.get('area', 'عمومی'))
        data.setdefault('area', 'عمومی')
        data.setdefault('images', [])
        data.setdefault('time', datetime.now().strftime('%H:%M'))
        data.setdefault('description', data.get('title', ''))
        
        activities.append(data)
        if save_data(activities):
            return jsonify({'status': 'success', 'id': new_id, 'data': data, 'total': len(activities)})
        return jsonify({'error': 'خطا در ذخیره'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activities/<int:activity_id>', methods=['PUT'])
def update_activity(activity_id):
    try:
        data = request.json
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'داده نامعتبر'}), 400
        
        activities = load_data()
        for i, item in enumerate(activities):
            if item.get('id') == activity_id:
                data['id'] = activity_id
                activities[i] = data
                if save_data(activities):
                    return jsonify({'status': 'success', 'data': data})
                return jsonify({'error': 'خطا در ذخیره'}), 500
        return jsonify({'error': 'فعالیت پیدا نشد'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activities/<int:activity_id>', methods=['DELETE'])
def delete_activity(activity_id):
    try:
        activities = load_data()
        for i, item in enumerate(activities):
            if item.get('id') == activity_id:
                del activities[i]
                if save_data(activities):
                    return jsonify({'status': 'success', 'message': 'حذف شد'})
                return jsonify({'error': 'خطا در ذخیره'}), 500
        return jsonify({'error': 'فعالیت پیدا نشد'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orgname', methods=['POST'])
def save_orgname():
    try:
        org_name = request.json.get('name', '')
        settings = load_settings()
        settings['org_name'] = org_name
        if save_settings(settings):
            return jsonify({'status': 'success', 'message': 'ذخیره شد'})
        return jsonify({'status': 'error', 'message': 'خطا در ذخیره'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_data():
    try:
        if save_data([]):
            return jsonify({'success': True, 'message': 'همه داده‌ها پاک شدند'})
        return jsonify({'success': False, 'error': 'خطا در پاک کردن'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# اجرای برنامه روی سرور
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 سامانه گزارش عملکرد (نسخه سرور)")
    print("=" * 50)
    initialize_data()
    print(f"📁 داده‌ها در پوشه: {get_data_folder()}")
    print("=" * 50)
    print("🌐 سرور در حال اجرا...")
    print("📍 آدرس: http://0.0.0.0:8080")
    print("⚠️ برای متوقف کردن: Ctrl+C")
    print("=" * 50)
    
    # نکته مهم: debug=False برای محیط سرور الزامی است
    app.run(host='0.0.0.0', port=8080, debug=False)
