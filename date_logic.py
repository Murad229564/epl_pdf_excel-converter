"""
Delivery Date সংক্রান্ত সব লজিক এখানে।

Default নিয়ম: order input date + 7 days থেকে শুরু করে সবচেয়ে কাছের Friday খুঁজে বের করা হয়
(Friday-ই না হলে সামনের দিকে এগিয়ে Friday-তে যাওয়া হয়), তারপর সেই Friday যদি BD সরকারি
ছুটির তালিকায় থাকে, তাহলে তার পরের Friday-তে যাওয়া হয় (যতক্ষণ না ছুটি-মুক্ত Friday পাওয়া যায়)।

Manual override নিয়ম: ব্যবহারকারী নিজে থেকে ডেট বসাতে চাইলে, সেই ডেট অবশ্যই
current date + 4 days বা তার পরে হতে হবে — না হলে reject করা হবে।
"""
from datetime import date, timedelta
from config import BD_HOLIDAYS


def _next_friday_on_or_after(d: date) -> date:
    days_until_friday = (4 - d.weekday()) % 7  # Monday=0 ... Friday=4
    return d + timedelta(days=days_until_friday)


def get_default_delivery_date(today: date = None) -> date:
    """order input date + 7 days থেকে শুরু করে ছুটি-মুক্ত প্রথম Friday রিটার্ন করে।"""
    today = today or date.today()
    candidate = _next_friday_on_or_after(today + timedelta(days=7))
    while candidate.isoformat() in BD_HOLIDAYS:
        candidate += timedelta(days=7)
    return candidate


def validate_manual_delivery_date(date_str: str, today: date = None):
    """Manual delivery date ভ্যালিড কিনা চেক করে।
    Returns (is_valid: bool, error_message: str|None, parsed_date: date|None)"""
    today = today or date.today()
    try:
        parsed = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return False, "Delivery Date ফরম্যাট সঠিক না (YYYY-MM-DD হতে হবে)", None

    min_allowed = today + timedelta(days=4)
    if parsed < min_allowed:
        return False, (
            f"Delivery Date কমপক্ষে {min_allowed.isoformat()} বা তার পরে হতে হবে "
            f"(আজকের তারিখ থেকে ন্যূনতম ৪ দিন পর)"
        ), None

    return True, None, parsed
