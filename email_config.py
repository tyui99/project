# 邮件配置文件
# 请根据您的邮箱服务商配置以下信息

# 常见邮箱服务商SMTP配置示例：
# QQ邮箱: smtp.qq.com, 端口587(TLS)或465(SSL)
# 163邮箱: smtp.163.com, 端口587(TLS)或465(SSL) 
# Gmail: smtp.gmail.com, 端口587(TLS)或465(SSL)
# Outlook: smtp-mail.outlook.com, 端口587(TLS)

# SMTP服务器配置
SMTP_CONFIG = {
    'server': 'smtp.qq.com',  # 例如: 'smtp.qq.com'
    'port': 587,   # TLS端口587，SSL端口465
    'username': 'your_email@example.com',  # 您的邮箱地址
    'password': 'YOUR_EMAIL_PASSWORD_OR_APP_SPECIFIC_PASSWORD',  # 您的邮箱密码或授权码
    'sender_email': 'your_email@example.com',  # 发件人邮箱（通常与username相同）
    'sender_name': '会议提醒助手',  # 发件人显示名称
    'use_tls': True  # True使用TLS，False使用SSL
}

# 邮件模板配置
EMAIL_TEMPLATES = {
    'submission_reminder': {
        'subject': '📝 会议投稿截止提醒 - {conference_name}',
        'template': '''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                    📝 投稿截止提醒
                </h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #dc3545; margin-top: 0;">⚠️ 紧急提醒</h3>
                    <p><strong>{conference_name}</strong> 的投稿截止时间即将到来！</p>
                </div>
                
                <div style="background-color: #fff; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px;">
                    <h4 style="color: #495057; margin-top: 0;">📋 会议信息</h4>
                    <ul style="list-style-type: none; padding: 0;">
                        <li><strong>会议名称:</strong> {conference_name}</li>
                        <li><strong>投稿截止:</strong> <span style="color: #dc3545; font-weight: bold;">{submission_deadline}</span></li>
                        <li><strong>通知时间:</strong> {notification_date}</li>
                        <li><strong>会议时间:</strong> {conference_date}</li>
                        <li><strong>会议地点:</strong> {location}</li>
                    </ul>
                </div>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #d1ecf1; border-radius: 5px;">
                    <p style="margin: 0; color: #0c5460;">
                        <strong>💡 温馨提示:</strong> 距离投稿截止还有 <strong>{days_left}</strong> 天，请抓紧时间完成投稿！
                    </p>
                </div>
                
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px; border-top: 1px solid #dee2e6; padding-top: 15px;">
                    此邮件由会议提醒系统自动发送，如需取消订阅请在系统中进行设置。
                </p>
            </div>
        </body>
        </html>
        '''
    },
    
    'notification_reminder': {
        'subject': '📢 会议通知时间提醒 - {conference_name}',
        'template': '''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745; border-bottom: 2px solid #28a745; padding-bottom: 10px;">
                    📢 录用通知提醒
                </h2>
                
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #155724; margin-top: 0;">🎯 关注通知</h3>
                    <p><strong>{conference_name}</strong> 的录用通知时间即将到来！</p>
                </div>
                
                <div style="background-color: #fff; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px;">
                    <h4 style="color: #495057; margin-top: 0;">📋 会议信息</h4>
                    <ul style="list-style-type: none; padding: 0;">
                        <li><strong>会议名称:</strong> {conference_name}</li>
                        <li><strong>通知时间:</strong> <span style="color: #28a745; font-weight: bold;">{notification_date}</span></li>
                        <li><strong>会议时间:</strong> {conference_date}</li>
                        <li><strong>会议地点:</strong> {location}</li>
                    </ul>
                </div>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #d1ecf1; border-radius: 5px;">
                    <p style="margin: 0; color: #0c5460;">
                        <strong>💡 温馨提示:</strong> 距离通知时间还有 <strong>{days_left}</strong> 天，请关注邮箱和会议官网！
                    </p>
                </div>
                
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px; border-top: 1px solid #dee2e6; padding-top: 15px;">
                    此邮件由会议提醒系统自动发送，如需取消订阅请在系统中进行设置。
                </p>
            </div>
        </body>
        </html>
        '''
    },
    
    'camera_ready_reminder': {
        'subject': '📄 终稿提交提醒 - {conference_name}',
        'template': '''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #fd7e14; border-bottom: 2px solid #fd7e14; padding-bottom: 10px;">
                    📄 终稿提交提醒
                </h2>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #856404; margin-top: 0;">📝 准备终稿</h3>
                    <p><strong>{conference_name}</strong> 的终稿提交截止时间即将到来！</p>
                </div>
                
                <div style="background-color: #fff; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px;">
                    <h4 style="color: #495057; margin-top: 0;">📋 会议信息</h4>
                    <ul style="list-style-type: none; padding: 0;">
                        <li><strong>会议名称:</strong> {conference_name}</li>
                        <li><strong>终稿截止:</strong> <span style="color: #fd7e14; font-weight: bold;">{camera_ready_deadline}</span></li>
                        <li><strong>会议时间:</strong> {conference_date}</li>
                        <li><strong>会议地点:</strong> {location}</li>
                    </ul>
                </div>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #d1ecf1; border-radius: 5px;">
                    <p style="margin: 0; color: #0c5460;">
                        <strong>💡 温馨提示:</strong> 距离终稿截止还有 <strong>{days_left}</strong> 天，请按照会议要求准备最终版本！
                    </p>
                </div>
                
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px; border-top: 1px solid #dee2e6; padding-top: 15px;">
                    此邮件由会议提醒系统自动发送，如需取消订阅请在系统中进行设置。
                </p>
            </div>
        </body>
        </html>
        '''
    }
}

# 验证配置是否完整
def is_email_configured():
    """检查邮件配置是否完整"""
    config = SMTP_CONFIG
    required_fields = ['server', 'username', 'password', 'sender_email']
    return all(config.get(field) and config.get(field).strip() for field in required_fields)

# 获取配置状态信息
def get_config_status():
    """获取配置状态信息"""
    if is_email_configured():
        return "✅ 邮件配置已完成"
    else:
        return "❌ 邮件配置未完成，请在 email_config.py 中配置SMTP信息"