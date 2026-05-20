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
    """استخراج قیمت از ساختار API بیت‌برگ"""
    if "currency_price" in item and item["currency_price"] is not None:
        return float(item["currency_price"])
    if "quote" in item and item["quote"] is not None:
        return float(item["quote"])
    if "price" in item and item["price"] is not None:
        return float(item["price"])
    return 0.0

def fetch_all_prices():
    """دریافت تمام قیمت‌ها"""
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
    """بارگذاری تاریخچه"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در خواندن تاریخچه: {e}")
            return []
    return []

def save_history(history):
    """ذخیره تاریخچه"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"✅ تاریخچه ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره تاریخچه: {e}")

def calculate_changes(current_prices, previous_prices):
    """محاسبه درصد تغییرات"""
    changes = {}
    if not current_prices:
        return changes
    
    prev_dict = {}
    if previous_prices:
        prev_dict = {item["slug"]: get_price(item) for item in previous_prices if "slug" in item}
        print(f"📊 {len(prev_dict)} قیمت قبلی برای مقایسه موجود است")
    
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

def generate_readme(top_gainers, top_losers, all_changes, timestamp):
    """تولید فایل README.md با فرمت Markdown صحیح"""
    
    lines = []
    lines.append("# 📊 Bitbarg Market Monitor (گزارش  زنده هر ۵ دقیقه)")
    lines.append("")
    lines.append(f"**🕒 آخرین به‌روزرسانی:** `{timestamp}`")
    lines.append(f"**📈 تعداد ارزهای ردیابی‌شده:** `{len(all_changes)}`")
    lines.append("")
    
    # بررسی اولین اجرا
    has_changes = any(c["change_percent"] != 0.0 for c in all_changes.values())
    if not has_changes:
        lines.append("> ⚠️ **توجه:** این اولین اجراست. درصد تغییرات ۲۴ ساعته از اجرای بعدی محاسبه خواهد شد.")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("## 🔥 بیشترین رشدها")
    lines.append("")
    if top_gainers:
        for i, c in enumerate(top_gainers, 1):
            lines.append(f"{i}. **{c['name']}**: {c['change_percent']:+.2f}% (قیمت: {c['current_price']:,.2f} USDT)")
    else:
        lines.append("هنوز محاسبه نشده (اجرای اول)")
    lines.append("")
    
    lines.append("## ❄️ بیشترین افت‌ها")
    lines.append("")
    if top_losers:
        for i, c in enumerate(top_losers, 1):
            lines.append(f"{i}. **{c['name']}**: {c['change_percent']:+.2f}% (قیمت: {c['current_price']:,.2f} USDT)")
    else:
        lines.append("هنوز محاسبه نشده (اجرای اول)")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("## 📈 ۲۰ ارز برتر (بر اساس درصد تغییر)")
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
    lines.append("*🤖 این گزارش به‌صورت خودکار توسط GitHub Actions تولید و به‌روزرسانی می‌شود.*")
    lines.append("*📡 داده‌ها از API رسمی [Bitbarg](https://bitbarg.com) دریافت می‌شود.*")
    lines.append("")
    
    # نوشتن با خطوط جداگانه
    try:
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ README ذخیره شد ({len(lines)} خط)")
    except Exception as e:
        print(f"❌ خطا در ذخیره README: {e}")

def generate_json_report(top_gainers, top_losers, all_changes, timestamp):
    """تولید گزارش JSON"""
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
    
    # ۱. دریافت قیمت‌ها
    current_prices = fetch_all_prices()
    if not current_prices:
        print("❌ داده‌ای دریافت نشد")
        t = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        generate_readme([], [], {}, t)
        generate_json_report([], [], {}, t)
        sys.exit(1)
    
    print(f"✅ مجموعاً {len(current_prices)} ارز دریافت شد")
    
    # ۲. بارگذاری تاریخچه
    history = load_history()
    previous_prices = history[-1]["items"] if history else []
    
    if previous_prices:
        print(f"📚 تاریخچه: {len(history)} وضعیت قبلی")
    else:
        print("📚 اولین اجرا - تاریخچه‌ای یافت نشد")
    
    # ۳. محاسبه تغییرات
    all_changes = calculate_changes(current_prices, previous_prices)
    if not all_changes:
        print("❌ تغییری محاسبه نشد")
        sys.exit(1)
    
    print(f"📊 تغییرات برای {len(all_changes)} ارز محاسبه شد")
    
    # ۴. یافتن برترین‌ها
    sorted_items = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
    top_gainers = sorted_items[:TOP_N]
    top_losers = sorted_items[-TOP_N:]
    top_losers.reverse()
    
    print(f"🔥 برترین رشدها: {', '.join([f'{c[\"name\"]}({c[\"change_percent\"]:+.2f}%)' for c in top_gainers])}")
    print(f"❄️ برترین افت‌ها: {', '.join([f'{c[\"name\"]}({c[\"change_percent\"]:+.2f}%)' for c in top_losers])}")
    
    # ۵. به‌روزرسانی تاریخچه
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({
        "timestamp": timestamp,
        "items": current_prices
    })
    
    if len(history) > 100:
        history = history[-100:]
        print("📝 تاریخچه به ۱۰۰ وضعیت محدود شد")
    
    save_history(history)
    
    # ۶. تولید گزارش‌ها
    generate_readme(top_gainers, top_losers, all_changes, timestamp)
    generate_json_report(top_gainers, top_losers, all_changes, timestamp)
    
    print("✅ عملیات با موفقیت به پایان رسید!")

if __name__ == "__main__":
    main()