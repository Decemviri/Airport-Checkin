import requests
import json
import os
import urllib3
import time

# 禁用 requests 的安全警告
urllib3.disable_warnings()

# 获取环境变量
SCKEY = os.environ.get('SCKEY', '')
TG_BOT_TOKEN = os.environ.get('TGBOT', '')
TG_USER_ID = os.environ.get('TGUSERID', '')
EMAIL = os.environ.get('EMAIL', '')
PASSWORD = os.environ.get('PASSWORD', '')
BASE_URL = os.environ.get('BASE_URL', '')

def checkin(email, password, base_url):
    if not email or not password or not base_url:
        print("环境变量未正确加载，请检查 GitHub Secrets 配置。")
        return "环境变量缺失"

    # 处理邮箱中的 @ 符号，转换为 URL 编码
    email_parts = email.split('@')
    encoded_email = email_parts[0] + '%40' + email_parts[1]
    
    session = requests.session()
    session.trust_env = False 
    
    # 使用较新的 Chrome User-Agent，替换掉原来 2017 年的旧版本，降低被拦截概率
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    try:
        # 1. 先访问首页，获取初始 Cookie
        print("正在访问首页...")
        session.get(base_url, headers={'User-Agent': user_agent}, verify=False, timeout=15)
        time.sleep(2)  # 增加延时，避免请求过快触发反爬
        
        # 2. 发送登录请求
        print("正在尝试登录...")
        login_url = base_url + '/auth/login'
        login_headers = {
            'User-Agent': user_agent,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Origin': base_url,
            'Referer': base_url + '/auth/login',
            'X-Requested-With': 'XMLHttpRequest'  # 伪装成 Ajax 请求
        }
        post_data = 'email=' + encoded_email + '&passwd=' + password + '&code='
        
        session.post(login_url, data=post_data.encode(), headers=login_headers, verify=False, timeout=15)
        time.sleep(2)
        
        # 3. 发送签到请求
        print("正在尝试签到...")
        checkin_headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Origin': base_url,
            'Referer': base_url + '/user',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = session.post(base_url + '/user/checkin', headers=checkin_headers, verify=False, timeout=15)
        
        # 解析返回结果
        response_data = json.loads(response.text)
        print("签到结果:", response_data['msg'])
        return response_data['msg']
        
    except json.JSONDecodeError:
        print("解析 JSON 失败，可能被防火墙拦截。服务器返回内容为:", response.text)
        return "解析数据失败或被拦截"
    except Exception as e:
        print("网络请求发生异常:", str(e))
        return "网络请求异常"

if __name__ == '__main__':
    result = checkin(EMAIL, PASSWORD, BASE_URL)
    
    # 消息推送逻辑
    if SCKEY != '':
        print("正在发送 Server酱 推送...")
        sendurl = 'https://sctapi.ftqq.com/' + SCKEY + '.send?title=机场签到&desp=' + result
        requests.get(url=sendurl, verify=False)
        
    if TG_USER_ID != '' and TG_BOT_TOKEN != '':
        print("正在发送 Telegram 推送...")
        sendurl = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage?chat_id={TG_USER_ID}&text={result}&disable_web_page_preview=True'
        requests.get(url=sendurl, verify=False)

    print("脚本执行完毕。")
