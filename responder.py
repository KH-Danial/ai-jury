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

# ۳. تحلیل عکس با مدل بینایی (در صورت وجود)
vision_answer = ""
if image_url:
    # تمیز کردن URL
    try:
        unquoted_url = unquote(image_url)
        safe_url = quote(unquoted_url, safe=':/?&=')
    except:
        safe_url = image_url

    # 🆕 دانلود تصویر و تبدیل به base64 (دور زدن خطای ۵۰۰ ناشی از URL)
    try:
        img_response = requests.get(safe_url, timeout=15)
        if img_response.status_code == 200:
            img_base64 = base64.b64encode(img_response.content).decode('utf-8')
            # حدس زدن نوع تصویر (فرض jpeg؛ در صورت نیاز می‌توان تشخیص خودکار اضافه کرد)
            data_uri = f"data:image/jpeg;base64,{img_base64}"
        else:
            data_uri = None
            vision_answer = f"**👁️ تحلیل تصویر:** خطا در دانلود تصویر (کد {img_response.status_code})\n"
    except Exception as e:
        data_uri = None
        vision_answer = f"**👁️ تحلیل تصویر:** خطا در دانلود تصویر: {str(e)[:100]}\n"

    if data_uri:
        # 🆕 پرامپت انگلیسی برای مدل بینایی (چون Llama Vision فقط انگلیسی پشتیبانی می‌کند)
        english_prompt = f"Analyze this image carefully. Describe any data, trends, charts, text, or important details you see. Provide a thorough analysis in English."
        if prompt and prompt.strip():
            english_prompt = f"The user asked this (translate if needed): '{prompt}'\n\n{english_prompt}"

        for attempt in range(3):  # تلاش مجدد با backoff
            vision_response = requests.post(
                "https://models.github.ai/inference/chat/completions",
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta/llama-3.2-11b-vision-instruct",  # 🆕 شناسه صحیح
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": english_prompt},
                                {"type": "image_url", "image_url": {"url": data_uri}}
                            ]
                        }
                    ],
                    "max_tokens": 500
                }
            )
            if vision_response.status_code == 200:
                vision_english = vision_response.json()["choices"][0]["message"]["content"]
                vision_answer = f"**👁️ تحلیل تصویر:**\n{vision_english}\n"
                break
            elif vision_response.status_code == 500:
                time.sleep(2 ** attempt)  # منتظر می‌ماند: 1s, 2s, 4s
            else:
                vision_answer = f"**👁️ تحلیل تصویر:** خطا {vision_response.status_code}\n"
                break

# ۴. مدل‌های هیئت منصفه (متخصصان متن) با پرامپت اجباری فارسی
models = [
    "gpt-4o-mini",
    "cohere/cohere-command-r-08-2024"  # 🆕 شناسه صحیح Cohere
]

# 🆕 پرامپت بسیار قوی‌تر برای وادار کردن مدل‌ها به پاسخ فارسی
forced_prompt = f"""⚠️ IMPORTANT INSTRUCTION: You MUST respond ONLY in Persian (Farsi) language.
You are NOT allowed to respond in English or any other language.
If the user's question contains non-Persian text, translate it and respond in Persian.
DO NOT mention that you can only speak English. DO NOT apologize for language limitations.
Just respond in Persian directly.

User question:
{prompt}"""

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

jury_prompt = f"سوال کاربر: {prompt}\n\nپاسخ‌های متخصصان:\n" + "\n".join(all_answers) + "\n\nبا توجه به پاسخ‌های بالا، یک پاسخ نهایی جامع و دقیق به فارسی بنویس. اگر پاسخ‌ها متناقض بودند، بهترین نظر را انتخاب کن. اگر پاسخی به انگلیسی است، آن را ترجمه کن."

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
