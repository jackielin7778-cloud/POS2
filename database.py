"""
POS 連鎖店系統 v2.0 - 資料庫模組
支援：總部+分店架構、統一會員、庫存調度
"""
import sqlite3
from datetime import datetime

DB_PATH = "pos_chain.db"


def get_connection():
    """建立資料庫連線"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化資料庫"""
    conn = get_connection()
    cursor = conn.cursor()

    # ===== 分店資料表 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS stores (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        address TEXT,
        phone TEXT,
        is_ HQ INTEGER DEFAULT 0,
        parent_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES stores(id)
    )''')

    # ===== 使用者/帳號資料表 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        store_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (store_id) REFERENCES stores(id)
    )''')
    # role: 'admin' (總部), 'manager' (分店老闆), 'staff' (員工)

    # ===== 商品資料表（總部統一） =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price_ex_tax REAL DEFAULT 0,
        price_inc_tax REAL DEFAULT 0,
        cost REAL DEFAULT 0,
        barcode TEXT,
        category TEXT,
        image_url TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # ===== 分店商品資料表（各店定價/庫存） =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS store_products (
        id INTEGER PRIMARY KEY,
        store_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        price_ex_tax REAL DEFAULT 0,
        price_inc_tax REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        low_stock_alert INTEGER DEFAULT 5,
        is_active INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (store_id) REFERENCES stores(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # ===== 會員資料表（統一跨店） =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        email TEXT,
        birthday TEXT,
        address TEXT,
        level TEXT DEFAULT 'normal',
        points INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0,
        join_store_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (join_store_id) REFERENCES stores(id)
    )''')
    # level: normal, silver, gold, platinum

    # ===== 會員等級設定 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS member_levels (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        min_points INTEGER DEFAULT 0,
        min_spent REAL DEFAULT 0,
        discount_percent REAL DEFAULT 0,
        birthday_bonus INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )''')

    # ===== 會員積分記錄 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS member_points_log (
        id INTEGER PRIMARY KEY,
        member_id INTEGER NOT NULL,
        points_change INTEGER NOT NULL,
        points_balance INTEGER NOT NULL,
        reason TEXT,
        store_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (store_id) REFERENCES stores(id)
    )''')

    # ===== 促銷資料表（總部統一設定） =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS promotions (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        value REAL DEFAULT 0,
        min_amount REAL DEFAULT 0,
        min_quantity INTEGER DEFAULT 1,
        start_date TEXT,
        end_date TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # type: percent, fixed, bogo, second_discount, amount, birthday, member_only

    # ===== 促銷適用商品 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS promotion_products (
        id INTEGER PRIMARY KEY,
        promotion_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        FOREIGN KEY (promotion_id) REFERENCES promotions(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # ===== 庫存調撥資料表 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS inventory_transfers (
        id INTEGER PRIMARY KEY,
        from_store_id INTEGER NOT NULL,
        to_store_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        approved_by INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_at TIMESTAMP,
        FOREIGN KEY (from_store_id) REFERENCES stores(id),
        FOREIGN KEY (to_store_id) REFERENCES stores(id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (approved_by) REFERENCES users(id)
    )''')
    # status: pending, approved, rejected, completed

    # ===== 銷售資料表 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        store_id INTEGER NOT NULL,
        member_id INTEGER,
        subtotal REAL NOT NULL,
        discount REAL DEFAULT 0,
        promo_discount REAL DEFAULT 0,
        member_discount REAL DEFAULT 0,
        total REAL NOT NULL,
        cash REAL DEFAULT 0,
        change_amount REAL DEFAULT 0,
        payment_method TEXT DEFAULT 'cash',
        invoice_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (store_id) REFERENCES stores(id),
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')

    # ===== 銷售明細 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        discount REAL DEFAULT 0,
        subtotal REAL NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES sales(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # ===== 庫存警示設定 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock_alerts (
        id INTEGER PRIMARY KEY,
        store_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        low_stock_threshold INTEGER DEFAULT 5,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (store_id) REFERENCES stores(id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        UNIQUE(store_id, product_id)
    )''')

    # ===== 會員生日優惠券 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS birthday_coupons (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        discount_percent REAL DEFAULT 0,
        discount_amount REAL DEFAULT 0,
        min_spent REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # ===== 節慶促銷模板 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS holiday_promotions (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        value REAL DEFAULT 0,
        min_amount REAL DEFAULT 0,
        start_date TEXT,
        end_date TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # type: percent, fixed, bogo, second_discount, amount

    # ===== 電子發票資料表（符合MIG 4.1 F0401）- 三個檔案 =====

    # ===== 1. einvoice_main (發票主檔) =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_main (
        id INTEGER PRIMARY KEY,
        -- 發票辨識
        invoice_number TEXT UNIQUE NOT NULL,
        invoice_date TEXT NOT NULL,
        invoice_time TEXT NOT NULL,
        invoice_type TEXT DEFAULT '07',
        -- 發票資訊
        random_number TEXT,
        group_mark TEXT,
        donate_mark TEXT DEFAULT '0',
        print_mark TEXT DEFAULT 'N',
        -- 賣方資訊（Seller）
        seller_identifier TEXT NOT NULL,
        seller_name TEXT NOT NULL,
        seller_address TEXT,
        seller_person TEXT,
        seller_phone TEXT,
        seller_email TEXT,
        seller_fax_number TEXT,
        seller_bank_code TEXT,
        seller_bank_account TEXT,
        seller_bank_name TEXT,
        seller_business_bank_code TEXT,
        seller_remark TEXT,
        -- 賣方額外欄位
        seller_person_in_charge TEXT,
        seller_customer_number TEXT,
        seller_role_remark TEXT,
        -- 買方資訊（Buyer）
        buyer_identifier TEXT,
        buyer_name TEXT,
        buyer_address TEXT,
        buyer_person TEXT,
        buyer_phone TEXT,
        buyer_email TEXT,
        buyer_fax_number TEXT,
        -- 買方額外欄位
        buyer_person_in_charge TEXT,
        buyer_customer_number TEXT,
        buyer_role_remark TEXT,
        buyer_remark TEXT,
        -- 載具資訊（Carrier）
        carrier_type TEXT,
        carrier_id1 TEXT,
        carrier_id2 TEXT,
        -- 保稅區資訊（海關）
        npoaban TEXT,
        bonded_area_confirm TEXT,
        customs_clearance_method TEXT,
        zero_tax_rate_reason TEXT,
        -- 備註與其他
        main_remark TEXT,
        category TEXT,
        relate_number TEXT,
        remark TEXT,
        -- 狀態
        invoice_status TEXT DEFAULT 'issued',
        upload_time TEXT,
        upload_response TEXT,
        mpi_inv_m税务机关 TEXT,
        void_reason TEXT,
        void_time TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # invoice_type: 07=一般, 08=特種, 09=收據
    # donate_mark: 0=不捐贈, 1=捐贈
    # print_mark: Y=需列印, N=不列印
    # group_mark: * = 為組合商品

    # ===== 2. einvoice_details (發票明細) =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_details (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER NOT NULL,
        -- ProductItem 欄位
        sequence_number INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        product_specification TEXT,
        -- 數量單位
        quantity REAL NOT NULL,
        unit TEXT,
        unit_price REAL NOT NULL,
        -- 金額
        amount REAL NOT NULL,
        -- 課稅資訊
        tax_type TEXT DEFAULT '1',
        tax_rate REAL DEFAULT 0.05,
        sales_amount REAL DEFAULT 0,
        tax_amount REAL DEFAULT 0,
        free_amount REAL DEFAULT 0,
        zero_rate_amount REAL DEFAULT 0,
        -- 單一欄位備註
        remark TEXT,
        -- 擴展
        original_invoice_number TEXT,
        original_sequence_number INTEGER,
        original_description TEXT,
        allowance_sequence_number TEXT,
        -- 非必要欄位
        barcode TEXT,
        relate_number TEXT,
        fund_type TEXT,
        insurance_fee REAL,
        service_fee REAL,
        FOREIGN KEY (invoice_id) REFERENCES einvoice_main(id)
    )''')

    # ===== 3. einvoice_amount (發票金額匯總) =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_amount (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER UNIQUE NOT NULL,
        -- 金額欄位（InvoiceAmount）
        sales_amount REAL NOT NULL,
        tax_type TEXT DEFAULT '1',
        tax_rate REAL DEFAULT 0.05,
        tax_amount REAL NOT NULL,
        total_amount REAL NOT NULL,
        discount_amount REAL DEFAULT 0,
        -- 免稅/零稅率
        free_tax_sales_amount REAL DEFAULT 0,
        zero_tax_sales_amount REAL DEFAULT 0,
        -- 幣別（原幣）
        original_currency_amount REAL,
        exchange_rate REAL,
        currency TEXT,
        -- 備註
        remark TEXT,
        FOREIGN KEY (invoice_id) REFERENCES einvoice_main(id)
    )''')

    # ===== 4. einvoice_remarks (發票備註) =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_remarks (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER NOT NULL,
        remark_sequence INTEGER,
        remark_text TEXT,
        FOREIGN KEY (invoice_id) REFERENCES einvoice_main(id)
    )''')

    # ===== 5. 字軌號碼管理（政府配發）=====
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_track_numbers (
        id INTEGER PRIMARY KEY,
        track_code1 TEXT NOT NULL,
        track_code2 TEXT NOT NULL,
        start_number INTEGER NOT NULL,
        end_number INTEGER NOT NULL,
        current_number INTEGER NOT NULL,
        issue_date TEXT,
        is_active INTEGER DEFAULT 1,
        used_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # ===== 6. 發票上傳紀錄 =====
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_upload_log (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER NOT NULL,
        invoice_number TEXT NOT NULL,
        upload_time TEXT NOT NULL,
        response_code TEXT,
        response_message TEXT,
        mpi_inv_m税务机关 TEXT,
        FOREIGN KEY (invoice_id) REFERENCES einvoice_main(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_items (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER NOT NULL,
        sequence_number INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT,
        unit_price REAL NOT NULL,
        amount REAL NOT NULL,
        tax_type TEXT DEFAULT '1',
        tax_rate REAL DEFAULT 0.05,
        sales_amount REAL NOT NULL,
        tax_amount REAL NOT NULL,
        free_amount REAL DEFAULT 0,
        zero_rate_amount REAL DEFAULT 0,
        zero_rate_reason TEXT,
        customs_clearance TEXT,
        FOREIGN KEY (invoice_id) REFERENCES einvoice_main(id)
    )''')

    # 發票備註
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_remarks (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER NOT NULL,
        remark_text TEXT,
        FOREIGN KEY (invoice_id) REFERENCES einvoice_main(id)
    )''')

    # 字軌號碼管理（政府配發）
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_track_numbers (
        id INTEGER PRIMARY KEY,
        track_code1 TEXT NOT NULL,
        track_code2 TEXT NOT NULL,
        start_number INTEGER NOT NULL,
        end_number INTEGER NOT NULL,
        current_number INTEGER NOT NULL,
        issue_date TEXT,
        is_active INTEGER DEFAULT 1,
        used_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 發票上傳紀錄
    cursor.execute('''CREATE TABLE IF NOT EXISTS einvoice_upload_log (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER NOT NULL,
        upload_time TEXT NOT NULL,
        response_code TEXT,
        response_message TEXT,
        mpi_inv_m税务机关 TEXT,
        FOREIGN KEY (invoice_id) REFERENCES einvoice_main(id)
    )''')

    conn.commit()
    conn.close()
    print("資料庫初始化完成 (v2.0)")


# ===== 分店管理 =====

def add_store(name, code, address="", phone="", is_hq=0, parent_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stores (name, code, address, phone, is_hq, parent_id) VALUES (?, ?, ?, ?, ?, ?)",
        (name, code, address, phone, is_hq, parent_id))
    conn.commit()
    conn.close()


def get_stores(is_active=None):
    conn = get_connection()
    cursor = conn.cursor()
    if is_active is not None:
        cursor.execute("SELECT * FROM stores WHERE is_active = ? ORDER BY is_hq DESC, name", (is_active,))
    else:
        cursor.execute("SELECT * FROM stores ORDER BY is_hq DESC, name")
    stores = cursor.fetchall()
    conn.close()
    return stores


def get_store_by_id(store_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stores WHERE id = ?", (store_id,))
    store = cursor.fetchone()
    conn.close()
    return store


# ===== 使用者管理 =====

def add_user(username, password, name, role, store_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, name, role, store_id) VALUES (?, ?, ?, ?, ?)",
        (username, password, name, role, store_id))
    conn.commit()
    conn.close()


def verify_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ? AND is_active = 1", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


# ===== 商品管理 =====

def add_product(name, price_ex_tax=0, price_inc_tax=0, cost=0, barcode="", category=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price_ex_tax, price_inc_tax, cost, barcode, category) VALUES (?, ?, ?, ?, ?, ?)",
        (name, price_ex_tax, price_inc_tax, cost, barcode, category))
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id


def get_products(search="", store_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if store_id:
        # 取得分店商品（含庫存）
        cursor.execute('''
            SELECT p.*, sp.price_ex_tax as store_price, sp.price_inc_tax as store_price_inc, 
                   sp.stock, sp.low_stock_alert
            FROM products p
            LEFT JOIN store_products sp ON p.id = sp.product_id AND sp.store_id = ?
            WHERE p.is_active = 1 AND (p.name LIKE ? OR p.barcode LIKE ?)
            ORDER BY p.name
        ''', (store_id, f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM products WHERE is_active = 1 AND (name LIKE ? OR barcode LIKE ?)", 
            (f"%{search}%", f"%{search}%"))
    
    products = cursor.fetchall()
    conn.close()
    return products


def get_product_by_id(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product


# ===== 分店商品管理 =====

def add_store_product(store_id, product_id, price_ex_tax=0, price_inc_tax=0, stock=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO store_products 
        (store_id, product_id, price_ex_tax, price_inc_tax, stock) VALUES (?, ?, ?, ?, ?)''',
        (store_id, product_id, price_ex_tax, price_inc_tax, stock))
    conn.commit()
    conn.close()


def update_store_stock(store_id, product_id, quantity_change):
    """更新庫存（增減）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE store_products SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP 
        WHERE store_id = ? AND product_id = ?''', (quantity_change, store_id, product_id))
    conn.commit()
    conn.close()


def get_store_product(store_id, product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM store_products WHERE store_id = ? AND product_id = ?", 
        (store_id, product_id))
    sp = cursor.fetchone()
    conn.close()
    return sp


# ===== 會員管理 =====

def add_member(name, phone, email="", birthday="", address="", join_store_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO members (name, phone, email, birthday, address, join_store_id) 
        VALUES (?, ?, ?, ?, ?, ?)''', (name, phone, email, birthday, address, join_store_id))
    member_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return member_id


def get_members(search="", store_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if search:
        cursor.execute("SELECT * FROM members WHERE is_active = 1 AND (name LIKE ? OR phone LIKE ?)",
            (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM members WHERE is_active = 1 ORDER BY created_at DESC")
    
    members = cursor.fetchall()
    conn.close()
    return members


def get_member_by_phone(phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE phone = ? AND is_active = 1", (phone,))
    member = cursor.fetchone()
    conn.close()
    return member


def get_member_by_id(member_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
    member = cursor.fetchone()
    conn.close()
    return member


def update_member_points(member_id, points_change, reason="", store_id=None):
    """更新會員積分"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 更新積分
    cursor.execute("UPDATE members SET points = points + ? WHERE id = ?", (points_change, member_id))
    
    # 取得新餘額
    cursor.execute("SELECT points FROM members WHERE id = ?", (member_id,))
    new_balance = cursor.fetchone()[0]
    
    # 記錄log
    cursor.execute('''INSERT INTO member_points_log (member_id, points_change, points_balance, reason, store_id)
        VALUES (?, ?, ?, ?, ?)''', (member_id, points_change, new_balance, reason, store_id))
    
    # 檢查升級
    check_and_update_level(member_id)
    
    conn.commit()
    conn.close()


def check_and_update_level(member_id):
    """檢查並更新會員等級"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT points, total_spent FROM members WHERE id = ?", (member_id,))
    member = cursor.fetchone()
    if not member:
        conn.close()
        return
    
    points, total_spent = member[0], member[1]
    
    cursor.execute("SELECT name FROM member_levels WHERE is_active = 1 AND (min_points <= ? OR min_spent <= ?) ORDER BY min_points DESC, min_spent DESC LIMIT 1",
        (points, total_spent))
    new_level = cursor.fetchone()
    
    if new_level:
        cursor.execute("UPDATE members SET level = ? WHERE id = ?", (new_level[0], member_id))
    
    conn.commit()
    conn.close()


# ===== 會員等級 =====

def add_member_level(name, min_points=0, min_spent=0, discount_percent=0, birthday_bonus=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO member_levels (name, min_points, min_spent, discount_percent, birthday_bonus)
        VALUES (?, ?, ?, ?, ?)''', (name, min_points, min_spent, discount_percent, birthday_bonus))
    conn.commit()
    conn.close()


def get_member_levels():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM member_levels WHERE is_active = 1 ORDER BY min_points, min_spent")
    levels = cursor.fetchall()
    conn.close()
    return levels


# ===== 促銷管理 =====

def add_promotion(name, promo_type, value, min_amount=0, min_quantity=1, start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO promotions (name, type, value, min_amount, min_quantity, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)''', (name, promo_type, value, min_amount, min_quantity, start_date, end_date))
    promo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return promo_id


def get_promotions(product_id=None, active_only=True):
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if product_id:
        cursor.execute('''SELECT p.* FROM promotions p
            JOIN promotion_products pp ON p.id = pp.promotion_id
            WHERE pp.product_id = ? AND p.is_active = 1
            AND (p.start_date IS NULL OR p.start_date <= ?)
            AND (p.end_date IS NULL OR p.end_date >= ?)
            ORDER BY p.value DESC''', (product_id, today, today))
    else:
        if active_only:
            cursor.execute("SELECT * FROM promotions WHERE is_active = 1 AND (start_date IS NULL OR start_date <= ?) AND (end_date IS NULL OR end_date >= ?) ORDER BY created_at DESC", (today, today))
        else:
            cursor.execute("SELECT * FROM promotions ORDER BY created_at DESC")
    
    promos = cursor.fetchall()
    conn.close()
    return promos


def add_promotion_product(promotion_id, product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO promotion_products (promotion_id, product_id) VALUES (?, ?)",
        (promotion_id, product_id))
    conn.commit()
    conn.close()


def calculate_promotion(item, promotions):
    """計算促銷折扣"""
    if not promotions:
        return 0
    
    discount = 0
    qty = item['quantity']
    price = item['price']
    subtotal = item.get('subtotal', qty * price)
    
    for p in promotions:
        p = dict(p)
        
        if p['type'] == 'percent':
            discount += price * qty * (p['value'] / 100)
        elif p['type'] == 'fixed':
            discount += p['value']
        elif p['type'] == 'bogo':
            free_items = qty // 2
            discount += free_items * price
        elif p['type'] == 'second_discount':
            if qty >= 2:
                discount += price * (p['value'] / 100)
        elif p['type'] == 'amount':
            if subtotal >= p['min_amount']:
                discount += p['value']
    
    return round(discount, 2)


# ===== 庫存調拨 =====

def create_transfer(from_store_id, to_store_id, product_id, quantity, notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO inventory_transfers 
        (from_store_id, to_store_id, product_id, quantity, notes) VALUES (?, ?, ?, ?, ?)''',
        (from_store_id, to_store_id, product_id, quantity, notes))
    transfer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transfer_id


def get_transfers(store_id=None, status=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if store_id:
        cursor.execute('''SELECT t.*, 
            s1.name as from_store, s2.name as to_store,
            p.name as product_name
            FROM inventory_transfers t
            JOIN stores s1 ON t.from_store_id = s1.id
            JOIN stores s2 ON t.to_store_id = s2.id
            JOIN products p ON t.product_id = p.id
            WHERE (t.from_store_id = ? OR t.to_store_id = ?)
            ORDER BY t.created_at DESC''', (store_id, store_id))
    else:
        cursor.execute('''SELECT t.*, 
            s1.name as from_store, s2.name as to_store,
            p.name as product_name
            FROM inventory_transfers t
            JOIN stores s1 ON t.from_store_id = s1.id
            JOIN stores s2 ON t.to_store_id = s2.id
            JOIN products p ON t.product_id = p.id
            ORDER BY t.created_at DESC''')
    
    transfers = cursor.fetchall()
    conn.close()
    return transfers


def approve_transfer(transfer_id, approved_by):
    conn = get_connection()
    cursor = conn.cursor()
    
    # 取得調拨資料
    cursor.execute("SELECT * FROM inventory_transfers WHERE id = ?", (transfer_id,))
    transfer = cursor.fetchone()
    
    if transfer:
        # 扣庫存（from_store）
        cursor.execute('''UPDATE store_products SET stock = stock - ? 
            WHERE store_id = ? AND product_id = ?''',
            (transfer['quantity'], transfer['from_store_id'], transfer['product_id']))
        
        # 增庫存（to_store）
        cursor.execute('''UPDATE store_products SET stock = stock + ? 
            WHERE store_id = ? AND product_id = ?''',
            (transfer['quantity'], transfer['to_store_id'], transfer['product_id']))
        
        # 更新狀態
        cursor.execute('''UPDATE inventory_transfers 
            SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
            WHERE id = ?''', (approved_by, transfer_id))
    
    conn.commit()
    conn.close()


# ===== 銷售 =====

def create_sale(store_id, member_id, subtotal, discount, promo_discount, member_discount, total, 
                cash, change_amount, payment_method='cash', created_by=None, items=None, invoice_number=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''INSERT INTO sales 
        (store_id, member_id, subtotal, discount, promo_discount, member_discount, total, 
         cash, change_amount, payment_method, invoice_number, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (store_id, member_id, subtotal, discount, promo_discount, member_discount, total,
         cash, change_amount, payment_method, invoice_number, created_by))
    sale_id = cursor.lastrowid
    
    if items:
        for item in items:
            cursor.execute('''INSERT INTO sale_items 
                (sale_id, product_id, product_name, quantity, unit_price, discount, subtotal)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (sale_id, item['product_id'], item['name'], item['quantity'], 
                 item['price'], item.get('discount', 0), item['subtotal']))
            
            # 扣庫存
            cursor.execute('''UPDATE store_products SET stock = stock - ? 
                WHERE store_id = ? AND product_id = ?''',
                (item['quantity'], store_id, item['product_id']))
    
    # 更新會員消費
    if member_id:
        cursor.execute("UPDATE members SET total_spent = total_spent + ? WHERE id = ?", (total, member_id))
        # 積分 (消費1元=1點)
        points = int(total)
        update_member_points(member_id, points, "消費積分", store_id)
    
    conn.commit()
    conn.close()
    return sale_id


def get_sales(store_id=None, limit=100):
    conn = get_connection()
    cursor = conn.cursor()
    
    if store_id:
        cursor.execute('''SELECT s.*, st.name as store_name, m.name as member_name
            FROM sales s
            LEFT JOIN stores st ON s.store_id = st.id
            LEFT JOIN members m ON s.member_id = m.id
            WHERE s.store_id = ?
            ORDER BY s.created_at DESC LIMIT ?''', (store_id, limit))
    else:
        cursor.execute('''SELECT s.*, st.name as store_name, m.name as member_name
            FROM sales s
            LEFT JOIN stores st ON s.store_id = st.id
            LEFT JOIN members m ON s.member_id = m.id
            ORDER BY s.created_at DESC LIMIT ?''', (limit,))
    
    sales = cursor.fetchall()
    conn.close()
    return sales


def get_daily_sales(store_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if store_id:
        cursor.execute('''SELECT COUNT(*), SUM(total), SUM(discount) 
            FROM sales WHERE store_id = ? AND date(created_at) = date('now')''', (store_id,))
    else:
        cursor.execute("SELECT COUNT(*), SUM(total), SUM(discount) FROM sales WHERE date(created_at) = date('now')")
    
    result = cursor.fetchone()
    conn.close()
    return {'orders': result[0] or 0, 'revenue': result[1] or 0}


def get_store_revenue(store_id=None, days=30):
    """取得分店營收"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if store_id:
        cursor.execute('''SELECT DATE(created_at) as date, SUM(total) as revenue, COUNT(*) as orders
            FROM sales WHERE store_id = ? AND created_at >= date('now', '-' || ? || ' days')
            GROUP BY DATE(created_at) ORDER BY date''', (store_id, days))
    else:
        cursor.execute('''SELECT store_id, st.name as store_name, SUM(total) as revenue, COUNT(*) as orders
            FROM sales s JOIN stores st ON s.store_id = st.id
            WHERE s.created_at >= date('now', '-' || ? || ' days')
            GROUP BY store_id ORDER BY revenue DESC''', (days,))
    
    results = cursor.fetchall()
    conn.close()
    return results


# ===== 庫存警示 =====

def get_low_stock_products(store_id):
    """取得低庫存商品"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT sp.*, p.name as product_name, p.barcode
        FROM store_products sp
        JOIN products p ON sp.product_id = p.id
        WHERE sp.store_id = ? AND sp.stock <= sp.low_stock_alert AND sp.is_active = 1
        ORDER BY sp.stock''', (store_id,))
    products = cursor.fetchall()
    conn.close()
    return products


# ===== 統計報表 =====

def get_top_products(store_id=None, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    
    if store_id:
        cursor.execute('''SELECT product_name, SUM(quantity) as total_qty, SUM(subtotal) as total_sales
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.store_id = ?
            GROUP BY product_id ORDER BY total_sales DESC LIMIT ?''', (store_id, limit))
    else:
        cursor.execute('''SELECT product_name, SUM(quantity) as total_qty, SUM(subtotal) as total_sales
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            GROUP BY product_id ORDER BY total_sales DESC LIMIT ?''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return results


def get_hourly_sales(store_id=None):
    """時段分析"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if store_id:
        cursor.execute('''SELECT strftime('%H', created_at) as hour, COUNT(*) as orders, SUM(total) as revenue
            FROM sales WHERE store_id = ? AND created_at >= date('now', '-7 days')
            GROUP BY hour ORDER BY hour''', (store_id,))
    else:
        cursor.execute('''SELECT strftime('%H', created_at) as hour, COUNT(*) as orders, SUM(total) as revenue
            FROM sales WHERE created_at >= date('now', '-7 days')
            GROUP BY hour ORDER BY hour''')
    
    results = cursor.fetchall()
    conn.close()
    return results


# ===== 會員生日優惠 =====

def get_birthday_coupon():
    """取得當前有效的生日優惠券"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM birthday_coupons WHERE is_active = 1 LIMIT 1")
    coupon = cursor.fetchone()
    conn.close()
    return coupon


def check_birthday_discount(member_id, subtotal):
    """檢查會員是否符合生日優惠"""
    if not member_id:
        return 0
    
    member = get_member_by_id(member_id)
    if not member or not member['birthday']:
        return 0
    
    # 檢查是否在生日月份（當月或前後一個月）
    today = datetime.now()
    try:
        member_birthday = datetime.strptime(member['birthday'], '%Y-%m-%d')
        birth_month = member_birthday.month
        current_month = today.month
        
        month_diff = abs(birth_month - current_month)
        if month_diff > 1:
            if birth_month == 12 and current_month == 1:
                month_diff = 1
            elif birth_month == 1 and current_month == 12:
                month_diff = 1
        
        if month_diff > 1:
            return 0
    except:
        return 0
    
    # 取得優惠券
    coupon = get_birthday_coupon()
    if not coupon:
        return 0
    
    # 檢查最低消費
    if subtotal < coupon['min_spent']:
        return 0
    
    # 計算折扣
    discount = 0
    if coupon['discount_percent'] > 0:
        discount = subtotal * (coupon['discount_percent'] / 100)
    elif coupon['discount_amount'] > 0:
        discount = coupon['discount_amount']
    
    return round(discount, 2)


def add_birthday_coupon(name, discount_percent=0, discount_amount=0, min_spent=0):
    """新增生日優惠券"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO birthday_coupons 
        (name, discount_percent, discount_amount, min_spent) VALUES (?, ?, ?, ?)''',
        (name, discount_percent, discount_amount, min_spent))
    conn.commit()
    conn.close()


# ===== 庫存檢查 =====

def check_stock_available(store_id, product_id, quantity=1):
    """檢查庫存是否足夠"""
    sp = get_store_product(store_id, product_id)
    if not sp:
        return {'available': False, 'message': '商品不存在'}
    
    if sp['stock'] < quantity:
        return {'available': False, 'message': f'庫存不足 目前庫存: {sp["stock"]}'}
    
    return {'available': True, 'stock': sp['stock']}


def check_cart_stock(store_id, cart_items):
    """檢查購物車所有商品庫存"""
    unavailable_items = []
    
    for item in cart_items:
        result = check_stock_available(store_id, item['product_id'], item['quantity'])
        if not result['available']:
            unavailable_items.append({
                'name': item['name'],
                'requested': item['quantity'],
                'available': result.get('stock', 0),
                'message': result['message']
            })
    
    if unavailable_items:
        return {'all_available': False, 'items': unavailable_items}
    
    return {'all_available': True}


# ===== 節慶促銷模板 =====

def get_holiday_templates():
    """取得節慶促銷模板"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holiday_promotions WHERE is_active = 1 ORDER BY name")
    templates = cursor.fetchall()
    conn.close()
    return templates


def add_holiday_template(name, promo_type, value, min_amount=0):
    """新增節慶促銷模板"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO holiday_promotions (name, type, value, min_amount)
        VALUES (?, ?, ?, ?)''', (name, promo_type, value, min_amount))
    conn.commit()
    conn.close()


def apply_holiday_template(template_id, start_date=None, end_date=None):
    """套用節慶模板建立促銷"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM holiday_promotions WHERE id = ?", (template_id,))
    template = cursor.fetchone()
    
    if template:
        add_promotion(
            name=template['name'],
            promo_type=template['type'],
            value=template['value'],
            min_amount=template['min_amount'],
            start_date=start_date,
            end_date=end_date
        )
    
    conn.close()


# ===== 電子發票預留 =====

def generate_invoice_number(store_id):
    """產生發票號碼（格式：AB+店家代碼+年份月份+流水號）"""
    import random
    store = get_store_by_id(store_id)
    code = store['code'] if store else '00'
    today = datetime.now().strftime('%Y%m')
    serial = random.randint(1000, 9999)
    return f"AB{code}{today}{serial}"


# ===== 電子發票完整功能 =====

def create_invoice(store_id, sale_id, member_id, total_amount, items, 
                  member_phone="", member_email="", carrier_type="", carrier_number=""):
    """開立電子發票"""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M:%S')
    
    # 產生發票號碼
    invoice_number = generate_invoice_number(store_id)
    
    # 計算稅額（5%稅）
    tax_rate = 0.05
    tax_amount = round(total_amount * tax_rate / (1 + tax_rate), 0)
    free_amount = total_amount - tax_amount
    
    # 建立發票主檔
    cursor.execute('''INSERT INTO invoices 
        (invoice_number, sale_id, store_id, member_id, member_phone, member_email,
         total_amount, tax_amount, free_amount, invoice_status, invoice_date, invoice_time,
         carrier_type, carrier_number, pay_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?, ?, ?, ?, ?)''',
        (invoice_number, sale_id, store_id, member_id, member_phone, member_email,
         total_amount, tax_amount, free_amount, today, now_time, carrier_type, carrier_number, now_time))
    
    invoice_id = cursor.lastrowid
    
    # 建立發票明細
    sequence = 1
    for item in items:
        item_amount = item['subtotal']
        item_tax = round(item_amount * tax_rate / (1 + tax_rate), 0)
        item_free = item_amount - item_tax
        
        cursor.execute('''INSERT INTO invoice_items 
            (invoice_id, product_id, product_name, quantity, unit_price, amount, tax_type, sequence_number)
            VALUES (?, ?, ?, ?, ?, ?, 'taxed', ?)''',
            (invoice_id, item['product_id'], item['name'], item['quantity'], 
             item['price'], item_amount, sequence))
        sequence += 1
    
    conn.commit()
    conn.close()
    
    return invoice_id, invoice_number


def get_invoices(store_id=None, status=None, limit=100):
    """取得發票列表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT i.*, s.name as store_name FROM invoices i JOIN stores s ON i.store_id = s.id WHERE 1=1"
    params = []
    
    if store_id:
        query += " AND i.store_id = ?"
        params.append(store_id)
    
    if status:
        query += " AND i.invoice_status = ?"
        params.append(status)
    
    query += " ORDER BY i.created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    invoices = cursor.fetchall()
    conn.close()
    return invoices


def get_invoice_by_number(invoice_number):
    """依發票號碼查詢"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices WHERE invoice_number = ?", (invoice_number,))
    invoice = cursor.fetchone()
    conn.close()
    return invoice


def get_invoice_items(invoice_id):
    """取得發票明細"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY sequence_number", (invoice_id,))
    items = cursor.fetchall()
    conn.close()
    return items


def void_invoice(invoice_number, void_reason):
    """作廢發票"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''UPDATE invoices 
        SET invoice_status = 'voided', void_reason = ?, void_time = CURRENT_TIMESTAMP
        WHERE invoice_number = ?''', (void_reason, invoice_number))
    
    conn.commit()
    conn.close()


def get_invoice_statistics(store_id=None, start_date=None, end_date=None):
    """發票統計"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''SELECT 
        COUNT(*) as total_count,
        SUM(CASE WHEN invoice_status = 'issued' THEN total_amount ELSE 0 END) as issued_amount,
        SUM(CASE WHEN invoice_status = 'voided' THEN total_amount ELSE 0 END) as voided_amount,
        SUM(tax_amount) as total_tax
        FROM invoices WHERE 1=1'''
    params = []
    
    if store_id:
        query += " AND store_id = ?"
        params.append(store_id)
    
    if start_date:
        query += " AND invoice_date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND invoice_date <= ?"
        params.append(end_date)
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    
    return {
        'total_count': result[0] or 0,
        'issued_amount': result[1] or 0,
        'voided_amount': result[2] or 0,
        'total_tax': result[3] or 0
    }


def print_invoice(invoice_number):
    """產生發票列印格式"""
    invoice = get_invoice_by_number(invoice_number)
    if not invoice:
        return None
    
    items = get_invoice_items(invoice['id'])
    store = get_store_by_id(invoice['store_id'])
    
    # 產生列印格式
    print_data = {
        'invoice_number': invoice['invoice_number'],
        'invoice_date': invoice['invoice_date'],
        'invoice_time': invoice['invoice_time'],
        'store_name': store['name'] if store else '',
        'store_address': store['address'] if store else '',
        'items': [],
        'total_amount': invoice['total_amount'],
        'tax_amount': invoice['tax_amount'],
        'free_amount': invoice['free_amount'],
        'pay_type': invoice['pay_type'],
    }
    
    for item in items:
        print_data['items'].append({
            'name': item['product_name'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'amount': item['amount']
        })
    
    return print_data


# ===== MIG 4.1 電子發票函數 =====

def add_track_number(track_code1, track_code2, start_number, end_number, issue_date=None):
    """新增字軌號碼（政府配發）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO einvoice_track_numbers 
        (track_code1, track_code2, start_number, end_number, current_number, issue_date)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (track_code1, track_code2, start_number, end_number, start_number, issue_date))
    conn.commit()
    conn.close()


def get_available_track():
    """取得可用字軌"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM einvoice_track_numbers 
        WHERE is_active = 1 AND current_number <= end_number
        ORDER BY issue_date LIMIT 1''')
    track = cursor.fetchone()
    conn.close()
    return track


def consume_track_number():
    """使用一個字軌號碼"""
    track = get_available_track()
    if not track:
        return None
    
    invoice_number = f"{track['track_code1']}{track['track_code2']}{track['current_number']:08d}"
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE einvoice_track_numbers 
        SET current_number = current_number + 1 WHERE id = ?''', (track['id'],))
    conn.commit()
    conn.close()
    
    return invoice_number


def create_einvoice(store, buyer_info, items, tax_type='1', carrier_type='', carrier_id1='', carrier_id2='', 
                   invoice_type='07', donate_mark='0', remark='', group_mark=''):
    """建立符合MIG 4.1 F0401的電子發票（三表結構）"""
    import random
    
    conn = get_connection()
    cursor = conn.cursor()
    
    today_ymd = datetime.now().strftime('%Y%m%d')
    now_time = datetime.now().strftime('%H:%M:%S')
    
    # 取得發票號碼
    invoice_number = consume_track_number()
    if not invoice_number:
        return None, "無可用字軌號碼"
    
    # 隨機碼（4位數）
    random_number = f"{random.randint(0, 9999):04d}"
    
    # 計算金額
    total_amount = sum(item['amount'] for item in items)
    tax_rate = 0.05
    tax_amount = round(total_amount * tax_rate)
    sales_amount = total_amount - tax_amount
    free_amount = 0
    zero_rate_amount = 0
    discount_amount = 0
    
    if tax_type == '3':  # 免稅
        free_amount = total_amount
        sales_amount = 0
        tax_amount = 0
    elif tax_type == '2':  # 零稅率
        zero_rate_amount = total_amount
        sales_amount = 0
        tax_amount = 0
    
    # 賣方資訊
    seller_identifier = store.get('code') or '00000000'
    seller_name = store.get('name', '')
    seller_address = store.get('address', '')
    seller_person = store.get('contact_person', '')
    seller_phone = store.get('phone', '')
    seller_email = store.get('email', '')
    seller_fax = store.get('fax', '')
    seller_bank_code = store.get('bank_code', '')
    seller_bank_account = store.get('bank_account', '')
    
    # 買方資訊
    buyer_identifier = buyer_info.get('identifier', '0000000000')
    buyer_name = buyer_info.get('name', '消費者')
    buyer_person = buyer_info.get('person', '')
    buyer_phone = buyer_info.get('phone', '')
    buyer_email = buyer_info.get('email', '')
    buyer_address = buyer_info.get('address', '')
    buyer_fax = buyer_info.get('fax', '')
    
    # ===== 1. 建立發票主檔 (einvoice_main) =====
    cursor.execute('''INSERT INTO einvoice_main 
        (invoice_number, invoice_date, invoice_time, invoice_type, random_number, group_mark, donate_mark, print_mark,
         seller_identifier, seller_name, seller_address, seller_person, seller_phone, seller_email, seller_fax_number,
         seller_bank_code, seller_bank_account,
         buyer_identifier, buyer_name, buyer_person, buyer_phone, buyer_email, buyer_address, buyer_fax_number,
         carrier_type, carrier_id1, carrier_id2, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (invoice_number, today_ymd, now_time, invoice_type, random_number, group_mark, donate_mark, 'N',
         seller_identifier, seller_name, seller_address, seller_person, seller_phone, seller_email, seller_fax,
         seller_bank_code, seller_bank_account,
         buyer_identifier, buyer_name, buyer_person, buyer_phone, buyer_email, buyer_address, buyer_fax,
         carrier_type, carrier_id1, carrier_id2, remark))
    
    main_id = cursor.lastrowid
    
    # ===== 2. 建立發票明細 (einvoice_details) =====
    seq = 1
    for item in items:
        item_amount = item.get('amount', 0)
        item_tax = round(item_amount * tax_rate)
        item_sales = item_amount - item_tax
        item_free = 0
        item_zero = 0
        
        if tax_type == '3':
            item_free = item_amount
            item_sales = 0
            item_tax = 0
        elif tax_type == '2':
            item_zero = item_amount
            item_sales = 0
            item_tax = 0
        
        cursor.execute('''INSERT INTO einvoice_details 
            (invoice_id, sequence_number, product_id, product_name, product_specification,
             quantity, unit, unit_price, amount,
             tax_type, tax_rate, sales_amount, tax_amount, free_amount, zero_rate_amount,
             barcode, relate_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (main_id, seq, item.get('product_id'), item.get('name', ''), item.get('spec', ''),
             item.get('quantity', 1), item.get('unit', '件'), item.get('unit_price', 0), item_amount,
             tax_type, tax_rate, item_sales, item_tax, item_free, item_zero,
             item.get('barcode', ''), item.get('relate_number', '')))
        seq += 1
    
    # ===== 3. 建立發票金額匯總 (einvoice_amount) =====
    cursor.execute('''INSERT INTO einvoice_amount 
        (invoice_id, sales_amount, tax_type, tax_rate, tax_amount, total_amount, discount_amount,
         free_tax_sales_amount, zero_tax_sales_amount, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (main_id, sales_amount, tax_type, tax_rate, tax_amount, total_amount, discount_amount,
         free_amount, zero_rate_amount, remark))
    
    conn.commit()
    conn.close()
    
    return main_id, invoice_number


def get_einvoice(invoice_number):
    """查詢電子發票主檔"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM einvoice_main WHERE invoice_number = ?", (invoice_number,))
    invoice = cursor.fetchone()
    conn.close()
    return invoice


def get_einvoice_details(invoice_id):
    """查詢電子發票明細"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM einvoice_details WHERE invoice_id = ? ORDER BY sequence_number", (invoice_id,))
    details = cursor.fetchall()
    conn.close()
    return details


def get_einvoice_amount(invoice_id):
    """查詢電子發票金額"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM einvoice_amount WHERE invoice_id = ?", (invoice_id,))
    amount = cursor.fetchone()
    conn.close()
    return amount


def get_einvoice(invoice_number):
    """查詢電子發票"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM einvoice_main WHERE invoice_number = ?", (invoice_number,))
    invoice = cursor.fetchone()
    conn.close()
    return invoice


def get_einvoice_items(invoice_id):
    """取得發票明細（兼容舊版）"""
    return get_einvoice_details(invoice_id)


def void_einvoice(invoice_number, void_reason):
    """作廢電子發票"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE einvoice_main 
        SET invoice_status = 'voided', void_reason = ?, void_time = CURRENT_TIMESTAMP
        WHERE invoice_number = ?''', (void_reason, invoice_number))
    conn.commit()
    conn.close()


def get_einvoice_statistics(store_id=None, start_date=None, end_date=None):
    """電子發票統計（MIG 4.1 F0401三表結構）"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''SELECT 
        COUNT(*) as total_count,
        SUM(CASE WHEN m.invoice_status = 'issued' THEN a.total_amount ELSE 0 END) as issued_amount,
        SUM(CASE WHEN m.invoice_status = 'voided' THEN a.total_amount ELSE 0 END) as voided_amount,
        SUM(a.sales_amount) as total_sales,
        SUM(a.tax_amount) as total_tax,
        SUM(a.free_tax_sales_amount) as total_free,
        SUM(a.zero_tax_sales_amount) as total_zero
        FROM einvoice_main m
        JOIN einvoice_amount a ON m.id = a.invoice_id
        WHERE 1=1'''
    params = []
    
    if store_id:
        query += " AND m.seller_identifier = ?"
        params.append(store_id)
    
    if start_date:
        query += " AND m.invoice_date >= ?"
        params.append(start_date.replace('-', ''))
    
    if end_date:
        query += " AND m.invoice_date <= ?"
        params.append(end_date.replace('-', ''))
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    
    return {
        'total_count': result[0] or 0,
        'issued_amount': result[1] or 0,
        'voided_amount': result[2] or 0,
        'total_sales': result[3] or 0,
        'total_tax': result[4] or 0,
        'total_free': result[5] or 0,
        'total_zero': result[6] or 0
    }


def generate_mig_xml(invoice_number):
    """產生MIG 4.1 F0401 XML格式（三表結構）"""
    invoice = get_einvoice(invoice_number)
    if not invoice:
        return None
    
    # 轉換 Row 為 dict
    invoice = dict(invoice)
    details = [dict(d) for d in get_einvoice_details(invoice['id'])]
    amount = dict(get_einvoice_amount(invoice['id'])) if get_einvoice_amount(invoice['id']) else None
    
    # 產生F0401 XML
    xml = f'''<?xml version="1.0" encoding="utf-8"?>
<Invoice xsi:schemaLocation="urn:GEINV:eInvoiceMessage:F0401:4.1 F0401.xsd" xmlns="urn:GEINV:eInvoiceMessage:F0401:4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Main>
    <InvoiceNumber>{invoice['invoice_number']}</InvoiceNumber>
    <InvoiceDate>{invoice['invoice_date']}</InvoiceDate>
    <InvoiceTime>{invoice['invoice_time']}</InvoiceTime>
    <InvoiceType>{invoice.get('invoice_type', '07')}</InvoiceType>
    <RandomNumber>{invoice.get('random_number', '')}</RandomNumber>
    <GroupMark>{invoice.get('group_mark', '')}</GroupMark>
    <DonateMark>{invoice.get('donate_mark', '0')}</DonateMark>
    <Seller>
      <Identifier>{invoice['seller_identifier']}</Identifier>
      <Name><![CDATA[{invoice['seller_name']}]]></Name>
      <Address>{invoice.get('seller_address', '')}</Address>
      <PersonInCharge>{invoice.get('seller_person_in_charge', '')}</PersonInCharge>
      <TelephoneNumber>{invoice.get('seller_phone', '')}</TelephoneNumber>
      <FacsimileNumber>{invoice.get('seller_fax_number', '')}</FacsimileNumber>
      <EmailAddress>{invoice.get('seller_email', '')}</EmailAddress>
      <CustomerNumber>{invoice.get('seller_customer_number', '')}</CustomerNumber>
      <RoleRemark>{invoice.get('seller_role_remark', '')}</RoleRemark>
      <BankCode>{invoice.get('seller_bank_code', '')}</BankCode>
      <BankAccount>{invoice.get('seller_bank_account', '')}</BankAccount>
    </Seller>
    <Buyer>
      <Identifier>{invoice.get('buyer_identifier', '')}</Identifier>
      <Name><![CDATA[{invoice.get('buyer_name', '')}]]></Name>
      <Address>{invoice.get('buyer_address', '')}</Address>
      <PersonInCharge>{invoice.get('buyer_person_in_charge', '')}</PersonInCharge>
      <TelephoneNumber>{invoice.get('buyer_phone', '')}</TelephoneNumber>
      <FacsimileNumber>{invoice.get('buyer_fax_number', '')}</FacsimileNumber>
      <EmailAddress>{invoice.get('buyer_email', '')}</EmailAddress>
      <CustomerNumber>{invoice.get('buyer_customer_number', '')}</CustomerNumber>
      <RoleRemark>{invoice.get('buyer_role_remark', '')}</RoleRemark>
    </Buyer>
    <BuyerRemark>{invoice.get('buyer_remark', '')}</BuyerRemark>
    <MainRemark>{invoice.get('main_remark', '')}</MainRemark>
    <CustomsClearanceMark>{invoice.get('customs_clearance_method', '')}</CustomsClearanceMark>
    <Category>{invoice.get('category', '')}</Category>
    <RelateNumber>{invoice.get('relate_number', '')}</RelateNumber>
    <CarrierType>{invoice.get('carrier_type', '')}</CarrierType>
    <CarrierId1>{invoice.get('carrier_id1', '')}</CarrierId1>
    <CarrierId2>{invoice.get('carrier_id2', '')}</CarrierId2>
    <PrintMark>{invoice.get('print_mark', 'N')}</PrintMark>
    <NPOBAN>{invoice.get('npoaban', '')}</NPOBAN>
    <BondedAreaConfirm>{invoice.get('bonded_area_confirm', '')}</BondedAreaConfirm>
    <ZeroTaxRateReason>{invoice.get('zero_tax_rate_reason', '')}</ZeroTaxRateReason>
  </Main>
  <Details>
'''
    
    for item in details:
        xml += f'''    <ProductItem>
      <SequenceNumber>{item['sequence_number']:03d}</SequenceNumber>
      <Description><![CDATA[{item['product_name']}]]></Description>
      <Quantity>{item['quantity']}</Quantity>
      <Unit>{item.get('unit', '件')}</Unit>
      <UnitPrice>{item['unit_price']}</UnitPrice>
      <TaxType>{item['tax_type']}</TaxType>
      <Amount>{item['amount']}</Amount>
      <Remark>{item.get('remark', '')}</Remark>
      <RelateNumber>{item.get('relate_number', '')}</RelateNumber>
    </ProductItem>
'''
    
    # Amount (Summary)
    if amount:
        xml += f'''  </Details>
  <Amount>
    <SalesAmount>{amount['sales_amount']}</SalesAmount>
    <FreeTaxSalesAmount>{amount.get('free_tax_sales_amount', 0)}</FreeTaxSalesAmount>
    <ZeroTaxSalesAmount>{amount.get('zero_tax_sales_amount', 0)}</ZeroTaxSalesAmount>
    <TaxAmount>{amount['tax_amount']}</TaxAmount>
    <TaxType>{amount['tax_type']}</TaxType>
    <TaxRate>{amount['tax_rate']}</TaxRate>
    <TotalAmount>{amount['total_amount']}</TotalAmount>
    <DiscountAmount>{amount.get('discount_amount', 0)}</DiscountAmount>
    <OriginalCurrencyAmount>{amount.get('original_currency_amount', '')}</OriginalCurrencyAmount>
    <ExchangeRate>{amount.get('exchange_rate', '')}</ExchangeRate>
    <Currency>{amount.get('currency', '')}</Currency>
  </Amount>
</Invoice>'''
    
    return xml


# ===== Streamlit 介面所需的簡化函數 =====

def create_store(name, code, address="", phone=""):
    """簡化的門市建立函數"""
    return add_store(name, code, address, phone)


def create_product(name, barcode, price, cost, category=""):
    """簡化的商品建立函數"""
    return add_product(name, price*0.9, price, cost, barcode, category)


def create_member(name, phone, email=""):
    """簡化的會員建立函數"""
    return add_member(name, phone, email)


def add_points(member_id, points, reason=""):
    """新增積分"""
    return update_member_points(member_id, points, reason)


def use_points(member_id, points, reason=""):
    """使用積分"""
    return update_member_points(member_id, -points, reason)


def get_inventory(store_id=None):
    """取得庫存列表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if store_id:
        cursor.execute('''SELECT sp.*, p.name as product_name, p.barcode, s.name as store_name
            FROM store_products sp
            JOIN products p ON sp.product_id = p.id
            JOIN stores s ON sp.store_id = s.id
            WHERE sp.store_id = ?
            ORDER BY p.name''', (store_id,))
    else:
        cursor.execute('''SELECT sp.*, p.name as product_name, p.barcode, s.name as store_name
            FROM store_products sp
            JOIN products p ON sp.product_id = p.id
            JOIN stores s ON sp.store_id = s.id
            ORDER BY s.name, p.name''')
    
    results = cursor.fetchall()
    conn.close()
    return results


def transfer_inventory(from_store_id, to_store_id, product_id, quantity):
    """庫存調拨"""
    return create_transfer(from_store_id, to_store_id, product_id, quantity)


def create_promotion(name, discount_type, discount_value):
    """簡化的促銷建立"""
    return add_promotion(name, discount_type, discount_value)

