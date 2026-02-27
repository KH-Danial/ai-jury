import requests
import base64
import re

# لیست منابع شما
urls = [
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/refs/heads/main/server.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub1.txt',
    'https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub2.txt',
    'https://raw.githubusercontent.com/itsyebekhe/PSG/main/lite/subscriptions/xray/base64/trojan',
    'https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/all_extracted_configs.txt',
    'https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/all_configs.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_base64_Sub.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_Sub.txt',
    'https://raw.githubusercontent.com/barry-far/V2ray-config/main/All_Configs_base64_Sub.txt',
    'https://raw.githubusercontent.com/frank-vpl/servers/refs/heads/main/irbox',
    'https://www.v2nodes.com/subscriptions/country/all/?key=E8FF7329C918147'
]

def get_flag(code):
    if not code or code == "??": return "🏳️"
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def get_country_data(address):
    """دریافت کد کشور برای مرتب‌سازی و پرچم"""
    try:
        clean_addr = address.split(':')[0]
        # استفاده از API برای تشخیص کشور
        resp = requests.get(f'http://ip-api.com/json/{clean_addr}', timeout=3).json()
        if resp.get('status') == 'success':
            return resp.get('countryCode'), get_flag(resp.get('countryCode'))
    except: pass
    return "ZZ", "🏳️"

def decode_if_base64(content):
    try:
        return base64.b64decode(content).decode('utf-8')
    except:
        return content

def main():
    print("در حال استخراج و پاکسازی تکراری‌ها...")
    raw_configs = set()
    
    # ۱. جمع‌آوری تمام کانفیگ‌ها
    for url in urls:
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                decoded_data = decode_if_base64(resp.text.strip())
                for line in decoded_data.splitlines():
                    if line.startswith(('vless://', 'vmess://', 'trojan://', 'ss://')):
                        raw_configs.add(line.strip())
        except: pass

    processed_data = []
    seen_ips = set()

    # ۲. استخراج IP، حذف تکراری‌ها و دریافت اطلاعات کشور
    for config in raw_configs:
        try:
            match = re.search(r'@([^:/]+):(\d+)', config)
            if not match: continue
            
            address_port = f"{match.group(1)}:{match.group(2)}"
            
            # جلوگیری از ورود IP تکراری
            if address_port in seen_ips:
                continue
            seen_ips.add(address_port)
            
            country_code, flag = get_country_data(match.group(1))
            clean_link = config.split('#')[0]
            
            processed_data.append({
                'link': clean_link,
                'country_code': country_code,
                'flag': flag
            })
        except: continue

    # ۳. مرتب‌سازی بر اساس کد کشور (برای پشت سر هم قرار گرفتن IPهای هر کشور)
    processed_data.sort(key=lambda x: x['country_code'])

    # ۴. شماره‌گذاری و ساخت خروجی نهایی
    output_lines = []
    for i, item in enumerate(processed_data, 1):
        # فرمت درخواستی: 🇩🇪 redline-crypto - 1
        name = f"{item['flag']} redline-crypto - {i}"
        output_lines.append(f"{item['link']}#{name}")

    final_text = "\n".join(output_lines)
    encoded_final = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    
    with open('sub_converted.txt', 'w', encoding='utf-8') as f:
        f.write(encoded_final)
    print(f"عملیات موفقیت‌آمیز: {len(output_lines)} سرور یکتا ذخیره شد.")

if __name__ == "__main__":
    main()
