"""Customer / Buyer / PO Number সংক্রান্ত validation — সবগুলো case-sensitive এবং
config.py-এর ফিক্সড লিস্টের সাথে হুবহু মিলতে হবে (ERP-এর রিকোয়ারমেন্ট অনুযায়ী)।"""
from config import CUSTOMERS, BUYERS


def validate_customer(customer_type, customer_name):
    """customer_name ফাঁকা থাকলে ঠিক আছে (PDF থেকে auto নেওয়া হবে)।
    ভরা থাকলে অবশ্যই ওই customer_type-এর ফিক্সড লিস্টের সাথে case-sensitive মিলতে হবে।"""
    if not customer_name:
        return None
    allowed = CUSTOMERS.get(customer_type, [])
    if allowed and customer_name not in allowed:
        return (
            f"Customer নাম '{customer_name}' {customer_type} লিস্টের সাথে "
            f"হুবহু (case-sensitive) মিলছে না। লিস্ট থেকে সিলেক্ট করুন।"
        )
    return None


def validate_buyer(buyer_name):
    """Buyer বাধ্যতামূলক — ফাঁকা রাখা যাবে না, আর অবশ্যই ফিক্সড লিস্টের সাথে
    case-sensitive মিলতে হবে।"""
    if not buyer_name or not buyer_name.strip():
        return "Buyer নাম আবশ্যক — এই ফিল্ড খালি রাখা যাবে না।"
    if buyer_name not in BUYERS:
        return (
            f"Buyer নাম '{buyer_name}' তালিকার সাথে হুবহু (case-sensitive) মিলছে না। "
            f"লিস্ট থেকে সিলেক্ট করুন।"
        )
    return None


def validate_po_number(po_override, pdf_po_number):
    """PO Number ফাঁকা থাকলে PDF থেকে auto নেওয়া হবে।
    ম্যানুয়ালি দিলে PDF-এ পাওয়া PO Number-এর সাথে হুবহু মিলতে হবে।"""
    if not po_override:
        return None
    if po_override != (pdf_po_number or ''):
        return (
            f"PO Number '{po_override}' আপলোড করা PDF-এর PO Number "
            f"('{pdf_po_number}') এর সাথে মিলছে না।"
        )
    return None
