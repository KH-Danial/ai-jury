import requests
import json
import os
import sys
from datetime import datetime, timezone

# --- تنظیمات ---
API_BASE_URL = "https://api.bitbarg.com/api/v1/docs/prices"
HISTORY_FILE = "price_history.json"
README_FILE = "README.md"
REPORT_FILE = "market_report.json"
LATEST_FILE = "latest.json"
DASHBOARD_FILE = "index.html"
TOP_N = 5
VOLATILITY_THRESHOLD = 2.0   # درصد نوسان بالا (مثلاً ۲٪ در ۵ دقیقه)

def get_price(item):
    """استخراج قیمت از ساختار API بیت‌برگ"""
    if "currency_price" in item and item["currency_price"] is not None:
        return float(item["currency_price"])
    if "quote" in item and item["quote"] is not None:
        return float(item["quote"])
    if "price" in item and item["price"] is not None:
        return float(item["price"])
    return 0.0

def fetch_all_prices():
    """دریافت تمام قیمت‌ها با مدیریت صفحه‌بندی"""
    all_items = []
    page = 1
    while True:
        try:
            print(f"📥 دریافت صفحه {page}...")
            resp = requests.get(
                API_BASE_URL,
                params={"pageSize": 100, "page": page, "base": "usdt"},
                headers={"Accept": "application/json"},
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict) or not data.get("success"):
                print(f"⚠️ خطا از API: {data.get('message', 'نامشخص')}")
                break
            items = data.get("result", {}).get("items", [])
            if not items:
                break
            all_items.extend(items)
            print(f"✅ {len(items)} آیتم از صفحه {page} دریافت شد")
            meta = data.get("result", {}).get("meta", {}).get("paginateHelper", {})
            if meta.get("currentPage", page) >= meta.get("lastPage", 1):
                break
            page += 1
        except Exception as e:
            print(f"❌ خطا: {e}")
            break
    return all_items

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"✅ تاریخچه ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره تاریخچه: {e}")

def calculate_changes(current_prices, previous_prices):
    changes = {}
    if not current_prices:
        return changes
    prev_dict = {}
    if previous_prices:
        prev_dict = {item["slug"]: get_price(item) for item in previous_prices if "slug" in item}
    for item in current_prices:
        slug = item.get("slug", "Unknown")
        current_price = get_price(item)
        if not slug:
            continue
        previous_price = prev_dict.get(slug)
        if previous_price and previous_price > 0:
            change_percent = ((current_price - previous_price) / previous_price) * 100
        else:
            change_percent = 0.0
        changes[slug] = {
            "name": slug,
            "current_price": current_price,
            "previous_price": previous_price,
            "change_percent": round(change_percent, 4)
        }
    return changes

def detect_volatility(all_changes, threshold=VOLATILITY_THRESHOLD):
    """ارزهایی که در ۵ دقیقه اخیر بیش از threshold درصد تغییر کرده‌اند"""
    volatile = []
    for coin in all_changes.values():
        if abs(coin["change_percent"]) >= threshold:
            volatile.append(coin)
    # مرتب‌سازی بر اساس قدر مطلق تغییر
    volatile.sort(key=lambda x: abs(x["change_percent"]), reverse=True)
    return volatile

def generate_readme(top_gainers, top_losers, volatile_coins, all_changes, timestamp):
    lines = []
    lines.append("# 📊 Bitbarg Market Monitor (گزارش زنده)")
    lines.append("")
    lines.append(f"**🕒 آخرین به‌روزرسانی:** `{timestamp}`")
    lines.append(f"**📈 تعداد ارزهای ردیابی‌شده:** `{len(all_changes)}`")
    lines.append("")

    # پیام اولین اجرا
    has_changes = any(c["change_percent"] != 0.0 for c in all_changes.values())
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

    # بخش نوسان‌های بالا
    lines.append("## ⚡ نوسان‌های بالا (تغییر بیش از {}% در ۵ دقیقه)".format(VOLATILITY_THRESHOLD))
    lines.append("")
    if volatile_coins:
        for i, c in enumerate(volatile_coins[:10], 1):   # حداکثر ۱۰ مورد
            emoji = "🔺" if c["change_percent"] > 0 else "🔻"
            lines.append(f"{i}. **{c['name']}**: %{c['change_percent']:+.2f} {emoji}")
    else:
        lines.append("در این لحظه نوسان شدیدی مشاهده نشد.")
    lines.append("")

    lines.append("---")
    lines.append("## 📋 ۲۰ ارز برتر (بر اساس درصد تغییر)")
    lines.append("")
    lines.append("| رتبه | ارز | قیمت فعلی (USDT) | تغییر ۲۴ ساعته |")
    lines.append("|------|-----|-----------------|----------------|")
    sorted_changes = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
    for i, coin in enumerate(sorted_changes[:20], 1):
        emoji = "🟢" if coin["change_percent"] > 0 else ("🔴" if coin["change_percent"] < 0 else "⚪")
        lines.append(f"| {i} | {coin['name']} | {coin['current_price']:,.2f} | {coin['change_percent']:+.2f}% {emoji} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*🤖 این گزارش به‌صورت خودکار هر ۵ دقیقه توسط GitHub Actions به‌روزرسانی می‌شود.*")
    lines.append("*📡 داده‌ها از API رسمی [Bitbarg](https://bitbarg.com) دریافت می‌شود.*")
    lines.append("")

    try:
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ README ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره README: {e}")

def generate_json_report(top_gainers, top_losers, volatile_coins, all_changes, timestamp):
    report = {
        "timestamp": timestamp,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "volatile_coins": volatile_coins,
        "all_changes": all_changes
    }
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON گزارش ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره JSON: {e}")

def generate_latest_json(top_gainers, top_losers, volatile_coins, all_changes, timestamp):
    """ایجاد API شخصی سبک"""
    latest = {
        "timestamp": timestamp,
        "total_coins": len(all_changes),
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "volatile": volatile_coins[:20],  # حداکثر ۲۰ نوسان بالا
        "all": all_changes
    }
    try:
        with open(LATEST_FILE, "w", encoding="utf-8") as f:
            json.dump(latest, f, indent=2, ensure_ascii=False)
        print(f"✅ latest.json ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره latest.json: {e}")

def generate_dashboard_html():
    """داشبورد ساده با Chart.js که از latest.json تغذیه می‌کند"""
    html = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>داشبورد بازار Bitbarg</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body { font-family: Tahoma, sans-serif; max-width: 900px; margin: auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 8px; border-bottom: 1px solid #ddd; text-align: center; }
        th { background: #4CAF50; color: white; }
        .up { color: green; } .down { color: red; }
        .volatile { background: #fff3e0; }
    </style>
</head>
<body>
    <h1>📊 داشبورد زنده بازار Bitbarg</h1>
    <p>🕒 آخرین به‌روزرسانی: <span id="timestamp">--</span></p>

    <div class="chart-container">
        <h2>📈 ۱۰ ارز با بیشترین تغییر (۵ دقیقه اخیر)</h2>
        <canvas id="changeChart" width="400" height="200"></canvas>
    </div>

    <div class="chart-container">
        <h2>⚡ نوسان‌های بالا (تغییر > %2)</h2>
        <table id="volatileTable">
            <thead><tr><th>ارز</th><th>قیمت (USDT)</th><th>تغییر</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>

    <script>
        fetch('latest.json')
            .then(response => response.json())
            .then(data => {
                document.getElementById('timestamp').textContent = data.timestamp;

                // ۱۰ ارز برتر بر اساس قدر مطلق تغییر
                const all = Object.values(data.all);
                const top10 = all.sort((a,b) => Math.abs(b.change_percent) - Math.abs(a.change_percent)).slice(0,10);

                const labels = top10.map(c => c.name);
                const values = top10.map(c => c.change_percent);
                const colors = values.map(v => v >= 0 ? 'rgba(75, 192, 192, 0.7)' : 'rgba(255, 99, 132, 0.7)');

                const ctx = document.getElementById('changeChart').getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: '% تغییر',
                            data: values,
                            backgroundColor: colors,
                            borderColor: colors.map(c => c.replace('0.7', '1')),
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });

                // جدول نوسان‌های بالا
                const tbody = document.querySelector('#volatileTable tbody');
                data.volatile.forEach(coin => {
                    const tr = document.createElement('tr');
                    tr.className = 'volatile';
                    tr.innerHTML = `
                        <td>${coin.name}</td>
                        <td>${coin.current_price.toFixed(2)}</td>
                        <td class="${coin.change_percent >= 0 ? 'up' : 'down'}">%${coin.change_percent.toFixed(2)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            })
            .catch(err => console.error('خطا در دریافت داده:', err));
    </script>
</body>
</html>"""
    try:
        with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ داشبورد index.html ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره index.html: {e}")

def main():
    print("🚀 شروع فرآیند واکشی و تحلیل...")
    current_prices = fetch_all_prices()
    if not current_prices:
        print("❌ داده‌ای دریافت نشد")
        t = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        generate_readme([], [], [], {}, t)
        generate_json_report([], [], [], {}, t)
        generate_latest_json([], [], [], {}, t)
        generate_dashboard_html()
        sys.exit(1)

    print(f"✅ مجموعاً {len(current_prices)} ارز دریافت شد")
    history = load_history()
    previous_prices = history[-1]["items"] if history else []
    all_changes = calculate_changes(current_prices, previous_prices)
    if not all_changes:
        print("❌ تغییری محاسبه نشد")
        sys.exit(1)

    sorted_items = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
    top_gainers = sorted_items[:TOP_N]
    top_losers = sorted_items[-TOP_N:]
    top_losers.reverse()

    volatile_coins = detect_volatility(all_changes)

    print(f"🔥 برترین رشدها: {', '.join([f'{c[\"name\"]}({c[\"change_percent\"]:+.2f}%)' for c in top_gainers])}")
    print(f"❄️ برترین افت‌ها: {', '.join([f'{c[\"name\"]}({c[\"change_percent\"]:+.2f}%)' for c in top_losers])}")
    print(f"⚡ نوسان‌های بالا: {len(volatile_coins)} ارز")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({"timestamp": timestamp, "items": current_prices})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)

    generate_readme(top_gainers, top_losers, volatile_coins, all_changes, timestamp)
    generate_json_report(top_gainers, top_losers, volatile_coins, all_changes, timestamp)
    generate_latest_json(top_gainers, top_losers, volatile_coins, all_changes, timestamp)
    generate_dashboard_html()

    print("✅ عملیات با موفقیت به پایان رسید!")

if __name__ == "__main__":
    main()