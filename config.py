"""
সব fixed configuration এক জায়গায় — Customer/Buyer লিস্ট এবং BD সরকারি ছুটির তালিকা।
নতুন Customer/Buyer যোগ করতে চাইলে শুধু নিচের লিস্টে একটা লাইন যোগ করুন, কোথাও
কোড পরিবর্তন করার দরকার নেই।

গুরুত্বপূর্ণ: BD_HOLIDAYS_2026 লিস্টটা প্রতি বছর নতুন করে বসাতে হবে (সরকার প্রতি
বছর নতুন করে ছুটির তালিকা প্রকাশ করে)। প্রতিটা এন্ট্রি "YYYY-MM-DD" ফরম্যাটে।
"""

# ---------------------------------------------------------------------------
# IN-HOUSE customer এবং buyer লিস্ট (case-sensitive — ERP-এর সাথে হুবহু মিলতে হবে)
# ---------------------------------------------------------------------------
CUSTOMERS = {
    "IN-HOUSE": [
        "Epyllion Style Limited",
        "Epyllion Knitwears Limited",
        "Dekko Knitwears Limited",
        "Dazzling Dresses Ltd.",
    ],
    # আপাতত OUT-HOUSE-এর কোনো fixed customer লিস্ট নেই — PDF থেকে auto নেওয়া হবে,
    # অথবা চাইলে এখানে যোগ করে দিতে পারবেন (IN-HOUSE-এর মতো একই ফরম্যাটে)
    "OUT-HOUSE": [],
}

BUYERS = [
    "MARKS & SPENCER SCM LTD.",
    "C&A BUYING GMBH & CO. KG",
    "S.OLIVER",
    "Target Australia",
    "Tommy Hilfiger",
    "Carhartt",
    "Varner",
    "Express",
    "Country Road",
    "Ralph Lauren",
    "Stanley Stella",
    "Bonds",
]

# ---------------------------------------------------------------------------
# Customer-wise Delivery Address — আপাতত ফাঁকা, পরে data দিলে এখানে বসিয়ে দেওয়া হবে:
# "Epyllion Style Limited": ["Address 1", "Address 2"], ...
# ---------------------------------------------------------------------------
DELIVERY_ADDRESSES = {}

# ---------------------------------------------------------------------------
# ২০২৬ সালের সরকারি ছুটির তালিকা (Ministry of Public Administration অনুযায়ী)
# প্রতি বছর জানুয়ারিতে নতুন তালিকা এলে এই লিস্ট আপডেট করে দিতে হবে।
# ---------------------------------------------------------------------------
BD_HOLIDAYS_2026 = [
    "2026-02-04",  # Shab-e-Barat
    "2026-02-21",  # Shaheed Day / Int'l Mother Language Day
    "2026-03-17",  # Sheikh Mujibur Rahman's Birthday
    "2026-03-18",  # Shab-e-Qadr
    "2026-03-19", "2026-03-20", "2026-03-21", "2026-03-22", "2026-03-23",  # Eid-ul-Fitr period
    "2026-03-26",  # Independence Day
    "2026-04-13",  # Chaitra Sankranti (Hill districts)
    "2026-04-14",  # Pohela Boishakh
    "2026-05-01",  # May Day & Buddha Purnima
    "2026-05-26", "2026-05-27", "2026-05-28", "2026-05-29", "2026-05-30", "2026-05-31",  # Eid-ul-Azha period
    "2026-06-26",  # Ashura
    "2026-08-05",  # July Mass Uprising Day
    "2026-08-15",  # National Mourning Day
    "2026-08-26",  # Eid-e-Milad-un-Nabi
    "2026-09-04",  # Janmashtami
    "2026-10-20", "2026-10-21",  # Durga Puja
    "2026-12-16",  # Victory Day
    "2026-12-25",  # Christmas Day
]

BD_HOLIDAYS = set(BD_HOLIDAYS_2026)
