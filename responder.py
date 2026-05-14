import os, json, requests

GITHUB_TOKEN = os.environ["GH_TOKEN"]

# ۱. خواندن اطلاعات Issue
event_path = os.environ["GITHUB_EVENT_PATH"]
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue_number = event["issue"]["number"]
title = event["issue"]["title"]
body = event["issue"]["body"] or ""
repo = os.environ["GITHUB_REPOSITORY"]

prompt = f"{title}\n\n{body}"

# ۲. مدل‌های هیئت منصفه - ۴ متخصص پایدار و تست‌شده
models = [
    "gpt-4o-mini",                        # ChatGPT
    "DeepSeek-R1",                        # DeepSeek
    "cohere/cohere-command-r-08-2024",    # Cohere (جایگزین Grok)
    "Mistral-small-2503"                  # Mistral (جایگزین Gemini)
]

forced_prompt = f"""⚠️ دستور: شما باید فقط به زبان فارسی پاسخ دهید. حق استفاده از هیچ زبان دیگری را ندارید.
اگر سوال کاربر حاوی متنی غیرفارسی است، آن را ترجمه کرده و پاسخ خود را کاملاً فارسی بنویسید.
به هیچ عنوان به «فارسی نبودن» یا «توانایی زبان» اشاره نکنید. مستقیماً پاسخ دهید.

سوال کاربر:
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

# ۳. مدل قاضی برای جمع‌بندی
jury_prompt = f"سوال کاربر: {prompt}\n\nپاسخ‌های متخصصان:\n" + "\n".join(answers) + "\n\nبا توجه به پاسخ‌های بالا، یک پاسخ نهایی جامع و دقیق به فارسی بنویس. اگر پاسخ‌ها متناقض بودند، بهترین نظر را انتخاب کن."

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

# ۴. ارسال کامنت نهایی
comment_body = f"## 🏛️ هیئت منصفه هوش مصنوعی\n\n### 👥 ۴ متخصص:\n- ChatGPT (GPT-4o mini)\n- DeepSeek R1\n- Cohere Command R\n- Mistral Small\n\n### 📣 پاسخ‌های متخصصان:\n" + "\n---\n".join(answers) + f"\n---\n### ⚖️ پاسخ نهایی (قاضی - GPT-4o mini):\n{final_answer}"

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