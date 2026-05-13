import os, json, requests, re, time
from config import API_BASE_URL, SECRET_NAME
from tsetmc import API_ENDPOINTS as BOURSE_ENDPOINTS, FIELD_MAPS as BOURSE_FIELDS
from Commodity import API_ENDPOINTS as COMMODITY_ENDPOINTS, FIELD_MAPS as COMMODITY_FIELDS
from Crypto import API_ENDPOINTS as CRYPTO_ENDPOINTS, FIELD_MAPS as CRYPTO_FIELDS
from gold_Currency import API_ENDPOINTS as GOLD_ENDPOINTS, FIELD_MAPS as GOLD_FIELDS

GITHUB_TOKEN = os.environ["GH_TOKEN"]
BRSAPI_KEY = os.environ.get(SECRET_NAME, "")

# ═══════════════════════════════════════════════════════════════
# ۱. خواندن اطلاعات Issue
# ═══════════════════════════════════════════════════════════════
event_path = os.environ["GITHUB_EVENT_PATH"]
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue_number = event["issue"]["number"]
title = event["issue"]["title"]
body = event["issue"]["body"] or ""
repo = os.environ["GITHUB_REPOSITORY"]
prompt = f"{title}\n\n{body}"
combined_text = title + " " + body

# ═══════════════════════════════════════════════════════════════
# ۲. ابزارهای کمکی: تشخیص بازار و فراخوانی API
# ═══════════════════════════════════════════════════════════════
def detect_market(text):
    """تشخیص می‌دهد سوال کاربر مربوط به کدام بازار است"""
    if any(kw in text for kw in ["بورس", "سهام", "نماد", "شاخص", "فرابورس", "فملی", "خودرو", "وبملت", "شپنا", "شتران", "کدال", "صندوق", "ETF", "اهرم", "آپشن", "اختیار"]):
        return "borse"
    if any(kw in text for kw in ["کالا", "آتی", "زعفران", "مس", "نفت", "گواهی", "IME", "فولاد", "سیمان", "پتروشیمی"]):
        return "commodity"
    if any(kw in text for kw in ["بیتکوین", "bitcoin", "اتریوم", "ethereum", "ارز دیجیتال", "crypto", "تتر", "بیت کوین", "BTC", "ETH", "رمز ارز"]):
        return "crypto"
    if any(kw in text for kw in ["طلا", "سکه", "دلار", "یورو", "ارز", "مثقال", "بهار", "امامی", "پوند", "درهم"]):
        return "gold"
    return None

def call_api(endpoint_path, params_dict):
    """فراخوانی APIهای BrsApi با هدر شبیه‌سازی‌شده مرورگر"""
    if not BRSAPI_KEY:
        print("DEBUG: BRSAPI_KEY is empty")
        return None
    try:
        url = f"{API_BASE_URL}{endpoint_path}"
        params_dict["key"] = BRSAPI_KEY

        # 🆕 اضافه کردن هدرهایی که یک مرورگر واقعی را شبیه‌سازی می‌کنند
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }

        print(f"DEBUG: Calling {url} with params: {params_dict}")
        resp = requests.get(url, params=params_dict, headers=headers, timeout=15)
        print(f"DEBUG: Response status: {resp.status_code}")

        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"DEBUG: Response body: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"DEBUG: API call failed for {endpoint_path}: {str(e)}")
        return None

def get_bourse_data(text):
    """دریافت داده‌های بورس بر اساس سوال"""
    result = []
    
    # شاخص
    if any(kw in text for kw in ["شاخص", "index"]):
        idx_type = "1"
        if "فرابورس" in text: idx_type = "2"
        if "منتخب" in text: idx_type = "3"
        data = call_api("/Tsetmc/Index.php", {"type": idx_type})
        if data:
            result.append(("شاخص بورس", data, "index"))
    
    # نماد خاص
    symbols = re.findall(r'\b(فملی|خودرو|وبملت|شپنا|شتران|اهرم|فولاد)\b', text)
    for sym in symbols[:3]:
        data = call_api("/Tsetmc/Symbol.php", {"l18": sym})
        if data:
            result.append((f"اطلاعات نماد {sym}", data, "symbol_data"))
    
    return result

def get_commodity_data(text):
    """دریافت داده‌های بورس کالا"""
    result = []
    if any(kw in text for kw in ["کامودیتی", "نفت", "مس", "طلا", "نقره"]):
        data = call_api("/Market/Commodity.php", {})
        if data:
            result.append(("کامودیتی‌ها", data, "commodity"))
    return result

def get_crypto_data(text):
    """دریافت داده‌های ارز دیجیتال"""
    result = []
    symbols = re.findall(r'\b(BTC|ETH|USDT|BNB|SOL|ADA|XRP)\b', text.upper())
    if not symbols:
        symbols = ["BTC"]
    for sym in symbols[:3]:
        data = call_api("/Market/Cryptocurrency.php", {"symbol": sym})
        if data:
            result.append((f"قیمت {sym}", data, "cryptocurrency"))
    return result

def get_gold_data(text):
    """دریافت داده‌های طلا و ارز"""
    result = []
    data = call_api("/Market/Gold_Currency_Pro.php", {"section": "gold,currency"})
    if data:
        result.append(("طلا و ارز", data, "gold_currency_pro"))
    return result

def enrich_prompt(original_prompt, combined_text):
    """دریافت داده واقعی و اضافه کردن به پرامپت"""
    market = detect_market(combined_text)
    if not market:
        return original_prompt
    
    all_data = []
    if market == "borse":
        all_data = get_bourse_data(combined_text)
    elif market == "commodity":
        all_data = get_commodity_data(combined_text)
    elif market == "crypto":
        all_data = get_crypto_data(combined_text)
    elif market == "gold":
        all_data = get_gold_data(combined_text)
    
    if not all_data:
        return original_prompt
    
    lines = ["\n\n📊 داده‌های واقعی بازار:\n"]
    for label, data, field_key in all_data:
        # انتخاب نقشه فیلد مناسب
        field_map = {}
        for fm in [BOURSE_FIELDS, COMMODITY_FIELDS, CRYPTO_FIELDS, GOLD_FIELDS]:
            if field_key in fm:
                field_map = fm[field_key]
                break
        
        lines.append(f"🔹 {label}:")
        if isinstance(data, list):
            for item in data[:5]:
                readable = ", ".join(f"{field_map.get(k, k)}: {v}" for k, v in item.items() if k in field_map and v)
                lines.append(f"  - {readable}")
        elif isinstance(data, dict):
            readable = ", ".join(f"{field_map.get(k, k)}: {v}" for k, v in data.items() if k in field_map and v)
            lines.append(f"  - {readable}")
    
    enriched = original_prompt + "\n".join(lines)
    enriched += "\n\nلطفاً با توجه به داده‌های واقعی بالا، تحلیل خود را ارائه دهید."
    return enriched

final_user_prompt = enrich_prompt(prompt, combined_text)

# ═══════════════════════════════════════════════════════════════
# ۳. مدل‌های هیئت منصفه
# ═══════════════════════════════════════════════════════════════
general_models = [
    {"id": "gpt-4o-mini", "role": "دستیار عمومی، برنامه‌نویسی و تحلیل فنی"},
    {"id": "DeepSeek-R1", "role": "تحلیل منطقی، ریاضی و امنیت سایبری"},
    {"id": "cohere/cohere-command-r-08-2024", "role": "نویسندگی خلاق و ایده‌پردازی"},
    {"id": "Mistral-small-2503", "role": "تحلیل مفهومی، فلسفه و دیدگاه‌های کلان"}
]

specialist_models = [
    {"id": "openai/gpt-4.1", "system": "شما تحلیلگر مالی و متخصص برنامه‌نویسی هستید.",
     "keywords": ["تحلیل", "قیمت", "کد", "برنامه‌نویسی", "سئو", "طراحی", "فارکس", "ارز دیجیتال", "بورس", "نمودار"]},
    {"id": "google/gemini-2.5-pro", "system": "شما محقق خبره و تولیدکننده محتوای خلاق هستید.",
     "keywords": ["مقاله", "تحقیق", "ایده", "خلاق", "محتوا", "شبکه اجتماعی", "بازاریابی"]}
]

def build_user_message(question, model_role="دستیار هوش مصنوعی"):
    return f"""⚠️ دستور: فقط به زبان فارسی پاسخ دهید.
نقش شما: {model_role}
مستقیماً پاسخ دهید.

سوال کاربر:
{question}"""

answers = []

# مدل‌های عمومی
for model in general_models:
    response = requests.post(
        "https://models.github.ai/inference/chat/completions",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
        json={"model": model["id"], "messages": [{"role": "user", "content": build_user_message(final_user_prompt, model["role"])}], "max_tokens": 600}
    )
    if response.status_code == 200:
        answers.append(f"**{model['id']}** ({model['role']}):\n{response.json()['choices'][0]['message']['content']}\n")
    else:
        answers.append(f"**{model['id']}**: خطا {response.status_code}")

# مدل‌های تخصصی
for spec in specialist_models:
    if any(keyword in combined_text for keyword in spec["keywords"]):
        response = requests.post(
            "https://models.github.ai/inference/chat/completions",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
            json={"model": spec["id"], "messages": [{"role": "system", "content": spec["system"]}, {"role": "user", "content": build_user_message(final_user_prompt, "متخصص سطح بالا")}], "max_tokens": 700}
        )
        if response.status_code == 200:
            answers.append(f"**🔹 {spec['id']}** (متخصص ویژه):\n{response.json()['choices'][0]['message']['content']}\n")
        else:
            answers.append(f"**🔹 {spec['id']}**: خطا {response.status_code}")

# ═══════════════════════════════════════════════════════════════
# ۴. قاضی و کامنت نهایی
# ═══════════════════════════════════════════════════════════════
judge_prompt = f"سوال کاربر: {prompt}\n\nپاسخ‌های متخصصان:\n" + "\n".join(answers) + "\n\nبا توجه به پاسخ‌های بالا، یک پاسخ نهایی جامع و دقیق به فارسی بنویس."

judge_response = requests.post(
    "https://models.github.ai/inference/chat/completions",
    headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
    json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": judge_prompt}], "max_tokens": 800}
)
final_answer = judge_response.json()["choices"][0]["message"]["content"] if judge_response.status_code == 200 else f"خطا: {judge_response.status_code}"

comment_body = f"## 🏛️ هیئت منصفه هوش مصنوعی\n\n### 📣 پاسخ‌ها:\n" + "\n---\n".join(answers) + f"\n---\n### ⚖️ پاسخ نهایی:\n{final_answer}"

requests.post(
    f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
    headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
    json={"body": comment_body}
)
print("✅ کامنت ثبت شد.")
