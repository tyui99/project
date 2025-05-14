import unittest
from unittest.mock import patch
from pachong import convert_to_beijing_time, extract_deadline_details_from_text, fetch_conferences
from datetime import datetime, timezone, timedelta

class TestPachong(unittest.TestCase):
    def test_convert_to_beijing_time(self):
        print('\n测试时区转换功能...')
        # 测试基本时区转换
        test_cases = [
            {
                'date_str': '2024-03-15 10:00:00',
                'tz_str': 'UTC',
                'expected_hour': 18  # UTC+8
            },
            {
                'date_str': '2024-03-15 10:00:00',
                'tz_str': 'PST',
                'expected_hour': 2   # 第二天
            },
            {
                'date_str': '2024-03-15 23:59:59',
                'tz_str': 'AoE',
                'expected_hour': 19   # 第二天
            }
        ]
        
        for case in test_cases:
            print(f"测试用例: {case['date_str']} {case['tz_str']}")
            result = convert_to_beijing_time(case['date_str'], case['tz_str'])
            self.assertIsNotNone(result)
            print(f"转换结果: {result}")
            self.assertEqual(result.hour, case['expected_hour'])

    def test_extract_deadline_details(self):
        print('\n测试截止日期提取功能...')
        test_text = """
        Paper Submission Deadline: March 15, 2024, 23:59 AoE
        Abstract Deadline: March 1, 2024 (UTC-7)
        Notification Date: May 1, 2024
        Camera Ready: June 1, 2024
        """
        print(f"测试文本:\n{test_text}")
        
        result = extract_deadline_details_from_text(test_text)
        print(f"提取结果: {result}")
        
        self.assertIn('submission_deadline', result)
        self.assertIn('abstract_deadline', result)
        self.assertIn('notification_date', result)
        self.assertIn('camera_ready', result)

    @patch('requests.get')
    def test_fetch_conferences(self, mock_get):
        print('\n测试会议信息爬取功能...')
        
        # 配置模拟响应
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.content = '<html><div class="contsec"></div></html>'
        mock_get.return_value = mock_response
        
        conferences = fetch_conferences()
        
        self.assertIsInstance(conferences, list)
        if conferences:  # 如果成功获取到会议信息
            print(f"成功获取到 {len(conferences)} 个会议信息")
            for conf in conferences[:2]:  # 只打印前两个会议的信息作为示例
                print(f"\n会议信息示例:")
                for key, value in conf.items():
                    print(f"{key}: {value}")
        else:
            print(f"请求状态码: {response.status_code}")
            print(f"响应内容:\n{response.content[:1000]}")  # 打印前1000字符
            response.raise_for_status()
            print("成功获取网页内容，开始解析...")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 调试日志：打印解析到的会议条目数量
            rows = soup.select('div.contsec table table tr')
            print(f"找到{len(rows)}个会议条目")
            for i, row in enumerate(rows[:3]):  # 打印前3个条目
                print(f"条目{i} HTML:\n{str(row)[:500]}")
            
            conferences = []
        
        self.assertIsInstance(conferences, list)
        if conferences:  # 如果成功获取到会议信息
            print(f"成功获取到 {len(conferences)} 个会议信息")
            for conf in conferences[:2]:  # 只打印前两个会议的信息作为示例
                print(f"\n会议信息示例:")
                for key, value in conf.items():
                    print(f"{key}: {value}")
        else:
            print("未获取到会议信息，请检查网络连接或网站可访问性")

if __name__ == '__main__':
    unittest.main(argv=[''], verbosity=2)