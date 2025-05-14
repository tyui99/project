# data.py
import json
import os
import datetime

# 文件路径配置
DATA_DIR = os.path.join(os.path.dirname(__file__), 'app_data')
CONFERENCE_DATA_FILE = os.path.join(DATA_DIR, 'conferences.json')
USER_PREFERENCES_FILE = os.path.join(DATA_DIR, 'user_preferences.json')
SENT_REMINDERS_FILE = os.path.join(DATA_DIR, 'sent_reminders.json')

# 确保数据目录存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 全局数据结构
conference_data_list = []  # 存储会议信息的列表
user_preferences = {}      # 存储用户偏好的字典，键为email
sent_reminders = {}        # 存储已发送提醒的记录，键为 (email, conf_acronym, deadline_type, deadline_date_str)

# --- 数据持久化辅助函数 ---
def _datetime_converter(o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    if isinstance(o, datetime.date):
        return o.isoformat()

def _datetime_parser(dct):
    for k, v in dct.items():
        if isinstance(v, str):
            try:
                # 尝试解析为 datetime (包含时区信息)
                dt_obj = datetime.datetime.fromisoformat(v)
                dct[k] = dt_obj
            except ValueError:
                try:
                    # 尝试解析为 date
                    date_obj = datetime.date.fromisoformat(v)
                    dct[k] = date_obj
                except ValueError:
                    pass #保持原样
    return dct

# --- 会议数据 --- 
def load_conference_data():
    """从JSON文件加载会议数据到全局列表。"""
    global conference_data_list
    try:
        if os.path.exists(CONFERENCE_DATA_FILE):
            with open(CONFERENCE_DATA_FILE, 'r', encoding='utf-8') as f:
                data_from_file = json.load(f, object_hook=_datetime_parser)
                for conf in data_from_file:
                    if 'parsed_deadlines' in conf and isinstance(conf['parsed_deadlines'], dict):
                        for key, val in conf['parsed_deadlines'].items():
                            if isinstance(val, str):
                                try:
                                    conf['parsed_deadlines'][key] = datetime.datetime.fromisoformat(val)
                                except ValueError:
                                    print(f"警告: 无法将 {val} 转换为 {key} 的datetime对象")
                                    conf['parsed_deadlines'][key] = None
                    if 'extracted_deadlines' not in conf:
                        conf['extracted_deadlines'] = {}
                conference_data_list = data_from_file
            print(f"会议数据已从 {CONFERENCE_DATA_FILE} 加载。共有 {len(conference_data_list)} 条记录。")
        else:
            conference_data_list = []
            print(f"会议数据文件 {CONFERENCE_DATA_FILE} 未找到，初始化为空列表。")
    except Exception as e:
        print(f"加载会议数据失败: {e}")
        conference_data_list = []

def save_conference_data(data_to_save=None):
    """将全局会议数据列表保存到JSON文件。"""
    global conference_data_list
    data = data_to_save if data_to_save is not None else conference_data_list
    try:
        with open(CONFERENCE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4, default=_datetime_converter)
        print(f"会议数据已保存到 {CONFERENCE_DATA_FILE}。")
    except Exception as e:
        print(f"保存会议数据失败: {e}")

# --- 用户偏好 --- 
def load_user_preferences():
    """从JSON文件加载用户偏好数据到全局字典。"""
    global user_preferences
    try:
        if os.path.exists(USER_PREFERENCES_FILE):
            with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                user_preferences = json.load(f)
            print(f"用户偏好数据已从 {USER_PREFERENCES_FILE} 加载。")
        else:
            user_preferences = {}
            print(f"用户偏好文件 {USER_PREFERENCES_FILE} 未找到，初始化为空字典。")
    except Exception as e:
        print(f"加载用户偏好数据失败: {e}")
        user_preferences = {}

def save_user_preferences(data_to_save=None):
    """将全局用户偏好字典保存到JSON文件。"""
    global user_preferences
    data = data_to_save if data_to_save is not None else user_preferences
    try:
        with open(USER_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"用户偏好数据已保存到 {USER_PREFERENCES_FILE}。")
    except Exception as e:
        print(f"保存用户偏好数据失败: {e}")

# --- 已发送提醒 --- 
def load_sent_reminders():
    """从JSON文件加载已发送提醒记录。"""
    global sent_reminders
    try:
        if os.path.exists(SENT_REMINDERS_FILE):
            with open(SENT_REMINDERS_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f, object_hook=_datetime_parser)
                sent_reminders_temp = {}
                for k_str, v_dt in loaded_data.items():
                    try:
                        key_tuple = eval(k_str) 
                        if isinstance(key_tuple, tuple) and len(key_tuple) == 4:
                            sent_reminders_temp[key_tuple] = v_dt
                        else:
                            print(f"警告: 无法将键 '{k_str}' 转换回元组。")
                    except Exception as eval_e:
                        print(f"警告: 解析已发送提醒的键 '{k_str}' 失败: {eval_e}")
                sent_reminders = sent_reminders_temp
            print(f"已发送提醒记录已从 {SENT_REMINDERS_FILE} 加载。")
        else:
            sent_reminders = {}
            print(f"已发送提醒记录文件 {SENT_REMINDERS_FILE} 未找到，初始化为空字典。")
    except Exception as e:
        print(f"加载已发送提醒记录失败: {e}")
        sent_reminders = {}

def save_sent_reminders(data_to_save=None):
    """将已发送提醒记录保存到JSON文件。"""
    global sent_reminders
    data = data_to_save if data_to_save is not None else sent_reminders
    try:
        data_to_serialize = {str(k): v for k, v in data.items()}
        with open(SENT_REMINDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_serialize, f, ensure_ascii=False, indent=4, default=_datetime_converter)
        print(f"已发送提醒记录已保存到 {SENT_REMINDERS_FILE}。")
    except Exception as e:
        print(f"保存已发送提醒记录失败: {e}")

# 初始化加载数据
load_conference_data()
load_user_preferences()
load_sent_reminders()

if __name__ == '__main__':
    print("--- data.py 测试 --- ")
    sample_conf_data = [
        {
            'acronym': 'TESTCONF1',
            'full_name': 'Test Conference 1',
            'rank': 'A',
            'url': 'http://example.com/testconf1',
            'deadlines_raw': 'Submission: 2025-01-01 AoE',
            'extracted_deadlines': {'submission_deadline': {'date_str': '2025-01-01', 'tz_str': 'AoE'}},
            'parsed_deadlines': {'submission_deadline': datetime.datetime(2025, 1, 2, 11, 59, 59, tzinfo=datetime.timezone.utc)}
        }
    ]
    save_conference_data(sample_conf_data)
    load_conference_data()
    print("加载后的会议数据:", conference_data_list)
    if conference_data_list and isinstance(conference_data_list[0]['parsed_deadlines']['submission_deadline'], datetime.datetime):
        print("会议数据 datetime 对象加载成功。")
    else:
        print("会议数据 datetime 对象加载失败。")

    sample_user_prefs = {
        'user@example.com': {
            'user_email': 'user@example.com',
            'subscribed_conferences': ['TESTCONF1'],
            'reminder_days_before': {'submission_deadline': 5},
            'custom_reminder_days': True
        }
    }
    save_user_preferences(sample_user_prefs)
    load_user_preferences()
    print("加载后的用户偏好:", user_preferences)

    sample_sent_reminders = {
        ('user@example.com', 'TESTCONF1', 'submission_deadline', '2025-01-02'): datetime.datetime.now()
    }
    save_sent_reminders(sample_sent_reminders)
    load_sent_reminders()
    print("加载后的已发送提醒:", sent_reminders)
    if sent_reminders and any(isinstance(v, datetime.datetime) for v in sent_reminders.values()):
         print("已发送提醒 datetime 对象加载成功。")
    else:
        print("已发送提醒 datetime 对象加载失败或为空。")
    print("--- data.py 测试结束 --- ")