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
# ۲. تشخیص بازار و فراخوانی API (با Debug کامل)
# ═══════════════════════════════════════════════════════════════

# آرایه‌ای برای جمع‌آوری پیام‌های debug
debug_logs = []

def log(msg):
    """ثبت پیام debug برای نمایش در کامنت نهایی"""
    debug_logs.append(msg)
    print(f"DEBUG: {msg}")

def detect_market(text):
    if any(kw in text for kw in ["بورس", "سهام", "شاخص", "فرابورس", "فملی", "اهرم", "آپشن"]):
        return "borse"
    if any(kw in text for kw in ["کالا", "نفت", "مس", "گواهی", "سیمان", "پتروشیمی"]):
        return "commodity"
    if any(kw in text for kw in ["بیتکوین", "bitcoin", "اتریوم", "crypto", "BTC", "ETH", "رمز ارز"]):
        return "crypto"
    if any(kw in text for kw in ["طلا", "سکه", "دلار", "یورو", "مثقال", "درهم"]):
        return "gold"
    return None

def call_api(endpoint_name, extra_params=None):
    """
    فراخوانی APIهای BrsApi فقط با پارامترهای معتبر.
    """
    if not BRSAPI_KEY:
        log("❌ BRSAPI_KEY خالی است — Secret در گیت‌هاب تنظیم نشده!")
        return None

    # پیدا کردن اطلاعات endpoint
    all_endpoints = {}
    all_endpoints.update(BOURSE_ENDPOINTS)
    all_endpoints.update(COMMODITY_ENDPOINTS)
    all_endpoints.update(CRYPTO_ENDPOINTS)
    all_endpoints.update(GOLD_ENDPOINTS)

    endpoint_info = all_endpoints.get(endpoint_name)
    if not endpoint_info:
        log(f"❌ Endpoint '{endpoint_name}' پیدا نشد")
        return None

    # ساخت پارامترها فقط بر اساس params مجاز
    final_params = {"key": BRSAPI_KEY}
    valid_params = endpoint_info.get("params", [])

    if extra_params:
        for k, v in extra_params.items():
            if k in valid_params:
                final_params[k] = v
            else:
                log(f"⚠️ پارامتر نامعتبر '{k}' برای '{endpoint_name}' نادیده گرفته شد")

    try:
        url = f"{API_BASE_URL}{endpoint_info['path']}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }

        log(f"📡 فراخوانی: {url}")
        log(f"📋 پارامترها: {final_params}")

        resp = requests.get(url, params=final_params, headers=headers, timeout=15)
        log(f"📊 کد وضعیت: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            log(f"✅ داده دریافت شد (طول: {len(str(data))} کاراکتر)")
            return data
        else:
            log(f"❌ خطا: {resp.status_code} — {resp.text[:150]}")
            return None
    except Exception as e:
        log(f"❌ استثنا: {str(e)[:200]}")
        return None

def get_bourse_data(text):
    result = []
    if any(kw in text for kw in ["شاخص", "index"]):
        idx_type = "1"
        if "فرابورس" in text: idx_type = "2"
        if "منتخب" in text: idx_type = "3"
        data = call_api("index", {"type": idx_type})
        if data:
            result.append(("شاخص بورس", data, "index"))
    symbols = re.findall(r'\b(فملی|خودرو|وبملت|شپنا|شتران|اهرم|فولاد)\b', text)
    for sym in symbols[:3]:
        data = call_api("symbol_data", {"l18": sym})
        if data:
            result.append((f"اطلاعات نماد {sym}", data, "symbol_data"))
    return result

def get_commodity_data(text):
    result = []
    if any(kw in text for kw in ["کامودیتی", "نفت", "مس", "طلا", "نقره"]):
        data = call_api("commodity", {})
        if data:
            result.append(("کامودیتی‌ها", data, "commodity"))
    return result

def get_crypto_data(text):
    result = []
    symbols = re.findall(r'\b(BTC|ETH|USDT|BNB|SOL|ADA|XRP)\b', text.upper())
    if not symbols:
        symbols = ["BTC"]
    for sym in symbols[:3]:
        data = call_api("cryptocurrency", {"symbol": sym})
        if data:
            result.append((f"قیمت {sym}", data, "cryptocurrency"))
    return result

def get_gold_data(text):
    result = []
    # 🆕 ارسال section=gold,currency برای دریافت فقط طلا و ارز (نه رمزارز)
    data = call_api("gold_currency_pro", {"section": "gold,currency"})
    if data:
        result.append(("طلا و ارز", data, "gold_currency_pro"))
    return result

def enrich_prompt(original_prompt, combined_text):
    market = detect_market(combined_text)
    if not market:
        log("🔍 بازار تشخیص داده نشد — پرامپت بدون داده باقی ماند")
        return original_prompt
    
    log(f"🔍 بازار تشخیص داده شده: {market}")
    
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
        log("⚠️ هیچ داده‌ای از API دریافت نشد — پرامپت غنی‌سازی نشد")
        return original_prompt
    
    log(f"✅ {len(all_data)} دسته داده دریافت شد")
    
    lines = ["\n\n📊 داده‌های واقعی بازار:\n"]
    for label, data, field_key in all_data:
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
    {"id": "gpt-4o-mini", "role": "دستیار عمومی و تحلیل فنی"},
    {"id": "DeepSeek-R1", "role": "تحلیل منطقی و ریاضی"},
    {"id": "cohere/cohere-command-r-08-2024", "role": "نویسندگی خلاق"},
    {"id": "Mistral-small-2503", "role": "تحلیل مفهومی و فلسفی"}
]

def build_user_message(question, model_role="دستیار هوش مصنوعی"):
    return f"""⚠️ دستور: فقط به زبان فارسی پاسخ دهید.
نقش شما: {model_role}
مستقیماً پاسخ دهید.

سوال کاربر:
{question}"""

answers = []

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

# ═══════════════════════════════════════════════════════════════
# ۴. قاضی و کامنت نهایی (همراه با Debug Log)
# ═══════════════════════════════════════════════════════════════
judge_prompt = f"سوال کاربر: {prompt}\n\nپاسخ‌های متخصصان:\n" + "\n".join(answers) + "\n\nبا توجه به پاسخ‌های بالا، یک پاسخ نهایی جامع و دقیق به فارسی بنویس."

judge_response = requests.post(
    "https://models.github.ai/inference/chat/completions",
    headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
    json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": judge_prompt}], "max_tokens": 800}
)
final_answer = judge_response.json()["choices"][0]["message"]["content"] if judge_response.status_code == 200 else f"خطا: {judge_response.status_code}"

# 🆕 اضافه کردن Debug Log به کامنت
debug_section = ""
if debug_logs:
    debug_section = "\n\n---\n### 🔍 گزارش فنی (Debug):\n" + "\n".join(f"- {l}" for l in debug_logs)

comment_body = f"## 🏛️ هیئت منصفه هوش مصنوعی\n\n### 📣 پاسخ‌ها:\n" + "\n---\n".join(answers) + f"\n---\n### ⚖️ پاسخ نهایی:\n{final_answer}{debug_section}"

requests.post(
    f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
    headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
    json={"body": comment_body}
)
print("✅ کامنت ثبت شد.")
