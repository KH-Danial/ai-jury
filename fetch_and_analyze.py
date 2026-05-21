import requests
import json
import os
import sys
import traceback
import time
from datetime import datetime, timezone

# --- تنظیمات ---
API_BASE_URL = "https://api.bitbarg.com/api/v1/docs/prices"
HISTORY_FILE = "price_history.json"
README_FILE = "README.md"
REPORT_FILE = "market_report.json"
LATEST_FILE = "latest.json"
DASHBOARD_FILE = "index.html"
TOP_N = 5
VOLATILITY_THRESHOLD = 2.0
MAX_RETRIES = 3

def get_price(item):
    for field in ["currency_price", "quote", "price"]:
        val = item.get(field)
        if val is not None:
            return float(val)
    return 0.0

def fetch_page_with_retry(page):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"📥 دریافت صفحه {page} (تلاش {attempt}/{MAX_RETRIES})...")
            resp = requests.get(
                API_BASE_URL,
                params={"pageSize": 100, "page": page, "base": "usdt"},
                headers={"Accept": "application/json", "User-Agent": "GitHub-Action"},
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                print(f"⚠️ خطا از API: {data.get('message')}")
                if attempt < MAX_RETRIES:
                    time.sleep(5 * attempt)
                    continue
                return None
            return data
        except requests.exceptions.Timeout as e:
            print(f"⏰ timeout در صفحه {page}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(5 * attempt)
                continue
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ خطا در دریافت صفحه {page}: {e}")
            if attempt < MAX_RETRIES:
                print(f"🔄 تلاش مجدد در {5*attempt} ثانیه...")
                time.sleep(5 * attempt)
                continue
            traceback.print_exc()
            return None
    return None

def fetch_all_prices():
    all_items = []
    page = 1
    while True:
        data = fetch_page_with_retry(page)
        if data is None:
            print(f"⚠️ دریافت صفحه {page} ناموفق بود. با داده‌های موجود ادامه می‌دهیم.")
            break
        items = data["result"]["items"]
        if not items:
            break
        all_items.extend(items)
        print(f"✅ {len(items)} آیتم از صفحه {page} دریافت شد")
        meta = data["result"]["meta"]["paginateHelper"]
        if meta["currentPage"] >= meta["lastPage"]:
            break
        page += 1
    return all_items

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def calculate_changes(current, previous):
    changes = {}
    if not current:
        return changes
    prev_dict = {}
    if previous:
        prev_dict = {it["slug"]: get_price(it) for it in previous if "slug" in it}
    for item in current:
        slug = item.get("slug")
        if not slug:
            continue
        cur_price = get_price(item)
        prev_price = prev_dict.get(slug)
        if prev_price and prev_price > 0:
            chg = ((cur_price - prev_price) / prev_price) * 100
        else:
            chg = 0.0
        changes[slug] = {
            "name": slug,
            "current_price": cur_price,
            "previous_price": prev_price,
            "change_percent": round(chg, 4)
        }
    return changes

def detect_volatility(changes, threshold=VOLATILITY_THRESHOLD):
    volatile = [c for c in changes.values() if abs(c["change_percent"]) >= threshold]
    volatile.sort(key=lambda x: abs(x["change_percent"]), reverse=True)
    return volatile

def write_readme(top_gainers, top_losers, volatile, changes, timestamp):
    try:
        lines = []
        lines.append("# 📊 Bitbarg Market Monitor (گزارش زنده)")
        lines.append("")
        lines.append(f"**🕒 آخرین به‌روزرسانی:** `{timestamp}`")
        lines.append(f"**📈 تعداد ارزهای ردیابی‌شده:** `{len(changes)}`")
        lines.append("")
        has_changes = any(c["change_percent"] != 0.0 for c in changes.values())
        if not has_changes:
            lines.append("> ⚠️ این اولین اجراست. درصد تغییرات از اجرای بعدی محاسبه می‌شود.")
            lines.append("")
        lines.append("---")
        lines.append("## 🔥 بیشترین رشدها")
        lines.append("")
        if top_gainers:
            for i, c in enumerate(top_gainers, 1):
                lines.append(f"{i}. **{c['name']}**: %{c['change_percent']:+.2f}")
        else:
            lines.append("داده‌ای موجود نیست")
        lines.append("")
        lines.append("## ❄️ بیشترین افت‌ها")
        lines.append("")
        if top_losers:
            for i, c in enumerate(top_losers, 1):
                lines.append(f"{i}. **{c['name']}**: %{c['change_percent']:+.2f}")
        else:
            lines.append("داده‌ای موجود نیست")
        lines.append("")
        lines.append(f"## ⚡ نوسان‌های بالا (تغییر بیش از {VOLATILITY_THRESHOLD}٪)")
        lines.append("")
        if volatile:
            for i, c in enumerate(volatile[:10], 1):
                emoji = "🔺" if c["change_percent"] > 0 else "🔻"
                lines.append(f"{i}. **{c['name']}**: %{c['change_percent']:+.2f} {emoji}")
        else:
            lines.append("نوسان شدیدی مشاهده نشد.")
        lines.append("")
        lines.append("---")
        lines.append("## 📋 ۲۰ ارز برتر")
        lines.append("")
        lines.append("| رتبه | ارز | قیمت (USDT) | تغییر |")
        lines.append("|------|-----|------------|--------|")
        sorted_changes = sorted(changes.values(), key=lambda x: x["change_percent"], reverse=True)
        for i, c in enumerate(sorted_changes[:20], 1):
            emoji = "🟢" if c["change_percent"] > 0 else ("🔴" if c["change_percent"] < 0 else "⚪")
            lines.append(f"| {i} | {c['name']} | {c['current_price']:,.2f} | {c['change_percent']:+.2f}% {emoji} |")
        lines.append("")
        lines.append("*🤖 خودکار توسط GitHub Actions*")
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("✅ README ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در نوشتن README: {e}")
        traceback.print_exc()

def write_json_files(top_gainers, top_losers, volatile, changes, timestamp):
    try:
        report = {
            "timestamp": timestamp,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "volatile": volatile[:20],
            "all_changes": changes
        }
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        latest = {
            "timestamp": timestamp,
            "total_coins": len(changes),
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "volatile": volatile[:20],
            "all": changes
        }
        with open(LATEST_FILE, "w", encoding="utf-8") as f:
            json.dump(latest, f, indent=2, ensure_ascii=False)
        print("✅ فایل‌های JSON ذخیره شدند")
    except Exception as e:
        print(f"❌ خطا در نوشتن JSON: {e}")
        traceback.print_exc()

def write_dashboard():
    html = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>داشبورد بازار Bitbarg</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body { font-family: Tahoma; max-width: 900px; margin: auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .chart-container { background: white; padding: 20px; border-radius: 10px; margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; border-bottom: 1px solid #ddd; }
        th { background: #4CAF50; color: white; }
        .up { color: green; } .down { color: red; }
    </style>
</head>
<body>
    <h1>📊 داشبورد زنده بازار Bitbarg</h1>
    <p>🕒 <span id="ts"></span></p>
    <div class="chart-container"><h2>📈 ۱۰ ارز با بیشترین تغییر</h2><canvas id="chart"></canvas></div>
    <div class="chart-container"><h2>⚡ نوسان‌های بالا</h2><table id="voltbl"><thead><tr><th>ارز</th><th>قیمت</th><th>تغییر</th></tr></thead><tbody></tbody></table></div>
    <script>
        fetch('latest.json').then(r=>r.json()).then(d=>{
            document.getElementById('ts').textContent = d.timestamp;
            const all = Object.values(d.all).sort((a,b)=>Math.abs(b.change_percent)-Math.abs(a.change_percent)).slice(0,10);
            new Chart(document.getElementById('chart'),{
                type:'bar', data:{ labels: all.map(c=>c.name), datasets:[{ label:'% تغییر', data: all.map(c=>c.change_percent), backgroundColor: all.map(v=>v.change_percent>=0?'rgba(75,192,192,0.7)':'rgba(255,99,132,0.7)') }] },
                options:{ responsive:true, scales:{ y:{ beginAtZero:true } } }
            });
            d.volatile.forEach(c=>{ let tr=document.createElement('tr'); tr.innerHTML=`<td>${c.name}</td><td>${c.current_price.toFixed(2)}</td><td class="${c.change_percent>=0?'up':'down'}">%${c.change_percent.toFixed(2)}</td>`; document.querySelector('#voltbl tbody').appendChild(tr); });
        });
    </script>
</body>
</html>"""
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ داشبورد ذخیره شد")

def main():
    print("🚀 شروع تحلیل...")
    try:
        current_prices = fetch_all_prices()
    except Exception as e:
        print(f"❌ دریافت قیمت‌ها شکست خورد: {e}")
        traceback.print_exc()
        current_prices = []

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not current_prices:
        write_readme([], [], [], {}, timestamp)
        write_json_files([], [], [], {}, timestamp)
        write_dashboard()
        print("⚠️ به دلیل عدم دریافت داده، فایل‌ها با محتوای خطا ساخته شدند.")
        sys.exit(1)

    history = load_history()
    previous = history[-1]["items"] if history else []
    changes = calculate_changes(current_prices, previous)

    if not changes:
        write_readme([], [], [], {}, timestamp)
        write_json_files([], [], [], {}, timestamp)
        write_dashboard()
        sys.exit(1)

    sorted_items = sorted(changes.values(), key=lambda x: x["change_percent"], reverse=True)
    top_gainers = sorted_items[:TOP_N]
    top_losers = sorted_items[-TOP_N:]
    top_losers.reverse()
    volatile = detect_volatility(changes)

    print(f"🔥 رشدها: {', '.join(c['name'] for c in top_gainers)}")
    print(f"❄️ افت‌ها: {', '.join(c['name'] for c in top_losers)}")
    print(f"⚡ نوسان: {len(volatile)} ارز")

    history.append({"timestamp": timestamp, "items": current_prices})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)

    write_readme(top_gainers, top_losers, volatile, changes, timestamp)
    write_json_files(top_gainers, top_losers, volatile, changes, timestamp)
    write_dashboard()

    print("✅ پایان موفق")

if __name__ == "__main__":
    main()