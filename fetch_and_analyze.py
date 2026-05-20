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

def fetch_all_prices():
    """
    دریافت قیمت تمام ارزها با مدیریت صفحه‌بندی و خطاها
    """
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
            
            # بررسی ساختار پاسخ
            if not isinstance(data, dict):
                print(f"⚠️ پاسخ API ساختار غیرمنتظره‌ای دارد: {type(data)}")
                break
                
            if not data.get("success", False):
                print(f"⚠️ خطا از API: {data.get('message', 'نامشخص')}")
                break
                
            if "result" not in data or "items" not in data["result"]:
                print("⚠️ ساختار 'result' یا 'items' در پاسخ یافت نشد")
                break
                
            items = data["result"]["items"]
            if not items:
                print(f"📭 صفحه {page} خالی است - پایان دریافت")
                break
                
            all_items.extend(items)
            print(f"✅ {len(items)} آیتم از صفحه {page} دریافت شد")
            
            # بررسی وجود صفحه بعدی
            meta = data.get("result", {}).get("meta", {}).get("paginateHelper", {})
            current_page = meta.get("currentPage", page)
            last_page = meta.get("lastPage", 1)
            
            if current_page >= last_page:
                print(f"🏁 به صفحه آخر رسیدیم ({current_page}/{last_page})")
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ خطا در دریافت داده‌ها: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"❌ خطا در تجزیه JSON: {e}")
            break
        except Exception as e:
            print(f"❌ خطای غیرمنتظره: {e}")
            break
    
    return all_items

def load_history():
    """خواندن داده‌های تاریخی از فایل"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ خطا در خواندن تاریخچه: {e}")
            return []
    return []

def save_history(history):
    """ذخیره‌سازی داده‌های تاریخی"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"✅ تاریخچه در {HISTORY_FILE} ذخیره شد")
    except IOError as e:
        print(f"❌ خطا در ذخیره تاریخچه: {e}")

def calculate_changes(current_prices, previous_prices):
    """محاسبه درصد تغییرات"""
    changes = {}
    
    if not current_prices:
        print("⚠️ قیمت فعلی موجود نیست")
        return changes
        
    prev_dict = {}
    if previous_prices:
        prev_dict = {item["slug"]: item["price"] for item in previous_prices}
    
    for item in current_prices:
        slug = item.get("slug", "Unknown")
        current_price = item.get("price", 0)
        
        if not slug or current_price is None:
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
    """تولید فایل README.md"""
    sorted_changes = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True) if all_changes else []
    
    # ساخت ردیف‌های جدول
    table_rows = ""
    for i, coin in enumerate(sorted_changes[:20], 1):
        if coin["change_percent"] != 0:  # فقط موارد با تغییرات غیر صفر
            emoji = "📈" if coin["change_percent"] > 0 else "📉"
            table_rows += f"| {i} | {coin['name']} | {coin['current_price']:,.2f} | {coin['change_percent']:+.2f}% {emoji} |\n"
    
    # ساخت بخش برترین‌ها
    gainers_list = "\n".join([f"{i+1}. {c['name']}: **%{c['change_percent']:+.2f}**" for i, c in enumerate(top_gainers)]) if top_gainers else "داده‌ای موجود نیست"
    losers_list = "\n".join([f"{i+1}. {c['name']}: **%{c['change_percent']:+.2f}**" for i, c in enumerate(top_losers)]) if top_losers else "داده‌ای موجود نیست"
    
    readme_content = f"""# 📊 Bitbarg Market Monitor (بات نتایج زنده)

**🕒 آخرین به‌روزرسانی:** `{timestamp}`

---

## 🔥 بیشترین رشدها
{gainers_list}

## ❄️ بیشترین افت‌ها
{losers_list}

---

## 📈 جدول برترین تغییرات
| رتبه | ارز | قیمت فعلی | تغییر ۲۴ ساعته |
|------|-----|-----------|----------------|
{table_rows if table_rows else "| - | - | - | - |"}

---
*🤖 این گزارش به صورت خودکار توسط GitHub Actions تولید و به‌روزرسانی می‌شود.*
"""
    try:
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"✅ گزارش README در {README_FILE} ذخیره شد")
    except IOError as e:
        print(f"❌ خطا در ذخیره README: {e}")

def generate_json_report(top_gainers, top_losers, all_changes, timestamp):
    """تولید گزارش JSON کامل"""
    report = {
        "timestamp": timestamp,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "all_changes": all_changes
    }
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ گزارش JSON در {REPORT_FILE} ذخیره شد")
    except IOError as e:
        print(f"❌ خطا در ذخیره JSON: {e}")

def main():
    print("🚀 شروع فرآیند واکشی و تحلیل داده‌ها...")
    
    # 1. واکشی قیمت‌های فعلی
    current_prices = fetch_all_prices()
    if not current_prices:
        print("❌ هیچ داده‌ای دریافت نشد. عملیات متوقف شد.")
        sys.exit(1)
    
    print(f"✅ مجموعاً {len(current_prices)} ارز دریافت شد")
    
    # 2. بارگذاری تاریخچه
    history = load_history()
    previous_prices = history[-1]["items"] if history else []
    
    if previous_prices:
        print(f"📚 تاریخچه موجود: {len(history)} وضعیت قبلی")
    else:
        print("📚 تاریخچه‌ای یافت نشد - این اولین اجراست")
    
    # 3. محاسبه تغییرات
    all_changes = calculate_changes(current_prices, previous_prices)
    
    if not all_changes:
        print("❌ هیچ تغییری محاسبه نشد")
        sys.exit(1)
    
    # 4. یافتن برترین‌ها
    sorted_items = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
    top_gainers = sorted_items[:TOP_N]
    top_losers = sorted_items[-TOP_N:]
    top_losers.reverse()
    
    print(f"🔥 ۵ ارز برتر در رشد: {', '.join([c['name'] for c in top_gainers])}")
    print(f"❄️ ۵ ارز برتر در افت: {', '.join([c['name'] for c in top_losers])}")
    
    # 5. به‌روزرسانی تاریخچه
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({
        "timestamp": timestamp,
        "items": current_prices
    })
    
    # محدود کردن تاریخچه
    if len(history) > 100:
        history = history[-100:]
        print("📝 تاریخچه به ۱۰۰ وضعیت آخر محدود شد")
    
    save_history(history)
    
    # 6. تولید گزارش‌ها
    generate_readme(top_gainers, top_losers, all_changes, timestamp)
    generate_json_report(top_gainers, top_losers, all_changes, timestamp)
    
    print("✅ عملیات با موفقیت به پایان رسید!")

if __name__ == "__main__":
    main()