import os, json, requests, re

GITHUB_TOKEN = os.environ["GH_TOKEN"]

# ------------------------------------------------------------
# ۰. ابزار کمکی: دریافت داده واقعی بازار
# ------------------------------------------------------------
def fetch_market_data(symbol="bitcoin"):
    """
    دریافت داده‌های واقعی بازار برای یک نماد خاص از دو منبع رایگان.
    اولویت با CoinCap (برای پوشش بیشتر) است و در صورت شکست، CoinPaprika امتحان می‌شود.
    """
    data = {"price_usd": "N/A", "volume_24h": "N/A", "source": "Unknown"}
    
    # --- تلاش اول: CoinCap (رایگان و بدون نیاز به API Key) ---
    try:
        url = f"https://api.coincap.io/v2/assets/{symbol.strip().lower()}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json().get("data", {})
            if d:
                data["price_usd"] = d.get("priceUsd", "N/A")
                data["volume_24h"] = d.get("volumeUsd24Hr", "N/A")
                data["source"] = "CoinCap"
                return data
    except Exception as e:
        print(f"CoinCap failed for {symbol}: {e}")

    # --- تلاش دوم: CoinPaprika (برای ارزهای اصلی بهتر است) ---
    try:
        url = f"https://api.coinpaprika.com/v1/tickers/{symbol.strip().lower()}-{symbol.strip().lower()}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json().get("quotes", {}).get("USD", {})
            if d:
                data["price_usd"] = d.get("price", "N/A")
                data["volume_24h"] = d.get("volume_24h", "N/A")
                data["source"] = "CoinPaprika"
                return data
    except Exception as e:
        print(f"CoinPaprika also failed for {symbol}: {e}")
        
    return data

# ------------------------------------------------------------
# ۱. خواندن اطلاعات Issue
# ------------------------------------------------------------
event_path = os.environ["GITHUB_EVENT_PATH"]
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue_number = event["issue"]["number"]
title = event["issue"]["title"]
body = event["issue"]["body"] or ""
repo = os.environ["GITHUB_REPOSITORY"]

prompt = f"{title}\n\n{body}"

# ------------------------------------------------------------
# ۲. مهندسی پیشرفته پرامپت: تزریق داده‌های واقعی بازار
# ------------------------------------------------------------
def enrich_prompt_with_market_data(original_prompt, combined_text):
    """
    اگر سوال در مورد بازار یا ارز دیجیتال باشد، داده‌های واقعی را به پرامپت اضافه می‌کند.
    """
    # لیستی از کلمات کلیدی که نشان‌دهنده نیاز به تحلیل بازار هستند
    keywords = ["تحلیل", "بیت‌کوین", "bitcoin", "اتریوم", "ethereum", "ارز دیجیتال", "قیمت", "روند", "فارکس", "بازار مالی", "نمودار", "پیش‌بینی"]
    
    # اگر سوال مرتبط با بازار باشد
    if any(keyword in combined_text.lower() for keyword in keywords):
        # استخراج نمادهای معاملاتی (مثل BTC, ETH, DOGE) از متن
        # این یک روش ساده است و می‌توان آن را قدرتمندتر کرد
        symbols = re.findall(r'\b([A-Z]{2,10})\b', combined_text)
        # اضافه کردن بیت‌کوین و اتریوم به صورت پیش‌فرض برای تحلیل‌های کلی بازار
        if not symbols:
            symbols = ["bitcoin", "ethereum"]
        
        market_data_lines = ["\n\n📊 داده‌های واقعی بازار (لحظه‌ای):"]
        for sym in symbols[:5]: # محدود کردن به ۵ ارز برای جلوگیری از طولانی شدن پرامپت و Rate Limit
            data = fetch_market_data(sym)
            if data["source"] != "Unknown":
                market_data_lines.append(f"- {sym.upper()}: قیمت = ${data['price_usd']}, حجم ۲۴ ساعته = ${data['volume_24h']} (منبع: {data['source']})")
        
        if len(market_data_lines) > 1:
            # اگر دادهای پیدا شد، آن را به پرامپت اضافه کن و دستور تحلیل بده
            enriched_prompt = original_prompt + "\n".join(market_data_lines)
            enriched_prompt += "\n\nلطفاً با توجه به داده‌های واقعی بالا، یک تحلیل فنی و بنیادی دقیق و مختصر ارائه بده و نقاط ورود و خروج احتمالی را مشخص کن."
            return enriched_prompt
    
    # اگر سوال تحلیلی نبود، همان پرامپت اصلی را برگردان
    return original_prompt

combined_text = title + " " + body
final_user_prompt = enrich_prompt_with_market_data(prompt, combined_text)

# ------------------------------------------------------------
# ۳. تعریف مدل‌های عمومی (همیشه فعال)
# ------------------------------------------------------------
general_models = [
    {
        "id": "gpt-4o-mini",
        "role": "دستیار عمومی، برنامه‌نویسی و تحلیل فنی"
    },
    {
        "id": "DeepSeek-R1",
        "role": "تحلیل منطقی، ریاضی و امنیت سایبری"
    },
    {
        "id": "cohere/cohere-command-r-08-2024",
        "role": "نویسندگی خلاق، تولید محتوا و ایده‌پردازی"
    },
    {
        "id": "Mistral-small-2503",
        "role": "تحلیل مفهومی، فلسفه و دیدگاه‌های کلان"
    }
]

# ------------------------------------------------------------
# ۴. تعریف مدل‌های تخصصی (فقط در حوزه مربوطه)
# ------------------------------------------------------------
specialist_models = [
    # (بدون تغییر باقی می‌ماند)
]

# ------------------------------------------------------------
# ۵. جمع‌آوری پاسخ‌ها
# ------------------------------------------------------------
answers = []

def build_user_message(question, model_role="دستیار هوش مصنوعی"):
    return f"""⚠️ دستور: شما فقط باید به زبان فارسی پاسخ دهید. حق استفاده از هیچ زبان دیگری را ندارید.
نقش شما: {model_role}
اگر سوال کاربر حاوی متنی غیرفارسی است، آن را ترجمه کرده و پاسخ خود را کاملاً فارسی بنویسید.
هرگز به «فارسی نبودن» یا «محدودیت زبان» اشاره نکنید. مستقیماً پاسخ دهید.

سوال کاربر:
{question}"""

for model in general_models:
    # ... (کد باقی‌مانده بدون تغییر باقی می‌ماند)
    response = requests.post(
        "https://models.github.ai/inference/chat/completions",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": model["id"],
            "messages": [
                {"role": "user", "content": build_user_message(final_user_prompt, model["role"])}
            ],
            "max_tokens": 600
        }
    )
    if response.status_code == 200:
        answer = response.json()["choices"][0]["message"]["content"]
        answers.append(f"**{model['id']}** ({model['role']}):\n{answer}\n")
    else:
        answers.append(f"**{model['id']}** (خطا {response.status_code})")

# (ب) مدل‌های تخصصی را فقط در صورت مرتبط بودن حوزه اضافه کن
for spec in specialist_models:
    # چک کن حداقل یکی از کلمات کلیدی در متن وجود داشته باشد
    if any(keyword in combined_text for keyword in spec["keywords"]):
        response = requests.post(
            "https://models.github.ai/inference/chat/completions",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "model": spec["id"],
                "messages": [
                    {"role": "system", "content": spec["system"]},
                    {"role": "user", "content": build_user_message(final_user_prompt, "متخصص سطح بالا")}
                ],
                "max_tokens": 700
            }
        )
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            answers.append(f"**🔹 {spec['id']}** (متخصص ویژه):\n{answer}\n")
        else:
            answers.append(f"**🔹 {spec['id']}** (خطا {response.status_code})")

# ------------------------------------------------------------
# ۶. مدل قاضی – جمع‌بندی نهایی
# ------------------------------------------------------------
judge_prompt = f"سوال کاربر: {prompt}\n\nپاسخ‌های متخصصان:\n" + "\n".join(answers) + "\n\nبا توجه به پاسخ‌های بالا، یک پاسخ نهایی جامع و دقیق به فارسی بنویس. اگر پاسخ‌ها متناقض بودند، بهترین نظر را انتخاب کن."

judge_response = requests.post(
    "https://models.github.ai/inference/chat/completions",
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": judge_prompt}],
        "max_tokens": 800
    }
)

if judge_response.status_code == 200:
    final_answer = judge_response.json()["choices"][0]["message"]["content"]
else:
    final_answer = f"⚠️ خطا در جمع‌بندی نهایی: {judge_response.status_code}"

# ------------------------------------------------------------
# ۷. ارسال کامنت نهایی
# ------------------------------------------------------------
comment_parts = [
    "## 🏛️ هیئت منصفه هوش مصنوعی\n",
    "### 👥 متخصصان دائمی (عمومی):\n",
    *(f"- {m['id']} ({m['role']})\n" for m in general_models),
    "\n### 📣 پاسخ‌ها:\n",
    "\n---\n".join(answers),
    f"\n---\n### ⚖️ پاسخ نهایی (قاضی - GPT-4o mini):\n{final_answer}"
]

comment_body = "".join(comment_parts)

comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
post = requests.post(
    comment_url,
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    },
    json={"body": comment_body}
)

if post.status_code == 201:
    print("✅ کامنت ثبت شد.")
else:
    print(f"❌ خطا: {post.status_code} {post.text[:200]}")