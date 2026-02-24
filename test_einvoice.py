#!/usr/bin/env python3
"""
電子發票 MIG 4.1 F0401 測試程式
測試所有欄位是否符合規格
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, create_einvoice, generate_mig_xml, get_einvoice, get_einvoice_details, get_einvoice_amount, get_connection

def setup_test_data():
    """設定測試資料"""
    print("設定測試資料...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 新增字軌號碼
    cursor.execute('''INSERT OR IGNORE INTO einvoice_track_numbers 
        (track_code1, track_code2, start_number, end_number, current_number, is_active)
        VALUES (?, ?, ?, ?, ?, ?)''',
        ('AB', '1234', 1, 10000, 1, 1))
    
    conn.commit()
    conn.close()
    print("✓ 測試資料設定完成")

def test_einvoice_creation():
    """測試電子發票建立"""
    print("\n" + "=" * 60)
    print("測試 1: 建立電子發票 (含所有欄位)")
    print("=" * 60)
    
    # 門市資料
    store = {
        'code': '12345678',
        'name': '測試商行有限公司',
        'address': '台北市測試區測試路100號',
        'contact_person': '王小明',
        'phone': '02-12345678',
        'email': 'seller@test.com',
        'fax': '02-12345679',
        'bank_code': '012',
        'bank_account': '1234567890',
    }
    
    # 買方資料
    buyer_info = {
        'identifier': '87654321',
        'name': '測試買家股份有限公司',
        'person': '李小華',
        'phone': '02-98765432',
        'email': 'buyer@test.com',
        'address': '新北市測試區測試街200號',
        'fax': '02-98765433',
    }
    
    # 商品明細
    items = [
        {
            'product_id': 1,
            'name': '測試商品A',
            'spec': '規格A',
            'quantity': 2,
            'unit': '個',
            'unit_price': 100,
            'amount': 200,
            'barcode': '471011022',
            'relate_number': '',
        },
        {
            'product_id': 2,
            'name': '測試商品B (免稅)',
            'spec': '規格B',
            'quantity': 1,
            'unit': '件',
            'unit_price': 50,
            'amount': 50,
            'barcode': '',
            'relate_number': '',
        },
    ]
    
    # 建立發票
    invoice_id, invoice_number = create_einvoice(
        store=store,
        buyer_info=buyer_info,
        items=items,
        tax_type='1',  # 應稅
        carrier_type='3J0002',
        carrier_id1='TEST1234',
        carrier_id2='',
        invoice_type='07',
        donate_mark='0',
        remark='這是測試發票',
        group_mark='',
    )
    
    if invoice_id:
        print(f"✓ 發票建立成功，ID: {invoice_id}, 號碼: {invoice_number}")
    else:
        print(f"✗ 發票建立失敗: {invoice_number}")
        return None
    
    # 更新額外欄位
    conn = get_connection()
    cursor = conn.cursor()
    
    # 更新 Main 額外欄位
    cursor.execute('''
        UPDATE einvoice_main SET
            seller_person_in_charge = ?,
            seller_customer_number = ?,
            seller_role_remark = ?,
            buyer_person_in_charge = ?,
            buyer_customer_number = ?,
            buyer_role_remark = ?,
            buyer_remark = ?,
            main_remark = ?,
            customs_clearance_method = ?,
            category = ?,
            relate_number = ?,
            bonded_area_confirm = ?,
            zero_tax_rate_reason = ?
        WHERE id = ?
    ''', (
        '王小明', 'CUST001', '賣方備註',
        '李小華', 'CUST002', '買家備註',
        '1',  # 買受人註記
        '這是主備註',
        '1',  # 通關方式
        '01', # 沖帳別
        'REL20260124001',
        '',   # 保稅區
        '',   # 零稅率原因
        invoice_id
    ))
    
    # 更新 Details 額外欄位
    cursor.execute('''
        UPDATE einvoice_details SET
            remark = ?
        WHERE invoice_id = ? AND sequence_number = 1
    ''', ('商品A備註', invoice_id))
    
    # 更新 Amount 欄位
    cursor.execute('''
        UPDATE einvoice_amount SET
            free_tax_sales_amount = ?,
            zero_tax_sales_amount = ?
        WHERE invoice_id = ?
    ''', (50, 0, invoice_id))
    
    conn.commit()
    conn.close()
    
    print("✓ 額外欄位更新完成")
    
    return invoice_number

def test_xml_generation(invoice_number):
    """測試 XML 產生"""
    print("\n" + "=" * 60)
    print("測試 2: 產生 MIG XML")
    print("=" * 60)
    
    if not invoice_number:
        print("✗ 無發票號碼")
        return None
    
    xml = generate_mig_xml(invoice_number)
    
    if xml:
        print("✓ XML 產生成功")
        print("\n--- XML 內容 ---\n")
        print(xml)
        return xml
    else:
        print("✗ XML 產生失敗")
        return None

def test_xml_fields(xml):
    """驗證 XML 欄位"""
    print("\n" + "=" * 60)
    print("測試 3: 驗證 XML 欄位")
    print("=" * 60)
    
    if not xml:
        print("✗ 無 XML 可驗證")
        return
    
    # 檢查必要欄位
    required_fields = [
        'InvoiceNumber', 'InvoiceDate', 'InvoiceTime', 'InvoiceType',
        '<Identifier>', '<Name>', '<Address>',
        'DonateMark', 'PrintMark',
        'Quantity', 'TaxType', 'Amount', 'SequenceNumber',
        'SalesAmount', 'TaxAmount', 'TotalAmount',
        'FreeTaxSalesAmount', 'ZeroTaxSalesAmount', 'TaxRate'
    ]
    
    # 檢查新增欄位
    new_fields = [
        'PersonInCharge',
        'CustomerNumber',
        'RoleRemark',
        'BuyerRemark',
        'MainRemark',
        'CustomsClearanceMark',
        'Category',
        'RelateNumber',
        'ZeroTaxRateReason',
        '<Remark>',  # ProductItem Remark
    ]
    
    print("必要欄位檢查:")
    all_ok = True
    for field in required_fields:
        if field in xml:
            print(f"  ✓ {field}")
        else:
            print(f"  ✗ {field} (缺失)")
            all_ok = False
    
    print("\n新增欄位檢查:")
    for field in new_fields:
        if field in xml:
            print(f"  ✓ {field}")
        else:
            print(f"  ✗ {field} (缺失)")
            all_ok = False
    
    if all_ok:
        print("\n✓ 所有欄位檢查通過!")
    else:
        print("\n✗ 部分欄位缺失，請修正")
    
    return all_ok

def test_einvoice_query(invoice_number):
    """測試發票查詢"""
    print("\n" + "=" * 60)
    print("測試 4: 發票查詢")
    print("=" * 60)
    
    invoice = get_einvoice(invoice_number)
    if invoice:
        invoice = dict(invoice)  # 轉換 Row 為 dict
        print(f"✓ 發票查詢成功")
        print(f"  發票號碼: {invoice['invoice_number']}")
        print(f"  賣方: {invoice['seller_name']}")
        print(f"  買方: {invoice.get('buyer_name', 'N/A')}")
        print(f"  賣方負責人: {invoice.get('seller_person_in_charge', 'N/A')}")
        print(f"  買方負責人: {invoice.get('buyer_person_in_charge', 'N/A')}")
    else:
        print("✗ 發票查詢失敗")
    
    if invoice:
        details = get_einvoice_details(invoice['id'])
        print(f"✓ 明細筆數: {len(details)}")
        for d in details:
            d = dict(d) if hasattr(d, 'keys') else d
            print(f"    - {d['product_name']}: 備註={d.get('remark', 'N/A')}")
        
        amount = get_einvoice_amount(invoice['id'])
        if amount:
            amount = dict(amount) if hasattr(amount, 'keys') else amount
            print(f"✓ 金額: 總額={amount['total_amount']}, 免稅={amount.get('free_tax_sales_amount', 0)}")

def main():
    """主測試流程"""
    print("\n" + "=" * 60)
    print("  電子發票 MIG 4.1 F0401 測試開始")
    print("=" * 60 + "\n")
    
    # 初始化資料庫
    init_db()
    print("✓ 資料庫初始化完成\n")
    
    # 設定測試資料
    setup_test_data()
    
    # 執行測試
    try:
        invoice_number = test_einvoice_creation()
        xml = test_xml_generation(invoice_number)
        test_xml_fields(xml)
        test_einvoice_query(invoice_number)
        
        print("\n" + "=" * 60)
        print("  所有測試完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
