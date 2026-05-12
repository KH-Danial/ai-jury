import os, json, requests, re

GITHUB_TOKEN = os.environ["GH_TOKEN"]

# ۱. خواندن اطلاعات Issue
event_path = os.environ["GITHUB_EVENT_PATH"]
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue_number = event["issue"]["number"]
title = event["issue"]["title"]
body = event["issue"]["body"] or ""
repo = os.environ["GITHUB_REPOSITORY"]

# ۲. استخراج لینک عکس (اگر وجود داشته باشد)
image_url = None
match = re.search(r'image:\s*(https?://[^\s]+)', body)
if match:
    image_url = match.group(1)
    # حذف خط image: از متن برای جلوگیری از گیج شدن مدل‌ها
    body = re.sub(r'image:\s*https?://[^\s]+\n?', '', body).strip()

prompt = f"{title}\n\n{body}"

# ۳. تحلیل عکس با مدل بینایی (اگر عکس وجود داشته باشد)
vision_answer = ""
if image_url:
    vision_response = requests.post(
        "https://models.github.ai/inference/chat/completions",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": "Llama-3.2-11B-Vision-Instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt if prompt else "این تصویر را تحلیل کن و هر داده، روند یا نکته مهمی که در آن می‌بینی را توضیح بده."},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": 500
        }
    )
    if vision_response.status_code == 200:
        vision_answer = f"**👁️ تحلیل تصویر (Llama-3.2-Vision):**\n{vision_response.json()['choices'][0]['message']['content']}\n"
    else:
        vision_answer = f"**👁️ تحلیل تصویر:** خطا {vision_response.status_code}\n"

# ۴. مدل‌های هیئت منصفه (متخصصان متن)
models = [
    "gpt-4o-mini",
    "cohere/cohere-command-r-08-2024"
]

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
            "messages": [{"role": "user", "content": prompt}],
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

jury_prompt = f"سوال کاربر: {prompt}\n\nپاسخ‌های متخصصان:\n" + "\n".join(all_answers) + "\n\nبا توجه به پاسخ‌های بالا، یک پاسخ نهایی جامع و دقیق به فارسی بنویس."

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
