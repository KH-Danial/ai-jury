import requests
import base64
import os

# لیست لینک‌های جمع‌کننده کانفیگ - می‌توانی هر زمان اینجا اضافه کنی
urls = [
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/refs/heads/main/server.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub1.txt',
    'https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub2.txt',
    'https://www.v2nodes.com/subscriptions/country/all/?key=E8FF7329C918147',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_RAW.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_BASE64.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_base64_Sub.txt'
]

# نام فایل‌های خروجی برای هر پروتکل
OUTPUT_FILES = {
    'vless': 'vless.txt',
    'reality': 'reality.txt',
    'vmess': 'vmess.txt',
    'trojan': 'trojan.txt',
    'hysteria2': 'hysteria2.txt',
    'shadowsocks': 'ss.txt',
    'socks': 'socks.txt',
    'wireguard': 'wireguard.txt'
}

def decode_if_base64(content):
    """اگر محتوا Base64 باشد رمزگشایی می‌کند، در غیر این صورت خودش را برمی‌گرداند."""
    try:
        return base64.b64decode(content).decode('utf-8', errors='ignore')
    except:
        return content

def extract_configs_from_line(line):
    """یک خط را بررسی و نوع پروتکل آن را تشخیص می‌دهد."""
    line = line.strip()
    if not line:
        return None, None

    # VLESS (با یا بدون Reality)
    if line.startswith('vless://'):
        if 'security=reality' in line:
            return 'reality', line
        return 'vless', line
    elif line.startswith('vmess://'):
        return 'vmess', line
    elif line.startswith('trojan://'):
        return 'trojan', line
    elif line.startswith('hysteria2://') or line.startswith('hy2://'):
        return 'hysteria2', line
    elif line.startswith('ss://'):
        return 'shadowsocks', line
    elif line.startswith('socks4://') or line.startswith('socks5://'):
        return 'socks', line
    elif line.startswith('wireguard://') or '[interface]' in line.lower():
        return 'wireguard', line
    return None, None

def main():
    # دیکشنری‌ای از مجموعه‌ها برای هر پروتکل
    configs_by_protocol = {key: set() for key in OUTPUT_FILES.keys()}

    # ۱. خواندن و دسته‌بندی
    for url in urls:
        try:
            print(f"Fetching: {url}")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                decoded_data = decode_if_base64(resp.text.strip())
                for line in decoded_data.splitlines():
                    proto, config_line = extract_configs_from_line(line)
                    if proto:
                        configs_by_protocol[proto].add(config_line)
            else:
                print(f"   ⚠️ {url} returned {resp.status_code}")
        except Exception as e:
            print(f"   ❌ Failed: {url} - {e}")

    # ۲. ذخیره‌سازی فایل‌های خروجی
    for protocol, configs in configs_by_protocol.items():
        if configs:
            text = "\n".join(sorted(configs))
            # رمزنگاری Base64 برای سازگاری با V2RayNG
            encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            filename = OUTPUT_FILES[protocol]
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(encoded_text)
            print(f"✅ {filename}: {len(configs)} configs saved.")
        else:
            print(f"⚠️ {OUTPUT_FILES[protocol]}: no configs found.")

    # ۳. (اختیاری) ساخت فایل کلی برای سازگاری با گذشته
    all_configs = set()
    for configs in configs_by_protocol.values():
        all_configs.update(configs)
    if all_configs:
        text = "\n".join(sorted(all_configs))
        encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        with open('sub_converted.txt', 'w', encoding='utf-8') as f:
            f.write(encoded_text)
        print(f"✅ sub_converted.txt: {len(all_configs)} total configs.")

if __name__ == "__main__":
    main()
