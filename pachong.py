import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, timedelta
import dateparser # 新增导入

# CCF 会议列表URL
CCF_URL = 'https://ccf.atom.im/'

# 时区转换函数：将任意时区时间转换为北京时间
def convert_to_beijing_time(date_str, original_tz_str=None):
    """
    将给定日期字符串和可选的原始时区信息转换为北京时间 (UTC+8)。
    如果 original_tz_str 为 None，dateparser 会尝试自动检测。
    :param date_str: 日期字符串，例如 "YYYY-MM-DD HH:MM:SS", "Month DD, YYYY, HH:MM AM/PM TZ", "YYYY-MM-DD"
    :param original_tz_str: 原始时区字符串，例如 "UTC-5", "PST", "EDT", "AoE". 
                            如果 date_str 本身包含时区信息 (如 'UTC-7' 或 'PST')，此参数可以省略或用于覆盖。
    :return: 北京时间 datetime 对象，如果转换失败则返回 None
    """
    try:
        # settings for dateparser
        # 'RETURN_AS_TIMEZONE_AWARE': True ensures datetime object is timezone-aware.
        # 'TIMEZONE': 'UTC' (or any other) can be a default if no timezone is found in string.
        # However, we want to respect original_tz_str or AoE logic first.
        settings = {'RETURN_AS_TIMEZONE_AWARE': True}
        
        dt_aware = None

        if original_tz_str and original_tz_str.upper() == 'AOE':
            # AoE (Anywhere on Earth) is UTC-12. Deadline is end of day in AoE.
            # This means when it's 23:59:59 on date_str in UTC-12.
            # dateparser might not directly understand 'AoE'.
            # We parse the date part and then attach UTC-12 timezone.
            # If date_str includes time, dateparser might parse it with local timezone if not specified.
            # So, it's safer to parse date, then set time to end of day, then set tz.
            dt_naive = dateparser.parse(date_str, settings={'PREFER_DATES_FROM': 'future'}) # Prefer future if year is ambiguous
            if not dt_naive:
                print(f"警告: dateparser 无法解析日期 '{date_str}' 用于 AoE.")
                return None
            # Set to end of the day for that date in AoE timezone
            dt_aoe = dt_naive.replace(hour=23, minute=59, second=59, microsecond=0, tzinfo=timezone(timedelta(hours=-12)))
            dt_aware = dt_aoe
        elif original_tz_str:
            # If original_tz_str is provided, use it to help dateparser
            # dateparser can often handle timezone abbreviations like PST, EST, or offsets like UTC-7
            # We can pass it in settings, or sometimes it's better to append to date_str if not already there
            # Let's try with dateparser's TIMEZONE setting or by letting it parse from string.
            # If date_str already has tz info, dateparser should use it.
            # If not, original_tz_str can guide it.
            dt_aware = dateparser.parse(date_str, settings={'TIMEZONE': original_tz_str, **settings})
            if not dt_aware: # Fallback if TIMEZONE setting didn't work as expected
                 dt_aware = dateparser.parse(f"{date_str} {original_tz_str}", settings=settings)

        if not dt_aware:
            # If no original_tz_str or previous attempts failed, let dateparser try its best.
            dt_aware = dateparser.parse(date_str, settings=settings)

        if not dt_aware:
            print(f"错误: dateparser 无法解析日期时间 '{date_str}' (原始时区: {original_tz_str})")
            return None

        # If not timezone aware after parsing (should not happen with RETURN_AS_TIMEZONE_AWARE=True)
        # or if we need to be absolutely sure about the source timezone if it was ambiguous.
        if dt_aware.tzinfo is None:
            # This case should be rare with RETURN_AS_TIMEZONE_AWARE. 
            # If it happens, it implies ambiguity. We might assume UTC or local.
            # For safety, let's assume UTC if original_tz_str was not helpful.
            print(f"警告: 解析后的日期 '{dt_aware}' 无时区信息，假设为UTC.")
            dt_aware = dt_aware.replace(tzinfo=timezone.utc)
            
        beijing_tz = timezone(timedelta(hours=8))
        return dt_aware.astimezone(beijing_tz)

    except Exception as e:
        print(f"错误: 转换时间 '{date_str}' (时区: {original_tz_str}) 失败: {e}")
        return None

def extract_deadline_details_from_text(text_block):
    """
    从文本块中提取不同类型的截止日期及其相关信息。
    :param text_block: 包含截止日期信息的字符串
    :return: 字典，键是截止日期类型 (str)，值是包含 'date_str' 和 'tz_str' 的字典
             例如: {'submission_deadline': {'date_str': 'Sep 20, 2024, 11:59 PM', 'tz_str': 'AoE'}, ...}
    """
    deadlines = {}
    # 常见的截止日期关键词和可能的类型映射
    # 顺序很重要，更具体的应该放在前面
    deadline_keywords_map = {
        r'(?:paper|full paper|manuscript|final version|submission) deadline': 'submission_deadline',
        r'abstract deadline': 'abstract_deadline',
        r'registration deadline': 'registration_deadline',
        r'(?i)(?:notification\s+date|notification\s+due|acceptance\s+notice\s+date|author\s+notification|paper\s+decision\s+date)': 'notification_date',
        r'(?i)(?:camera[\s-]*ready|final\\s+version)[\s:]*': 'camera_ready',
        r'start date|conference date': 'start_date',
        r'end date': 'end_date',
        r'(?:workshop|tutorial)\s+proposal\s+deadline': 'workshop_proposal_deadline',
    }
    
    tz_indicators = ['AoE', 'UTC', 'PST', 'PDT', 'EST', 'EDT', 'CST', 'CDT', 'GMT', 'CET', 'CEST', 'AEST', 'ACST']
    utc_offset_pattern = r'UTC[+-]\d{1,2}(?::\d{2})?\b'
    
    # 拆分文本块为多行进行处理，因为信息可能分布在多行
    lines = text_block.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]

    for line in cleaned_lines:
        for keyword_regex, deadline_type in deadline_keywords_map.items():
            match = re.search(keyword_regex, line, re.IGNORECASE)
            if match:
                # 关键词匹配成功，尝试提取日期和时区
                # 移除关键词部分，剩余部分应该是日期和时区信息
                remaining_text = line[match.end():].strip()
                if remaining_text.startswith(':'):
                    remaining_text = remaining_text[1:].strip()
                
                # 尝试从剩余文本中解析日期和时区
                # dateparser 通常能处理 "Month DD, YYYY, HH:MM AM/PM TZ" 或 "YYYY-MM-DD (TZ)"
                # 我们需要分离日期字符串和时区指示符 (如 AoE, UTC, PST)
                
                # 常见时区指示符
                tz_indicators = ['AoE', 'UTC', 'PST', 'PDT', 'EST', 'EDT', 'CST', 'CDT', 'MST', 'MDT', 
                                 'GMT', 'CET', 'CEST'] 
                # Regex for explicit UTC offsets like UTC+8, UTC-5:00
                utc_offset_pattern = r'UTC[+-]\d{1,2}(?::\d{2})?'
                
                date_part = remaining_text
                tz_part = None

                # 优先匹配显式UTC偏移
                tz_match = re.search(f'({utc_offset_pattern})', remaining_text, re.IGNORECASE)
                if tz_match:
                    tz_part = tz_match.group(1).upper()
                    # 移除匹配到的时区，保留日期部分
                    date_part = re.sub(f'\s*\({tz_part}\)\s*|\s*{tz_part}\s*', '', remaining_text, flags=re.IGNORECASE).strip()
                else:
                    # 匹配其他时区指示符
                    for tz_ind in tz_indicators:
                        # Match tz_ind possibly in parentheses or as a standalone word
                        # e.g., "(AoE)", "AoE", "11:59 PM PST"
                        tz_pattern = r'(?:\(\s*' + re.escape(tz_ind) + r'\s*\)|\b' + re.escape(tz_ind) + r'\b)'
                        tz_search = re.search(tz_pattern, remaining_text, re.IGNORECASE)
                        if tz_search:
                            tz_part = tz_ind  # 保持原始时区标识符大小写
                            # 移除匹配到的时区，保留日期部分
                            date_part = re.sub(tz_pattern, '', remaining_text, flags=re.IGNORECASE).strip()
                            break
                
                date_part = date_part.replace('截止日期', '').replace('Deadline', '').replace(':', '').strip()
                date_part = re.sub(r'^\s*-\s*', '', date_part).strip() # 移除开头的 '-' 和空格

                if date_part:
                    # 如果已经有这个类型的截止日期，并且新的更具体（例如包含时间），则考虑更新
                    # 简单起见，这里我们只取第一个匹配到的
                    if deadline_type not in deadlines:
                        deadlines[deadline_type] = {'date_str': date_part, 'tz_str': tz_part}
                        # print(f"  Extracted for {deadline_type}: date='{date_part}', tz='{tz_part}' from line: '{line}'")
                break # 处理完当前行的第一个匹配关键词后，跳到下一行
    return deadlines

def fetch_conferences():
    """
    从WikiCFP爬取近期计算机领域国际会议信息
    :return: 包含会议信息的列表，每个会议是一个字典
    """
    try:
        WIKICFP_URL = 'http://www.wikicfp.com/cfp/call?conference=computer%20science'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        print(f"开始请求 {WIKICFP_URL}...")
        response = requests.get(WIKICFP_URL, headers=headers, timeout=30)
        print(f"请求状态码: {response.status_code}")
        response.raise_for_status()
        print("成功获取网页内容，开始解析...")
        soup = BeautifulSoup(response.content, 'html.parser')
        conferences = []

        # 解析会议条目
        for row in soup.select('div.contsec table table tr'):
            cols = row.select('td')
            if len(cols) >= 4:
                # 提取基础信息
                name_elem = cols[0].find('a')
                if not name_elem:
                    continue

                conference = {
                    'name': name_elem.text.strip(),
                    'link': f"http://www.wikicfp.com{name_elem['href']}",
                    'location': cols[1].text.strip(),
                    'when': cols[2].text.strip(),
                    'deadline': cols[3].text.strip()
                }

                # 提取详细日期信息
                deadline_text = cols[3].text.strip()
                if ':' in deadline_text:
                    conference['deadline_details'] = extract_deadline_details_from_text(
                        f"Submission Deadline: {deadline_text}"
                    )

                conferences.append(conference)

        print(f"解析到 {len(conferences)} 个会议信息")
        print("错误: 未找到会议表格，网页结构可能已改变")
        return []

        rows = conference_table.find_all('tr')[1:]
        print(f"开始解析会议表格，找到 {len(rows)} 行数据")

        for index, row in enumerate(rows, 1):
            cols = row.find_all('td')
            if len(cols) < 6:
                print(f"跳过第 {index} 行：列数不足")
                continue

            acronym = cols[1].text.strip()
            full_name = cols[2].text.strip()
            rank = cols[3].text.strip()
            conference_info_cell = cols[5]
            
            print(f"\n正在处理第 {index} 个会议：{acronym} ({rank})")
            print(f"会议全称：{full_name}")
            
            conference_link_tag = cols[1].find('a')
            conference_url = conference_link_tag['href'] if conference_link_tag and 'href' in conference_link_tag.attrs else None
            if conference_url:
                if not conference_url.startswith('http'):
                    conference_url = requests.compat.urljoin(CCF_URL, conference_url)
                print(f"会议链接：{conference_url}")
            else:
                print("未找到会议链接")

            raw_deadline_text = conference_info_cell.get_text(separator='\n').strip()
            print("开始解析截止日期信息...")
            # 使用新的提取函数
            extracted_deadlines_info = extract_deadline_details_from_text(raw_deadline_text)
            if extracted_deadlines_info:
                print("找到以下截止日期：")
                for deadline_type, details in extracted_deadlines_info.items():
                    print(f"  - {deadline_type}: {details['date_str']} ({details['tz_str'] if details['tz_str'] else '时区未指定'})")
            else:
                print("未找到任何截止日期信息")

            conferences.append({
                'acronym': acronym,
                'full_name': full_name,
                'rank': rank,
                'url': conference_url,
                'deadlines_raw': raw_deadline_text, # 保留原始文本以供调试
                'extracted_deadlines': extracted_deadlines_info, # 新增：结构化的原始截止日期信息
                'parsed_deadlines': {} # 解析后的北京时间截止日期将由logic模块填充
            })

        return conferences

    except requests.exceptions.RequestException as e:
        print(f"错误: 请求CCF网站失败: {e}")
        return []
    except Exception as e:
        print(f"错误: 解析CCF网站内容失败: {e}")
        return []

# 示例：爬取人工智能类别的会议
if __name__ == '__main__':
    print("开始爬取CCF会议信息...")
    ai_conferences = fetch_conferences(category_name="人工智能")
    # ai_conferences = fetch_conferences(category_name="计算机网络") # 测试其他类别
    
    if ai_conferences:
        print(f"\n成功爬取到 {len(ai_conferences)} 个会议信息:")
        for conf in ai_conferences:
            print(f"  简称: {conf['acronym']}")
            print(f"  全称: {conf['full_name']}")
            # print(f"  级别: {conf['rank']}")
            # print(f"  链接: {conf['url']}")
            # print(f"  原始截止日期文本: {conf['deadlines_raw']}")
            print(f"  提取的截止日期: {conf['extracted_deadlines']}")
            
            # 测试转换提取出的日期
            if conf['extracted_deadlines']:
                print("    转换后的北京时间:")
                for deadline_type, details in conf['extracted_deadlines'].items():
                    bj_time = convert_to_beijing_time(details['date_str'], details['tz_str'])
                    if bj_time:
                        print(f"      {deadline_type}: {bj_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
                    else:
                        print(f"      {deadline_type}: 转换失败 (原始: {details['date_str']}, {details['tz_str']})")
            print("-" * 20)
    else:
        print("未能爬取到会议信息。")

    print("\n测试时区转换功能 (使用 dateparser):")
    test_dates = [
        ("2024-07-20 17:00:00", "UTC-7", "美国太平洋夏令时PDT"),
        ("July 20, 2024, 5:00 PM", "PDT", "美国太平洋夏令时PDT 另一种格式"),
        ("2024-08-15 23:59:59", "AoE", "全球任意地区AoE"),
        ("August 15, 2024", "AoE", "全球任意地区AoE 只有日期"),
        ("2024-09-01 10:00:00", "UTC+2", "欧洲中部夏令时CEST"),
        ("2023-03-10", "UTC", "UTC日期无时间"),
        ("March 10, 2023, UTC", None, "UTC日期，时区在字符串中"),
        ("2023-11-05 01:30:00", "PST", "美国太平洋标准时间PST"),
        ("2024-12-25 08:00:00", "Asia/Shanghai", "北京时间 (直接指定)"),
        ("Dec 25, 2024, 08:00 AM", "Asia/Shanghai", "北京时间 (直接指定)"),
        ("2024-01-15 12:00:00 JST", None, "日本标准时间 (JST在字符串中)"), # JST = UTC+9
        ("Deadline: September 20, 2024, 11:59 PM AoE", None, "包含文本的复杂字符串 - extract_deadline_details应处理")
    ]
    for date_str, tz_str, desc in test_dates:
        # 对于最后一个复杂字符串，我们应该先用 extract_deadline_details_from_text
        if "Deadline:" in date_str:
            print(f"\n测试复杂行解析: '{date_str}'")
            extracted = extract_deadline_details_from_text(date_str)
            print(f"  提取结果: {extracted}")
            if extracted:
                for _, details in extracted.items():
                    bj_time = convert_to_beijing_time(details['date_str'], details['tz_str'])
                    if bj_time:
                        print(f"  原始: {details['date_str']} ({details['tz_str']}), 北京时间: {bj_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
                    else:
                        print(f"  原始: {details['date_str']} ({details['tz_str']}), 转换失败")
            continue

        bj_time = convert_to_beijing_time(date_str, tz_str)
        if bj_time:
            print(f"原始: {date_str} ({desc} - {tz_str if tz_str else '自动检测'}), 北京时间: {bj_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        else:
            print(f"原始: {date_str} ({desc} - {tz_str if tz_str else '自动检测'}), 转换失败")