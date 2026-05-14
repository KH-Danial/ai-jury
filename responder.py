import os, json, requests, time

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

# ۲. ۵ مدل پایدار با تنظیمات بهینه
models = [
    {
        "id": "gpt-4o-mini",
        "role": "دستیار عمومی، برنامه‌نویسی و تحلیل فنی",
        "delay": 0,
        "max_tokens": 2000
    },
    {
        "id": "deepseek/deepseek-r1",
        "role": "تحلیل منطقی، ریاضی و امنیت سایبری",
        "delay": 4,
        "retry_on_429": True,
        "max_tokens": 2000
    },
    {
        "id": "Mistral-small-2503",
        "role": "تحلیل مفهومی، فلسفه و دیدگاه‌های کلان",
        "delay": 0,
        "max_tokens": 2000
    },
    {
        "id": "meta/llama-3.3-70b-instruct",
        "role": "استدلال پیشرفته و تحقیق عمیق",
        "delay": 0,
        "max_tokens": 2000
    },
    {
        "id": "phi-4",
        "role": "استدلال ساختاریافته و حل مسئله",
        "delay": 0,
        "max_tokens": 2000
    }
]

forced_prompt = f"""⚠️ دستور: شما باید فقط به زبان فارسی پاسخ دهید. حق استفاده از هیچ زبان دیگری را ندارید.
اگر سوال کاربر حاوی متنی غیرفارسی است، آن را ترجمه کرده و پاسخ خود را کاملاً فارسی بنویسید.
به هیچ عنوان به «فارسی نبودن» یا «توانایی زبان» اشاره نکنید.
پاسخی کامل، جامع و بدون وقفه ارائه دهید و از نصفه رها کردن پاسخ خودداری کنید.

سوال کاربر:
{prompt}"""

answers = []

for model in models:
    if model.get("delay", 0) > 0:
        time.sleep(model["delay"])
    
    attempt = 0
    max_attempts = 3 if model.get("retry_on_429") else 1
    success = False
    
    while attempt < max_attempts and not success:
        attempt += 1
        try:
            response = requests.post(
                "https://models.github.ai/inference/chat/completions",
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model["id"],
                    "messages": [{"role": "user", "content": forced_prompt}],
                    "max_tokens": model.get("max_tokens", 800)
                },
                timeout=90
            )
            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"]
                answers.append(f"**✅ {model['id']}** ({model['role']}):\n{answer}\n")
                success = True
            elif response.status_code == 429:
                if attempt < max_attempts:
                    wait_time = 4 * (2 ** (attempt - 1))
                    time.sleep(wait_time)
                else:
                    # 🆕 توضیح فارسی برای کاربر
                    answers.append(
                        f"**⚠️ {model['id']}** (خطای ۴۲۹)\n"
                        f"> این خطا فنی نیست — تعداد درخواست‌های مجاز روزانه این مدل به پایان رسیده است.\n"
                        f"> لطفاً ۲۴ ساعت بعد دوباره تلاش کنید یا از مدل دیگری استفاده نمایید.\n"
                    )
                    success = True
            else:
                answers.append(f"**❌ {model['id']}** (خطا {response.status_code})\n")
                success = True
        except Exception as e:
            answers.append(f"**❌ {model['id']}** (استثنا: {str(e)[:100]})\n")
            success = True

# ۳. مدل قاضی برای جمع‌بندی
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
        "max_tokens": 1000
    },
    timeout=90
)

if judge_response.status_code == 200:
    final_answer = judge_response.json()["choices"][0]["message"]["content"]
else:
    final_answer = f"⚠️ خطا در جمع‌بندی نهایی: {judge_response.status_code}"

# ۴. ارسال کامنت نهایی
comment_body = f"## 🏛️ هیئت منصفه هوش مصنوعی\n\n### 👥 ۵ متخصص:\n- GPT-4o mini\n- DeepSeek R1 (غیرفعال موقت)\n- Mistral Small\n- Llama 3.3 70B\n- Phi-4\n\n### 📣 پاسخ‌های متخصصان:\n" + "\n---\n".join(answers) + f"\n---\n### ⚖️ پاسخ نهایی (قاضی - GPT-4o mini):\n{final_answer}"

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