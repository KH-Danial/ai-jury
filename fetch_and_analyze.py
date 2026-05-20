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
TOP_N = 5

def get_price(item):
    """
    استخراج قیمت از ساختار API بیت‌برگ.
    این تابع تمام فیلدهای محتمل قیمت را بررسی می‌کند.
    """
    if "currency_price" in item and item["currency_price"] is not None:
        return float(item["currency_price"])
    if "quote" in item and item["quote"] is not None:
        return float(item["quote"])
    if "price" in item and item["price"] is not None:
        return float(item["price"])
    return 0

def fetch_all_prices():
    all_items = []
    page = 1
    while True:
        try:
            print(f"📥 دریافت صفحه {page}...")
            response = requests.get(
                API_BASE_URL,
                params={"pageSize": 100, "page": page, "base": "usdt"},
                headers={"Accept": "application/json"},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
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
            changes[slug] = {
                "name": slug,
                "current_price": current_price,
                "previous_price": previous_price,
                "change_percent": round(change_percent, 4)
            }
        else:
            changes[slug] = {
                "name": slug,
                "current_price": current_price,
                "previous_price": None,
                "change_percent": 0.0
            }
    return changes

def generate_readme(top_gainers, top_losers, all_changes, timestamp):
    sorted_changes = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True) if all_changes else []

    # ساخت ردیف‌های جدول: نمایش همه ۲۰ ارز اول، حتی با تغییر صفر
    table_rows = ""
    for i, coin in enumerate(sorted_changes[:20], 1):
        emoji = "📈" if coin["change_percent"] > 0 else ("📉" if coin["change_percent"] < 0 else "➖")
        table_rows += f"| {i} | {coin['name']} | {coin['current_price']:,.2f} | {coin['change_percent']:+.2f}% {emoji} |\n"

    gainers_list = "\n".join([f"{i+1}. {c['name']}: **%{c['change_percent']:+.2f}**" for i, c in enumerate(top_gainers)]) if top_gainers else "هنوز محاسبه نشده (اجرای اول)"
    losers_list = "\n".join([f"{i+1}. {c['name']}: **%{c['change_percent']:+.2f}**" for i, c in enumerate(top_losers)]) if top_losers else "هنوز محاسبه نشده (اجرای اول)"

    # اگر هیچ تغییری بزرگتر از صفر نباشد، یک راهنما اضافه کن
    if not any(coin["change_percent"] != 0 for coin in sorted_changes[:20]):
        note = "\n⚠️ **توجه:** این اولین اجراست و درصد تغییرات ۲۴ ساعته پس از اجرای بعدی محاسبه خواهد شد.\n"
    else:
        note = ""

    readme_content = f"""# 📊 Bitbarg Market Monitor (گزارش زنده)

**🕒 آخرین به‌روزرسانی:** `{timestamp}`
**📈 تعداد ارزهای ردیابی‌شده:** `{len(all_changes)}`

{note}
---

## 🔥 بیشترین رشدها
{gainers_list}

## ❄️ بیشترین افت‌ها
{losers_list}

---

## 📈 ۲۰ ارز برتر (بر اساس درصد تغییر)
| رتبه | ارز | قیمت فعلی | تغییر ۲۴ ساعته |
|------|-----|-----------|----------------|
{table_rows if table_rows else "| - | - | - | - |"}

---
*🤖 این گزارش به صورت خودکار توسط GitHub Actions تولید و به‌روزرسانی می‌شود.*
"""
    try:
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"✅ README ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره README: {e}")

def generate_json_report(top_gainers, top_losers, all_changes, timestamp):
    report = {
        "timestamp": timestamp,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "all_changes": all_changes
    }
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره JSON: {e}")

def main():
    print("🚀 شروع فرآیند واکشی و تحلیل...")
    current_prices = fetch_all_prices()
    if not current_prices:
        print("❌ داده‌ای دریافت نشد.")
        t = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        generate_readme([], [], {}, t)
        generate_json_report([], [], {}, t)
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

    print(f"🔥 رشدها: {', '.join([c['name'] for c in top_gainers])}")
    print(f"❄️ افت‌ها: {', '.join([c['name'] for c in top_losers])}")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({"timestamp": timestamp, "items": current_prices})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)

    generate_readme(top_gainers, top_losers, all_changes, timestamp)
    generate_json_report(top_gainers, top_losers, all_changes, timestamp)
    print("✅ پایان موفق")

if __name__ == "__main__":
    main()