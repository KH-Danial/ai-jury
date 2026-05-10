import os, json, requests

GITHUB_TOKEN = os.environ["GH_TOKEN"]

event_path = os.environ["GITHUB_EVENT_PATH"]
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue_number = event["issue"]["number"]
title = event["issue"]["title"]
body = event["issue"]["body"] or ""
repo = os.environ["GITHUB_REPOSITORY"]

prompt = f"{title}\n\n{body}"

response = requests.post(
    "https://models.github.ai/inference/chat/completions",
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800
    }
)

if response.status_code == 200:
    answer = response.json()["choices"][0]["message"]["content"]
else:
    answer = f"⚠️ خطا: {response.status_code}\n{response.text[:300]}"

comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
post = requests.post(
    comment_url,
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    },
    json={"body": f"**🤖 پاسخ هوش مصنوعی:**\n\n{answer}"}
)

if post.status_code == 201:
    print("✅ کامنت ثبت شد.")
else:
    print(f"❌ خطا در ثبت کامنت: {post.status_code} {post.text[:200]}")
