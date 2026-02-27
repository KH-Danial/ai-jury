import requests
import base64

# لیست منابع شما
urls = [
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/refs/heads/main/server.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub1.txt',
    'https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub2.txt',
    'https://www.v2nodes.com/subscriptions/country/all/?key=E8FF7329C918147',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_RAW.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_BASE64.txt'
]

def decode_if_base64(content):
    try:
        return base64.b64decode(content).decode('utf-8')
    except:
        return content

def main():
    unique_configs = set()
    for url in urls:
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                decoded_data = decode_if_base64(resp.text.strip())
                for line in decoded_data.splitlines():
                    if line.startswith(('vless://', 'vmess://', 'trojan://', 'ss://')):
                        unique_configs.add(line.strip())
        except:
            pass
    final_text = "\n".join(list(unique_configs))
    encoded_final = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    with open('second_sub.txt', 'w', encoding='utf-8') as f:
        f.write(encoded_final)

if __name__ == "__main__":
    main()
