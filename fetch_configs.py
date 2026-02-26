import requests
import base64
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor

# منابع استخراج سرور
urls = [
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/refs/heads/main/server.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub1.txt',
    'https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/itsyebekhe/PSG/main/lite/subscriptions/xray/base64/trojan',
    'https://raw.githubusercontent.com/frank-vpl/servers/refs/heads/main/irbox',
    'https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/v2ray/base64'
]

def get_flag(code):
    if not code or code == "??": return "🏳️"
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def get_country_info(address):
    try:
        clean_addr = address.split(':')[0]
        resp = requests.get(f'http://ip-api.com/json/{clean_addr}', timeout=2).json()
        if resp.get('status') == 'success':
            return get_flag(resp.get('countryCode'))
    except: pass
    return "🏳️"

def tcp_ping(address, port):
    """تست زنده بودن و محاسبه پینگ (سقف ۲۰۰ میلی‌ثانیه)"""
    start_time = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5) 
        sock.connect((address, int(port)))
        sock.close()
        return int((time.time() - start_time) * 1000)
    except:
        return None

def process_config(config):
    try:
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: return None
        
        address, port = match.group(1), match.group(2)
        ping = tcp_ping(address, port)
        
        if ping is None or ping > 200:
            return None
            
        flag = get_country_info(address)
        clean_config = config.split('#')[0]
        
        # تعیین کیفیت بر اساس پینگ
        if ping < 150:
            quality = "[Excellent]"
        else:
            quality = "[Good]"
        
        return {
            'config': clean_config,
            'ping': ping,
            'flag': flag,
            'quality': quality
        }
    except:
        return None

def main():
    print("در حال استخراج و فیلتر کردن هوشمند...")
    raw_configs = set()
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            content = resp.text.strip()
            try:
                content = base64.b64decode(content).decode('utf-8')
            except: pass
            
            for line in content.splitlines():
                if line.startswith(('vless://', 'vmess://', 'trojan://', 'ss://')):
                    raw_configs.add(line.strip())
        except: pass

    # تست موازی با ۳۰ پردازش همزمان
    final_results = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(process_config, list(raw_configs)[:200]))
        final_results = [r for r in results if r is not None]

    # مرتب‌سازی بر اساس پینگ
    final_results.sort(key=lambda x: x['ping'])

    # ساخت فایل نهایی با برچسب کیفیت
    output_configs = []
    for i, item in enumerate(final_results, 1):
        # فرمت نهایی: 🇮🇷 Excellent redline-crypto - 1 (120ms)
        new_name = f"{item['flag']} {item['quality']} redline-crypto - {i} ({item['ping']}ms)"
        output_configs.append(f"{item['config']}#{new_name}")

    final_text = "\n".join(output_configs)
    encoded_final = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    
    with open('sub_converted.txt', 'w', encoding='utf-8') as f:
        f.write(encoded_final)
    print(f"به‌روزرسانی انجام شد. {len(output_configs)} سرور باکیفیت ذخیره شدند.")

if __name__ == "__main__":
    main()
