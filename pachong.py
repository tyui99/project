import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, timedelta
import pytz
import dateparser

# 定义常量
CONF_CS_URL = "https://www.conferences-computer.science/"

def convert_to_beijing_time(date_str, tz_str=None):
    """将给定的日期时间字符串转换为北京时间"""
    try:
        settings = {'RETURN_AS_TIMEZONE_AWARE': True}
        if tz_str:
            tz_map = {
                'AoE': 'UTC-12',
                'PST': 'America/Los_Angeles',
                'PDT': 'America/Los_Angeles',
                'EST': 'America/New_York',
                'EDT': 'America/New_York',
                'CST': 'America/Chicago',
                'CDT': 'America/Chicago',
                'MST': 'America/Denver',
                'MDT': 'America/Denver',
                'JST': 'Asia/Tokyo',
                'GMT': 'GMT',
                'UTC': 'UTC',
                'CEST': 'Europe/Paris',
                'CET': 'Europe/Paris'
            }
            settings['TIMEZONE'] = tz_map.get(tz_str.upper(), tz_str)

        parsed_date = dateparser.parse(date_str, settings=settings)
        if parsed_date:
            beijing_tz = pytz.timezone('Asia/Shanghai')
            return parsed_date.astimezone(beijing_tz)
        return None

    except Exception as e:
        print(f"时间转换错误: {e}")
        return None

def preprocess_date_string(date_str):
    """预处理日期字符串，处理连接在一起的多个日期"""
    if not date_str or date_str == "N/A":
        return date_str

    # 如果日期字符串包含多个日期（通过检测多个年份或月份名称来判断）
    months = ["January", "February", "March", "April", "May", "June", "July", 
              "August", "September", "October", "November", "December"]
    
    # 按年份分割
    parts = re.split(r'(\d{4})', date_str)
    if len(parts) > 2:  # 有多个年份
        # 重组第一个日期（包括年份）
        first_date = parts[0] + parts[1]
        return first_date.strip()
    
    # 按月份分割
    for month in months:
        if date_str.count(month) > 1:
            # 取第一个月份之前的部分加上月份和年份
            month_parts = date_str.split(month)
            return (month_parts[0] + month + 
                    re.search(r'\d{4}', date_str).group(0)).strip()
    
    # 按星期几分割（如果有多个）
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day in weekdays:
        if date_str.count(day) > 1:
            # 取第一个星期几之后的部分直到下一个星期几或结尾
            day_parts = date_str.split(day)[1:]
            first_date = day + day_parts[0]
            # 确保包含年份
            year_match = re.search(r'\d{4}', date_str)
            if year_match and year_match.group(0) not in first_date:
                first_date += " " + year_match.group(0)
            return first_date.strip()
    
    return date_str.strip()

def extract_deadline_details_from_text(text):
    """从包含日期、时间和时区的文本中提取详细信息。

    Args:
        text (str): 包含日期信息的原始字符串。

    Returns:
        dict: 包含 'date_str' (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS) 和 'tz_str' (时区字符串) 的字典。
              如果无法解析，则 date_str 为 None。
    """
    if not text or text.lower() == 'tbd' or text.lower() == 'n/a':
        return {'date_str': None, 'tz_str': None}

    print(f"正在解析日期文本: '{text}'")

    # 1. 提取时区 (TZ)
    tz_str = None
    tz_pattern = r'\b(UTC[+-]\d{1,2}(?::\d{2})?|GMT[+-]\d{1,2}(?::\d{2})?|[A-Z]{3,5}(?![a-zA-Z])|[ECMP][SD]T)\b'
    tz_match = re.search(tz_pattern, text, re.IGNORECASE)
    if tz_match:
        potential_tz = tz_match.group(0).upper()
        common_months_days = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
                              "MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        if potential_tz not in common_months_days:
            tz_str = potential_tz
            print(f"  提取到时区: {tz_str}")
            # 从原始文本中移除时区，以便后续处理不包含它
            text = re.sub(tz_pattern, '', text, flags=re.IGNORECASE, count=1).strip()
        else:
            print(f"  候选时区 '{potential_tz}' 可能是月份或星期，已忽略。")

    # 改进的多日期解析策略
    # 1. 首先尝试提取所有可能的日期模式
    date_patterns = [
        r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
        r'((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{4})',
        r'(\d{4}-\d{1,2}-\d{1,2})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})'
    ]
    
    potential_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        potential_dates.extend(matches)
    
    # 如果没有找到明确的日期模式，尝试分割处理
    if not potential_dates:
        # 尝试按星期名称分割
        weekday_pattern = r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.?\s*'
        segments = re.split(weekday_pattern, text, flags=re.IGNORECASE)
        
        # 过滤掉空字符串和星期名称
        date_segments = [seg.strip() for seg in segments if seg and seg.strip() and not re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.?$', seg.strip(), re.IGNORECASE)]
        
        if not date_segments:
            date_segments = [text]  # 如果没有找到分段，使用原始文本
        
        potential_dates = date_segments

    parsed_date_obj = None
    final_date_str_from_loop = None

    # 尝试解析每个潜在的日期（优先解析最后一个，通常是最重要的）
    for current_text_to_parse in reversed(potential_dates):
        print(f"  尝试解析片段: '{current_text_to_parse}'")
        # 2. 预处理当前日期字符串片段
        date_line_to_parse = current_text_to_parse
        date_line_to_parse = re.sub(r'^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.?\s*', '', date_line_to_parse, flags=re.IGNORECASE).strip()
        date_line_to_parse = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_line_to_parse, flags=re.IGNORECASE)
        date_line_to_parse = re.sub(r'[\s,.]+$', '', date_line_to_parse)
        date_line_to_parse = re.sub(r'\s+(at|on)\s+', ' ', date_line_to_parse, flags=re.IGNORECASE).strip()
        def normalize_month(match):
            return match.group(0).capitalize()
        date_line_to_parse = re.sub(r'\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b', normalize_month, date_line_to_parse, flags=re.IGNORECASE)
        date_line_to_parse = re.sub(r'\s+', ' ', date_line_to_parse).strip()
        # 移除可能残留的其他日期片段
        date_line_to_parse = re.sub(r'[A-Za-z]{3,}\s*\d{1,2}\s*[A-Za-z]{3,}\s*\d{4}.*$', '', date_line_to_parse).strip()

        print(f"    预处理后的日期文本 (for strptime): '{date_line_to_parse}'")
        if not date_line_to_parse: # 如果预处理后为空，则跳过
            print("    预处理后文本为空，跳过此片段。")
            continue

        # 3. 尝试使用 strptime 解析
        date_formats_to_try = [
            "%d %B %Y %H:%M:%S", "%d %b %Y %H:%M:%S", "%B %d, %Y %H:%M:%S", "%b %d, %Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S",
            "%d %B %Y %H:%M", "%d %b %Y %H:%M", "%B %d, %Y %H:%M", "%b %d, %Y %H:%M",
            "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M", "%m/%d/%Y %H:%M", "%d/%m/%Y %H:%M",
            "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%Y %B %d", "%Y %b %d",
            "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%B %d %Y", "%b. %d, %Y",
            "%d %B, %Y", "%Y, %B %d", "%Y, %b %d"
        ]

        parsed_time_str = None
        time_pattern_detailed = r'(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)'
        time_match = re.search(time_pattern_detailed, date_line_to_parse)
        if time_match:
            parsed_time_str = time_match.group(1)

        temp_parsed_date_obj = None
        for fmt in date_formats_to_try:
            try:
                cleaned_for_fmt = re.sub(r'\s+', ' ', date_line_to_parse).strip()
                if "%b." not in fmt and "%b" in fmt:
                    cleaned_for_fmt = cleaned_for_fmt.replace('.', '')
                
                temp_parsed_date_obj = datetime.strptime(cleaned_for_fmt, fmt)
                print(f"    成功使用 strptime 格式 '{fmt}' 解析: {temp_parsed_date_obj}, 清理后原始: '{cleaned_for_fmt}'")
                parsed_date_obj = temp_parsed_date_obj # 保存成功的解析对象
                break 
            except ValueError:
                continue
        
        if parsed_date_obj: # 如果当前片段解析成功，就用这个结果
            final_date_str_from_loop = parsed_date_obj.strftime('%Y-%m-%d')
            if parsed_time_str and not (parsed_date_obj.hour or parsed_date_obj.minute or parsed_date_obj.second):
                final_date_str_from_loop = f"{final_date_str_from_loop} {parsed_time_str}"
            elif parsed_date_obj.hour or parsed_date_obj.minute or parsed_date_obj.second:
                final_date_str_from_loop = parsed_date_obj.strftime('%Y-%m-%d %H:%M:%S')
            print(f"  成功解析片段，使用日期: {final_date_str_from_loop}")
            break # 跳出外层循环，因为我们已经找到了一个可解析的日期

    if final_date_str_from_loop:
        result = {'date_str': final_date_str_from_loop, 'tz_str': tz_str}
        print(f"  最终结果 (strptime): {result}")
        return result
    else:
        print(f"  未能使用所有 strptime 格式解析任何日期片段 (原始文本: '{text}')")
        return {'date_str': None, 'tz_str': None}

def fetch_conferences(category_name=None, start_date=None, end_date=None):
    """从 conferences-computer.science 爬取会议信息

    Args:
        category_name (str, optional): 会议类别 (当前未使用，因为网站不按类别细分).
        start_date (str, optional): YYYY-MM-DD格式的开始日期，用于筛选会议.
        end_date (str, optional): YYYY-MM-DD格式的结束日期，用于筛选会议.
    """
    try:
        print(f"正在从 {CONF_CS_URL} 获取会议信息...")
        if start_date and end_date:
            print(f"  筛选日期范围: {start_date} 到 {end_date}")
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                print("错误: 日期范围格式无效，将不进行日期筛选。")
                start_date_obj = None
                end_date_obj = None
        else:
            start_date_obj = None
            end_date_obj = None

        response = requests.get(CONF_CS_URL)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        conferences = []

        # 找到会议表格
        table = soup.find('table')
        if not table:
            print("未找到会议表格")
            return []

        rows = table.find_all('tr')[1:]  # 跳过表头行
        print(f"找到 {len(rows)} 个会议条目")

        for row in rows:
            try:
                cols = row.find_all('td')
                if len(cols) < 8:  # 确保有足够的列
                    continue

                conference_name = cols[1].get_text(strip=True)
                abstract_deadline = cols[3].get_text(strip=True)
                submission_deadline = cols[4].get_text(strip=True)
                notification_date = cols[5].get_text(strip=True)
                conference_dates = cols[6].get_text(strip=True)
                proceedings = cols[7].get_text(strip=True)
                core_ranking = cols[8].get_text(strip=True) if len(cols) > 8 else "N/A"

                # 提取地点信息（通常在会议日期字段的括号中）
                location_match = re.search(r'\((.*?)\)', conference_dates)
                location = location_match.group(1) if location_match else "N/A"
                
                # 清理会议日期字段
                conference_dates = re.sub(r'\(.*?\)', '', conference_dates).strip()

                print(f"\n会议信息:")
                print(f"  名称: {conference_name}")
                print(f"  摘要截止: {abstract_deadline}")
                print(f"  投稿截止: {submission_deadline}")
                print(f"  通知日期: {notification_date}")
                print(f"  会议日期: {conference_dates}")
                print(f"  地点: {location}")
                print(f"  会议级别: {core_ranking}")

                # 解析截止日期
                abstract_details = extract_deadline_details_from_text(abstract_deadline)
                submission_details = extract_deadline_details_from_text(submission_deadline)
                notification_details = extract_deadline_details_from_text(notification_date) # 新增对通知日期的处理

                # 日期筛选逻辑（改进版：更宽松的筛选策略）
                perform_date_filter = bool(start_date_obj and end_date_obj)
                conference_passes_date_filter = True  # 默认通过，除非明确不符合条件

                if perform_date_filter:
                    notification_date_str_from_details = notification_details.get('date_str')
                    if notification_date_str_from_details:
                        try:
                            # 提取日期部分进行比较
                            conf_notification_date_part = notification_date_str_from_details.split(' ')[0]
                            conf_date = datetime.strptime(conf_notification_date_part, "%Y-%m-%d").date()
                            if start_date_obj <= conf_date <= end_date_obj:
                                print(f"  会议 {conference_name} 的通知日期 {conf_date} 在范围 {start_date_obj} - {end_date_obj} 内。")
                            else:
                                print(f"  会议 {conference_name} 的通知日期 {conf_date} 不在范围 {start_date_obj} - {end_date_obj} 内，但仍保留。")
                        except ValueError as ve:
                            print(f"  无法解析会议 {conference_name} 的通知日期 '{notification_date_str_from_details}' 进行筛选: {ve}。保留该会议。")
                    else:
                        print(f"  会议 {conference_name} 未能提取有效的通知日期，保留该会议。")
                
                # 不进行严格筛选，保留所有会议数据
                # if perform_date_filter and not conference_passes_date_filter:
                #     continue # 如果需要筛选且会议未通过筛选，则跳过

                # 尝试从 conference_name 中提取 acronym，如果无法简单提取，则都使用 full_name
                acronym = conference_name.split(' ')[0] if conference_name else 'N/A' # 简单提取第一个词作为acronym
                full_name = conference_name

                conference = {
                    'acronym': acronym, # 使用 acronym
                    'full_name': full_name, # 使用 full_name
                    'location': location,
                    'when': conference_dates,
                    'category': category_name if category_name else "Computer Science",
                    'proceedings': proceedings,
                    'rank': core_ranking, # 键名改为 rank 以匹配其他地方的用法
                    'url': CONF_CS_URL, # 添加一个url字段，虽然这里是列表页的URL
                    'deadlines_raw': f"Abstract: {abstract_deadline}, Submission: {submission_deadline}, Notification: {notification_date}", # 原始截止日期文本
                    'extracted_deadlines': {
                        'abstract_deadline': abstract_details,
                        'submission_deadline': submission_details,
                        'notification_date': notification_details
                    }
                }
                conferences.append(conference)

            except Exception as e:
                print(f"  处理会议行时出错: {e}")
                import traceback
                print(traceback.format_exc())
                continue

        print(f"\n成功解析 {len(conferences)} 个会议信息")
        return conferences

    except requests.exceptions.RequestException as e:
        print(f"错误: 请求网站失败: {e}")
        return []
    except Exception as e:
        print(f"错误: 解析网站内容失败: {e}")
        import traceback
        print(traceback.format_exc())
        return []