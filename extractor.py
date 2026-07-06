import re
import pdfplumber
import pandas as pd


def clean(s):
    if s is None:
        return ''
    return re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()


def _round_num(v):
    v = round(v, 3)
    return int(v) if v == int(v) else v


def parse_lwh(measurement):
    """L/W/H বের করে টেমপ্লেটের জন্য। নিয়ম:
    - PDF-এ Mm থাকলে -> ভ্যালু /10 করে Cm-এ কনভার্ট করা হয়, Unit = 'Cm'
    - PDF-এ Inch থাকলে -> ভ্যালু অপরিবর্তিত থাকে, Unit = 'Inch'
    - অন্য সব ক্ষেত্রে (Cm বা unit উল্লেখ নেই) -> ভ্যালু অপরিবর্তিত, Unit = 'Cm'
    Decimal ভ্যালুও (58.5) ঠিকভাবে ধরে।"""
    m = measurement or ''
    m_lower = m.lower()

    is_mm = bool(re.search(r'\bmm\b', m_lower))
    is_inch = 'inch' in m_lower or '"' in m

    nums = re.findall(r'(\d+\.?\d*)', m)

    def conv(n):
        if not n:
            return ''
        val = float(n)
        if is_mm:
            val = val / 10  # mm -> cm সবসময় কনভার্ট হবে
        return _round_num(val)

    l = conv(nums[0]) if len(nums) > 0 else ''
    w = conv(nums[1]) if len(nums) > 1 else ''
    h = conv(nums[2]) if len(nums) > 2 else ''

    unit = 'Inch' if is_inch else 'Cm'
    return l, w, h, unit


def get_col(row, *candidates):
    """বিভিন্ন buyer একই ডাটা ভিন্ন কলাম-নামে রাখে
    (PO No vs PONo, Color vs Gmt. Color, QTY vs Carton Qty) — 
    এটা একে একে চেক করে যেটাতে ভ্যালু পাবে সেটা রিটার্ন করবে।"""
    for name in candidates:
        if name in row:
            val = row[name]
            if str(val).strip():
                return val
    return ''


def split_prepack(value):
    parts = (value or '').split(' ')
    code = parts[0] if len(parts) > 0 else ''
    seq = parts[1] if len(parts) > 1 else ''
    return code, seq


def extract_header_info(pdf):
    """Pulls PO No, Customer (issuer), Buyer from the PO cover page.
    Works for this letterhead format regardless of numbers/dates."""
    text = pdf.pages[0].extract_text() or ''
    customer = text.split('\n')[0].strip() if text else ''

    po_match = re.search(r'PO No\.?\s*:\s*(\S+)', text)
    po_number = po_match.group(1) if po_match else ''

    buyer_match = re.search(r'Garments Buyer\s*:\s*([^\n]+?)(?:\s{2,}|\s+Merchandising|\n)', text)
    buyer = buyer_match.group(1).strip() if buyer_match else ''

    return {'po_number': po_number, 'customer': customer, 'buyer': buyer}


def extract_summary_table(pdf):
    """Page 1-এর 'Business Line' সামারি টেবিলটা ঠিক যেমন আছে তেমন বের করে আনে,
    যাতে ফাইনাল Excel-এ 'PO Summary' শীট হিসেবে দেখানো যায়। এই টেবিল না থাকলে
    ফাঁকা DataFrame রিটার্ন করে (এরর দেয় না, কারণ এটা অপশনাল তথ্য)।"""
    for page in pdf.pages:
        for t in page.extract_tables():
            if t and t[0] and t[0][0] == 'Business Line':
                header = [clean(h) for h in t[0]]
                rows = [[clean(c) for c in r] for r in t[1:]]
                return pd.DataFrame(rows, columns=header)
    return pd.DataFrame()


def extract_detail_rows(pdf):
    """Extracts every line item from the 'Purchase Order Details' table,
    across however many pages it spans. Only works for this specific
    Epyllion table layout (EWO No / Style No / ... headers).

    Returns (processed_df, raw_original_df):
    - processed_df: এর মধ্যে Length/Width/Height/MeasurementUnit/PrePack_Code/
      PrePack_Seq কলাম যোগ করা আছে ('Raw Data' শীট বানানোর জন্য)
    - raw_original_df: PDF-এ যেভাবে কলাম ছিল ঠিক সেভাবেই, কোনো যোগ-বিয়োগ ছাড়া
      ('PO Details' শীট বানানোর জন্য, যাতে PDF-এর হুবহু কাঠামো থাকে)
    """
    all_rows, header = [], None
    for page in pdf.pages:
        for t in page.extract_tables():
            if not t:
                continue
            if t[0][0] == 'Purchase Order Details':
                header = t[1]
                all_rows.extend(t[2:])
            elif t[0][0] == 'Business Line':
                continue  # এটা summary টেবিল, আলাদাভাবে extract_summary_table() দিয়ে নেওয়া হয়
            elif t[0][0] == 'EWO No':
                header = t[0]
                all_rows.extend(t[1:])
            else:
                all_rows.extend(t)

    if header is None:
        raise ValueError("এই PDF-এ পরিচিত 'Purchase Order Details' টেবিল ফরম্যাট পাওয়া যায়নি।")

    header = [clean(h) for h in header]
    rows = [r for r in all_rows if r and r[0] and str(r[0]).strip().isdigit()]
    raw_original_df = pd.DataFrame(rows, columns=header).map(clean)

    df = raw_original_df.copy()

    measurement_col = next((c for c in df.columns if 'measurement' in c.lower()), None)
    if measurement_col is None:
        raise ValueError(
            "এই PDF-এর টেবিলে 'Measurement' নামের কোনো কলাম পাওয়া যায়নি। "
            f"পাওয়া কলামগুলো: {list(df.columns)}"
        )

    df[['Length', 'Width', 'Height', 'MeasurementUnit']] = df[measurement_col].apply(
        lambda m: pd.Series(parse_lwh(m))
    )

    if 'Pre Pack' in df.columns:
        df[['PrePack_Code', 'PrePack_Seq']] = df['Pre Pack'].apply(
            lambda v: pd.Series(split_prepack(v))
        )
    else:
        df['PrePack_Code'] = ''
        df['PrePack_Seq'] = ''

    return df, raw_original_df


def to_canonical(df):
    """Converts the raw extracted DataFrame into the canonical line-item
    schema shared with the AI extractor, so builder.py can consume either."""
    line_items = []
    for _, r in df.iterrows():
        # স্পেস দিয়ে জোড়া লাগানো হচ্ছে, হাইফেন দিয়ে না (PDF-এ যেভাবে স্পেস দিয়ে আলাদা থাকে সেভাবেই)
        pack_type = f"{r['PrePack_Code']} {r['PrePack_Seq']}" if r.get('PrePack_Seq') else r.get('PrePack_Code', '')
        line_items.append({
            'item_name': r.get('Carton Nature', ''),
            'po_no': get_col(r, 'PONo', 'PO No'),
            'ewo_no': r.get('EWO No', ''),
            'style_no': r.get('Style No', ''),
            'length': r.get('Length', ''),
            'width': r.get('Width', ''),
            'height': r.get('Height', ''),
            'ply': r.get('Ply', ''),
            'qty': get_col(r, 'QTY', 'Carton Qty'),
            'pack_type': pack_type,
            'reference': '',
            'color': get_col(r, 'Gmt. Color', 'Color'),
            'size': '',
            'delivery_date': r.get('Delivery Start Date', ''),
            'measurement_unit': r.get('MeasurementUnit', 'Cm'),
        })
    return line_items


def process_pdf_rule_based(file_stream):
    """Main entry point for the rule-based (pdfplumber) extractor.
    Returns (header_info dict, canonical line_items list, raw_original_df, summary_df)."""
    with pdfplumber.open(file_stream) as pdf:
        header_info = extract_header_info(pdf)
        df, raw_original_df = extract_detail_rows(pdf)
        summary_df = extract_summary_table(pdf)
    return header_info, to_canonical(df), raw_original_df, summary_df
