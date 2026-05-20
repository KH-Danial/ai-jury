import requests
import json
import os
import sys
import traceback
from datetime import datetime, timezone

# --- تنظیمات ---
API_BASE_URL = "https://api.bitbarg.com/api/v1/docs/prices"
HISTORY_FILE = "price_history.json"
README_FILE = "README.md"
TOP_N = 5

def fetch_all_prices():
    """دریافت تمام قیمت‌ها با مدیریت کامل خطاها و لاگ‌گیری دقیق"""
    all_items = []
    page = 1
    last_page = 1

    print(f"🔍 شروع دریافت داده از {API_BASE_URL}")

    while True:
        try:
            print(f"📥 در حال دریافت صفحه {page}...")
            resp = requests.get(
                API_BASE_URL,
                params={"pageSize": 100, "page": page, "base": "usdt"},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "GitHub-Action-Monitor/1.0"
                },
                timeout=30
            )
            
            print(f"📊 وضعیت پاسخ: {resp.status_code}")
            print(f"🔗 URL نهایی: {resp.url}")
            
            resp.raise_for_status()
            
            content_type = resp.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                print(f"⚠️ نوع محتوای غیرمنتظره: {content_type}")
                print(f"📄 محتوای پاسخ: {resp.text[:200]}")
                break
            
            data = resp.json()
            
            print(f"🔑 کلیدهای پاسخ: {list(data.keys())}")
            print(f"✅ success: {data.get('success')}")
            print(f"📝 message: {data.get('message')}")
            
            if not isinstance(data, dict):
                print(f"⚠️ ساختار پاسخ غیرمنتظره: {type(data)}")
                break
                
            if not data.get("success"):
                error_msg = data.get('message', 'خطای نامشخص')
                print(f"❌ API خطا داد: {error_msg}")
                break
                
            result = data.get("result", {})
            if not isinstance(result, dict):
                print(f"⚠️ 'result' یک دیکشنری نیست: {type(result)}")
                break
                
            items = result.get("items", [])
            if not items:
                print("📭 هیچ آیتمی در این صفحه یافت نشد")
                break
                
            all_items.extend(items)
            print(f"✅ {len(items)} آیتم از صفحه {page} دریافت شد (کل: {len(all_items)})")
            
            meta = result.get("meta", {})
            paginate_helper = meta.get("paginateHelper", {})
            current_page = paginate_helper.get("currentPage", page)
            last_page = paginate_helper.get("lastPage", 1)
            total_items = paginate_helper.get("total", 0)
            
            print(f"📖 صفحه {current_page} از {last_page} (کل آیتم‌ها: {total_items})")
            
            if current_page >= last_page:
                print(f"🏁 به صفحه آخر رسیدیم")
                break
                
            page += 1
            
        except requests.exceptions.Timeout:
            print(f"⏰ درخواست صفحه {page} با timeout مواجه شد")
            break
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 خطای اتصال: {e}")
            break
        except requests.exceptions.RequestException as e:
            print(f"🌐 خطای شبکه: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"📄 خطا در تجزیه JSON: {e}")
            if 'resp' in locals():
                print(f"📄 محتوای پاسخ: {resp.text[:500]}")
            break
        except Exception as e:
            print(f"💥 خطای غیرمنتظره: {e}")
            traceback.print_exc()
            break

    print(f"📦 مجموع آیتم‌های دریافت شده: {len(all_items)}")
    return all_items

def load_history():
    """بارگذاری امن تاریخچه"""
    if not os.path.exists(HISTORY_FILE):
        print(f"📂 فایل تاریخچه {HISTORY_FILE} وجود ندارد - این اولین اجراست")
        return []
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
            print(f"📚 تاریخچه با {len(history)} وضعیت بارگذاری شد")
            return history
    except json.JSONDecodeError as e:
        print(f"⚠️ خطا در خواندن تاریخچه (JSON نامعتبر): {e}")
        return []
    except Exception as e:
        print(f"⚠️ خطا در خواندن تاریخچه: {e}")
        return []

def save_history(history):
    """ذخیره تاریخچه با مدیریت خطا"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"💾 تاریخچه ({len(history)} وضعیت) در {HISTORY_FILE} ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در ذخیره تاریخچه: {e}")

def get_item_price(item):
    """
    استخراج قیمت از آیتم با پشتیبانی از ساختارهای مختلف.
    این تابع جدید مشکل اصلی را حل می‌کند.
    """
    # اولویت: currency_price (دلار)
    price = item.get("currency_price")
    if price is not None:
        return float(price)
    
    # سپس quote (تومان)
    price = item.get("quote")
    if price is not None:
        return float(price)
    
    # سپس price (اگر وجود داشته باشد)
    price = item.get("price")
    if price is not None:
        return float(price)
    
    # در نهایت، اگر هیچکدام وجود نداشت
    return None

def calculate_changes(current, previous):
    """محاسبه درصد تغییرات با استفاده از تابع استخراج قیمت جدید"""
    changes = {}
    if not current:
        print("⚠️ لیست قیمت‌های فعلی خالی است")
        return changes

    prev_dict = {}
    if previous:
        for item in previous:
            slug = item.get("slug")
            price = get_item_price(item)
            if slug and price is not None:
                prev_dict[slug] = price
        print(f"📊 {len(prev_dict)} قیمت قبلی برای مقایسه موجود است")

    skipped = 0
    for item in current:
        slug = item.get("slug")
        price = get_item_price(item)
        
        if not slug or price is None:
            skipped += 1
            continue

        prev_price = prev_dict.get(slug)
        if prev_price and prev_price > 0:
            change_percent = ((price - prev_price) / prev_price) * 100
        else:
            change_percent = 0.0

        changes[slug] = {
            "name": slug,
            "current_price": price,
            "previous_price": prev_price,
            "change_percent": round(change_percent, 4)
        }
    
    if skipped:
        print(f"⚠️ {skipped} آیتم به دلیل عدم وجود slug یا قیمت نادیده گرفته شد")
    
    print(f"✅ تغییرات برای {len(changes)} ارز محاسبه شد")
    return changes

def generate_files(top_gainers, top_losers, all_changes, timestamp):
    """تولید گزارش‌ها حتی در صورت عدم وجود داده"""
    
    if not all_changes:
        readme_body = f"""# 📊 Bitbarg Market Monitor

**🕒 آخرین به‌روزرسانی:** `{timestamp}`

## ⚠️ وضعیت: خطا در دریافت داده
متأسفانه در این اجرا داده‌ای از API دریافت نشد. لطفاً لاگ‌های اجرا را بررسی کنید.

**دلایل احتمالی:**
- مشکل در اتصال به API بیت‌برگ
- تغییر در ساختار API
- محدودیت‌های شبکه در GitHub Actions

---
*🤖 این گزارش توسط GitHub Actions تولید می‌شود.*
"""
    else:
        sorted_all = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
        
        gainers_str = "\n".join([
            f"{i+1}. **{c['name']}**: {c['change_percent']:+.2f}% (قیمت: {c['current_price']:,.2f} دلار)"
            for i, c in enumerate(top_gainers)
        ])
        
        losers_str = "\n".join([
            f"{i+1}. **{c['name']}**: {c['change_percent']:+.2f}% (قیمت: {c['current_price']:,.2f} دلار)"
            for i, c in enumerate(top_losers)
        ])
        
        table_rows = ""
        for i, coin in enumerate(sorted_all[:20], 1):
            emoji = "🟢" if coin["change_percent"] > 0 else ("🔴" if coin["change_percent"] < 0 else "⚪")
            table_rows += f"| {i} | {coin['name']} | {coin['current_price']:,.2f} | {coin['change_percent']:+.2f}% {emoji} |\n"
        
        readme_body = f"""# 📊 Bitbarg Market Monitor (گزارش زنده)

**🕒 آخرین به‌روزرسانی:** `{timestamp}`
**📈 تعداد ارزهای ردیابی‌شده:** `{len(all_changes)}`

---

## 🔥 ۵ ارز با بیشترین رشد (۲۴ ساعته)
{gainers_str}

## ❄️ ۵ ارز با بیشترین افت (۲۴ ساعته)
{losers_str}

---

## 📋 ۲۰ ارز با بیشترین تغییرات
| رتبه | ارز | قیمت (دلار) | تغییر ۲۴ ساعته |
|------|-----|-------------|----------------|
{table_rows}

---
*🤖 این گزارش به‌صورت خودکار هر ۶ ساعت توسط GitHub Actions به‌روزرسانی می‌شود.*
*📡 داده‌ها از API رسمی [Bitbarg](https://bitbarg.com) دریافت می‌شود.*
"""
    
    try:
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write(readme_body)
        print(f"📄 فایل {README_FILE} با موفقیت ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در نوشتن README: {e}")
    
    # --- ساخت گزارش JSON ---
    report = {
        "metadata": {
            "timestamp": timestamp,
            "source": "Bitbarg API",
            "total_coins": len(all_changes)
        },
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "all_changes": all_changes
    }
    
    try:
        with open("market_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("📄 فایل market_report.json با موفقیت ذخیره شد")
    except Exception as e:
        print(f"❌ خطا در نوشتن JSON: {e}")

def main():
    print("="*50)
    print("🚀 شروع فرآیند واکشی و تحلیل قیمت‌ها")
    print("="*50)
    
    # ۱. دریافت قیمت‌های فعلی
    current_prices = fetch_all_prices()
    
    if not current_prices:
        print("❌ هیچ قیمتی دریافت نشد - در حال تولید گزارش خطا...")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        generate_files([], [], {}, timestamp)
        sys.exit(1)
    
    # ۲. بارگذاری تاریخچه
    history = load_history()
    previous_prices = history[-1]["items"] if history else []
    
    # ۳. محاسبه تغییرات
    all_changes = calculate_changes(current_prices, previous_prices)
    
    if not all_changes:
        print("❌ هیچ تغییری محاسبه نشد")
        sys.exit(1)
    
    # ۴. یافتن برترین‌ها
    sorted_items = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
    top_gainers = sorted_items[:TOP_N]
    top_losers = sorted_items[-TOP_N:]
    top_losers.reverse()
    
    print("\n" + "="*50)
    print("📊 نتایج تحلیل:")
    print(f"🔥 برترین رشدها: {', '.join([f'{c[\"name\"]}({c[\"change_percent\"]:+.2f}%)' for c in top_gainers])}")
    print(f"❄️ برترین افت‌ها: {', '.join([f'{c[\"name\"]}({c[\"change_percent\"]:+.2f}%)' for c in top_losers])}")
    print("="*50 + "\n")
    
    # ۵. به‌روزرسانی تاریخچه
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({
        "timestamp": timestamp,
        "items": current_prices
    })
    
    # محدود کردن تاریخچه به ۱۰۰ وضعیت
    if len(history) > 100:
        history = history[-100:]
        print("📝 تاریخچه به ۱۰۰ وضعیت آخر محدود شد")
    
    save_history(history)
    
    # ۶. تولید گزارش‌ها
    generate_files(top_gainers, top_losers, all_changes, timestamp)
    
    print("\n" + "="*50)
    print("✅ عملیات با موفقیت به پایان رسید!")
    print("="*50)

if __name__ == "__main__":
    main()