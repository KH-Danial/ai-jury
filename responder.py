import os, json, requests, re, base64, time
from urllib.parse import quote, unquote

GITHUB_TOKEN = os.environ["GH_TOKEN"]

# ۱. خواندن اطلاعات Issue
event_path = os.environ["GITHUB_EVENT_PATH"]
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue_number = event["issue"]["number"]
title = event["issue"]["title"]
body = event["issue"]["body"] or ""
repo = os.environ["GITHUB_REPOSITORY"]

# ۲. استخراج لینک عکس (اگر وجود داشته باشد) و حذف آن از متن
image_url = None
match = re.search(r'image:\s*(https?://[^\s]+)', body)
if match:
    image_url = match.group(1)
    body = re.sub(r'image:\s*https?://[^\s]+\n?', '', body).strip()

prompt = f"{title}\n\n{body}"

# ۳. تحلیل عکس با مدل بینایی (gpt-4o-mini) و ترجمه آن به فارسی
vision_answer = ""
if image_url:
    # تمیز کردن URL
    try:
        unquoted_url = unquote(image_url)
        safe_url = quote(unquoted_url, safe=':/?&=')
    except:
        safe_url = image_url

    # دانلود تصویر و تبدیل به base64
    try:
        img_response = requests.get(safe_url, timeout=15)
        if img_response.status_code == 200:
            img_base64 = base64.b64encode(img_response.content).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{img_base64}"
        else:
            data_uri = None
            vision_answer = f"**👁️ تحلیل تصویر:** خطا در دانلود تصویر (کد {img_response.status_code})\n"
    except Exception as e:
        data_uri = None
        vision_answer = f"**👁️ تحلیل تصویر:** خطا در دانلود تصویر: {str(e)[:100]}\n"

    if data_uri:
        # پرامپت انگلیسی برای استخراج داده‌های دقیق
        english_prompt = "Analyze this image carefully. Describe all text, numbers, axes labels, trends, and any data points you can see. Be as precise as possible, citing exact numbers and labels in your description. Provide your analysis in English."
        if prompt and prompt.strip():
            english_prompt = f"The user asked this (translate if needed): '{prompt}'\n\n{english_prompt}"

        # تلاش برای دریافت تحلیل از gpt-4o-mini
        raw_vision_result = ""
        success = False
        for attempt in range(3):
            vision_response = requests.post(
                "https://models.github.ai/inference/chat/completions",
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # <--- تغییر اصلی اینجاست
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": english_prompt},
                                {"type": "image_url", "image_url": {"url": data_uri}}
                            ]
                        }
                    ],
                    "max_tokens": 600
                }
            )
            if vision_response.status_code == 200:
                raw_vision_result = vision_response.json()["choices"][0]["message"]["content"]
                success = True
                break
            elif vision_response.status_code == 500:
                time.sleep(2 ** attempt)
            else:
                vision_answer = f"**👁️ تحلیل تصویر:** خطا {vision_response.status_code}\n"
                break

        if success and raw_vision_result:
            # ترجمه خودکار تحلیل انگلیسی به فارسی
            translate_prompt = f"""دستور: شما باید فقط به زبان فارسی پاسخ دهید. متن انگلیسی زیر را دقیقاً به فارسی ترجمه کن. تمام اعداد، تاریخ‌ها و جزئیات فنی باید عیناً حفظ شوند. فقط ترجمه را بنویس و هیچ توضیح اضافه نده.

English Text:
{raw_vision_result}"""

            translate_response = requests.post(
                "https://models.github.ai/inference/chat/completions",
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": translate_prompt}],
                    "max_tokens": 600
                }
            )
            if translate_response.status_code == 200:
                persian_vision = translate_response.json()["choices"][0]["message"]["content"]
                vision_answer = f"**👁️ تحلیل تصویر:**\n{persian_vision}\n"
            else:
                vision_answer = f"**👁️ تحلیل تصویر (ترجمه خودکار):**\n{raw_vision_result}\n"
    else:
        pass

# ۴. مدل‌های هیئت منصفه (متخصصان متن)
models = [
    "gpt-4o-mini",
    "cohere/cohere-command-r-08-2024"
]

# تزریق تحلیل فارسی تصویر به پرامپت متخصصان
base_prompt = f"سوال کاربر: {prompt}"
if vision_answer:
    vision_text = vision_answer.replace("**👁️ تحلیل تصویر:**\n", "").replace("\n", " ")
    base_prompt = f"تحلیل دقیق تصویر توسط یک مدل بینایی:\n{vision_text}\n\n{base_prompt}"

forced_prompt = f"""⚠️ دستور: شما باید فقط به زبان فارسی پاسخ دهید. حق استفاده از هیچ زبان دیگری را ندارید.
اگر سوال کاربر یا تحلیل تصویر حاوی متنی غیرفارسی است، آن را ترجمه کرده و پاسخ خود را کاملاً فارسی بنویسید.
به هیچ عنوان به «فارسی نبودن» یا «توانایی زبان» اشاره نکنید. مستقیماً پاسخ دهید.

{base_prompt}"""

answers = []

for model in models:
    response = requests.post(
        "https://models.github.ai/inference/chat/completions",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": forced_prompt}],
            "max_tokens": 600
        }
    )
    if response.status_code == 200:
        answer = response.json()["choices"][0]["message"]["content"]
        answers.append(f"**{model}:**\n{answer}\n")
    else:
        answers.append(f"**{model}:** خطا {response.status_code}")

# ۵. مدل قاضی برای جمع‌بندی
all_answers = []
if vision_answer:
    all_answers.append(vision_answer)
all_answers.extend(answers)

jury_prompt = f"""سوال کاربر: {prompt}

تحلیل تصویر (که توسط یک مدل بینایی دقیق انجام شده و معتبر است):
{vision_answer if vision_answer else "هیچ تصویری ارائه نشده است."}

پاسخ‌های متخصصان:
{chr(10).join(answers)}

با توجه به اطلاعات بالا، یک پاسخ نهایی جامع و دقیق به فارسی بنویس.
دستورالعمل‌های حیاتی:
۱. تحلیل تصویر (اگر موجود باشد) معتبرترین منبع اطلاعات است. تمام اعداد، تاریخ‌ها و روندهای ذکر شده در آن را عیناً در پاسخ خود بیاور.
۲. اگر پاسخ متخصصان متناقض با تحلیل تصویر بود، تحلیل تصویر را ملاک قرار بده.
۳. از افزودن هیچ عدد، تاریخ یا داده‌ای که در منابع بالا (خصوصاً تحلیل تصویر) وجود ندارد، خودداری کن.
۴. پاسخ باید کاملاً فارسی و روان باشد."""

final_response = requests.post(
    "https://models.github.ai/inference/chat/completions",
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": jury_prompt}],
        "max_tokens": 800
    }
)

if final_response.status_code == 200:
    final_answer = final_response.json()["choices"][0]["message"]["content"]
else:
    final_answer = f"⚠️ خطا در جمع‌بندی: {final_response.status_code}"

# ۶. ارسال کامنت نهایی
comment_parts = ["## 🏛️ هیئت منصفه هوش مصنوعی\n"]
if vision_answer:
    comment_parts.append(f"### 👁️ تحلیل تصویر:\n{vision_answer}\n---\n")
comment_parts.append("### 📣 پاسخ‌های متخصصان:\n")
comment_parts.append("\n---\n".join(answers))
comment_parts.append(f"\n---\n### ⚖️ پاسخ نهایی (قاضی):\n{final_answer}")

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
    print("✅ کامنت هیئت منصفه ثبت شد.")
else:
    print(f"❌ خطا: {post.status_code} {post.text[:200]}")
