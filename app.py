import io
import os
import tempfile

from flask import Flask, request, render_template, send_file, jsonify

from extractor import process_pdf_rule_based
from builder import build_combined_excel, validate_line_items
from validators import validate_customer, validate_buyer, validate_po_number
from date_logic import get_default_delivery_date, validate_manual_delivery_date
from config import CUSTOMERS, BUYERS, DELIVERY_ADDRESSES

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB


@app.route('/')
def index():
    return render_template(
        'index.html',
        customers=CUSTOMERS,
        buyers=BUYERS,
        delivery_addresses=DELIVERY_ADDRESSES,
    )


@app.route('/process', methods=['POST'])
def process():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'PDF ফাইল পাওয়া যায়নি'}), 400

    pdf_file = request.files['pdf_file']
    if pdf_file.filename == '':
        return jsonify({'error': 'ফাইল সিলেক্ট করা হয়নি'}), 400

    customer_type = request.form.get('customer_type', 'IN-HOUSE').strip()
    customer_name = request.form.get('customer_name', '').strip()
    buyer_name = request.form.get('buyer_name', '').strip()
    po_number_override = request.form.get('po_number', '').strip()
    delivery_mode = request.form.get('delivery_mode', 'auto').strip()
    delivery_date_manual = request.form.get('delivery_date', '').strip()
    delivery_address = request.form.get('delivery_address', '').strip()
    method = request.form.get('method', 'rule_based')

    # --- Buyer বাধ্যতামূলক ও case-sensitive লিস্ট-ম্যাচ ---
    buyer_error = validate_buyer(buyer_name)
    if buyer_error:
        return jsonify({'error': buyer_error}), 422

    # --- Customer (দিলে) case-sensitive লিস্ট-ম্যাচ ---
    customer_error = validate_customer(customer_type, customer_name)
    if customer_error:
        return jsonify({'error': customer_error}), 422

    # --- Delivery Date: manual হলে আগেই ভ্যালিডেট করে নেওয়া (PDF পড়ার আগে, সময় বাঁচাতে) ---
    if delivery_mode == 'manual':
        is_valid, err, parsed_date = validate_manual_delivery_date(delivery_date_manual)
        if not is_valid:
            return jsonify({'error': err}), 422
        delivery_date_final = parsed_date.isoformat()
    else:
        delivery_date_final = get_default_delivery_date().isoformat()

    pdf_bytes_raw = pdf_file.read()

    # --- Method: Rule-Based (active) ---
    if method == 'rule_based':
        try:
            header_info, line_items, raw_df, summary_df = process_pdf_rule_based(io.BytesIO(pdf_bytes_raw))
        except Exception as e:
            return jsonify({'error': f'PDF পড়তে সমস্যা হয়েছে (rule-based): {str(e)}'}), 422

    # --- Method: AI-Based (coming soon, not wired in yet) ---
    elif method == 'ai_based':
        return jsonify({
            'error': 'AI-Based মেথড এখনো চালু করা হয়নি। শীঘ্রই আসছে — আপাতত Rule-Based ব্যবহার করুন।'
        }), 501

    else:
        return jsonify({'error': f'অজানা মেথড: {method}'}), 400

    if not line_items:
        return jsonify({'error': 'কোনো লাইন-আইটেম পাওয়া যায়নি এই PDF থেকে'}), 422

    # --- PO Number (দিলে) আপলোড করা PDF-এর PO Number-এর সাথে মিল থাকতে হবে ---
    po_error = validate_po_number(po_number_override, header_info.get('po_number', ''))
    if po_error:
        return jsonify({'error': po_error}), 422

    warnings = validate_line_items(line_items)
    base_name = os.path.splitext(pdf_file.filename)[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, f'{base_name}_Output.xlsx')
        build_combined_excel(
            line_items, header_info, out_path,
            profile=customer_type,
            customer_override=customer_name or None,
            buyer_override=buyer_name or None,
            po_override=po_number_override or None,
            delivery_date=delivery_date_final,
            delivery_address=delivery_address,
            raw_df=raw_df,
            summary_df=summary_df,
            warnings=warnings,
        )
        with open(out_path, 'rb') as f:
            file_bytes = f.read()

    buf = io.BytesIO(file_bytes)
    response = send_file(
        buf,
        as_attachment=True,
        download_name=f'{base_name}_Output.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response.headers['X-Warning-Count'] = str(len(warnings))
    return response


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
