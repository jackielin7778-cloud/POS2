"""
POS 連鎖店系統 v2.0 - 主程式
支援：總部+分店架構、統一會員、庫存調度、權限管理
"""
import streamlit as st
import pandas as pd
from database import init_db, get_stores, get_store_by_id, verify_login, get_user_by_id, get_connection
from database import get_products, add_product, add_store_product, get_store_product, update_store_stock
from database import get_members, add_member, get_member_by_phone, get_member_by_id
from database import get_member_levels, add_member_level
from database import get_promotions, add_promotion, calculate_promotion
from database import create_sale, get_sales, get_daily_sales, get_store_revenue
from database import get_transfers, create_transfer, approve_transfer
from database import get_low_stock_products, get_top_products, get_hourly_sales
from database import check_stock_available, check_cart_stock, check_birthday_discount
from database import get_birthday_coupon, add_birthday_coupon
from database import get_holiday_templates, add_holiday_template, apply_holiday_template
from database import generate_invoice_number, create_invoice, get_invoices, get_invoice_by_number
from database import void_invoice, get_invoice_statistics, print_invoice
from database import create_einvoice, get_einvoice, get_einvoice_details, get_einvoice_amount, void_einvoice
from database import get_einvoice_statistics, generate_mig_xml, add_track_number, get_available_track

# 初始化
init_db()
st.set_page_config(page_title="POS 連鎖店系統", page_icon="🏪", layout="wide")


def calculate_price_inc_tax(price_ex_tax):
    if not price_ex_tax:
        return 0.0
    try:
        return round(float(price_ex_tax) * 1.05, 1)
    except:
        return 0.0


# ===== 登入頁面 =====
def login_page():
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h1>🏪 POS 連鎖店系統</h1>
        <h3>請登入</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("帳號")
            password = st.text_input("密碼", type="password")
            submit = st.form_submit_button("登入", type="primary")
            
            if submit:
                user = verify_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['id']
                    st.session_state.username = user['username']
                    st.session_state.user_name = user['name']
                    st.session_state.user_role = user['role']
                    st.session_state.user_store_id = user['store_id']
                    st.rerun()
                else:
                    st.error("帳號或密碼錯誤")


# ===== 側邊欄 =====
def render_sidebar():
    with st.sidebar:
        st.title(f"🏪 {st.session_state.user_name}")
        st.caption(f"角色: {st.session_state.user_role}")
        
        if st.session_state.user_store_id:
            store = get_store_by_id(st.session_state.user_store_id)
            if store:
                st.caption(f"分店: {store['name']}")
                stats = get_daily_sales(st.session_state.user_store_id)
                st.metric("今日營收", f"${stats['revenue']:,.0f}")
                st.metric("訂單數", stats['orders'])
        
        st.markdown("---")
        
        # 選單
        if st.session_state.user_role == 'admin':
            menu = ["儀表板", "分店管理", "商品管理", "會員管理", "促銷管理", "庫存調度", "銷售報表", "電子發票"]
        else:
            menu = ["收銀前台", "商品管理", "會員管理", "促銷", "我的分店", "銷售報表", "電子發票"]
        
        page = st.radio("選單", menu)
        
        st.markdown("---")
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.rerun()
    
    return page


# ===== 儀表板（總部） =====
def dashboard_page():
    st.title("📊 總部儀表板")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 取得所有分店營收
    all_revenue = get_store_revenue(days=1)
    
    total_revenue = sum(r['revenue'] for r in all_revenue) if all_revenue else 0
    total_orders = sum(r['orders'] for r in all_revenue) if all_revenue else 0
    
    col1.metric("今日總營收", f"${total_revenue:,.0f}")
    col2.metric("今日總訂單", total_orders)
    
    stores = get_stores(is_active=1)
    hq_count = len([s for s in stores if s['is_hq']])
    store_count = len([s for s in stores if not s['is_hq']])
    
    col3.metric("分店數", store_count)
    col4.metric("會員數", len(get_members()))
    
    # 各分店營收
    st.subheader("📈 各分店營收（近30天）")
    store_revenue = get_store_revenue(days=30)
    if store_revenue:
        df = pd.DataFrame(store_revenue)
        df.columns = ['分店ID', '分店名', '營收', '訂單數']
        st.dataframe(df)
    
    # 時段分析
    st.subheader("🕐 時段分析（近7天）")
    hourly = get_hourly_sales()
    if hourly:
        hours = [h['hour'] for h in hourly]
        revenues = [h['revenue'] for h in hourly]
        chart_data = pd.DataFrame({'小時': hours, '營收': revenues})
        st.bar_chart(chart_data.set_index('小時'))


# ===== 收銀前台 =====
def pos_page():
    st.title("🛒 收銀前台")
    
    store_id = st.session_state.user_store_id
    if not store_id:
        st.error("此帳號未綁定分店")
        return
    
    # 初始化購物車
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input("🔍 搜尋商品", placeholder="輸入商品名稱或條碼...")
        products = get_products(search, store_id)
        
        if products:
            cols = st.columns(4)
            for i, p in enumerate(products):
                p = dict(p)
                stock = p.get('stock', 0) or 0
                promo_text = ""
                
                # 檢查促銷
                promos = get_promotions(p['id'])
                if promos:
                    promo = dict(promos[0])
                    if promo['type'] == 'percent':
                        promo_text = f" 🔥 {int(promo['value'])}%OFF"
                
                price = p.get('store_price_inc', p['price_inc_tax'])
                
                # 庫存不足標記
                stock_status = "✅" if stock > 0 else "❌"
                
                with cols[i % 4]:
                    st.write(f"**{p['name']}**{promo_text}")
                    st.caption(f"含稅: ${price} | 庫存: {stock_status}{stock}")
                    
                    # 庫存檢查：庫存 > 0 才能加入
                    if stock > 0:
                        # 檢查購物車中已選數量
                        in_cart = 0
                        for cart_item in st.session_state.cart:
                            if cart_item['product_id'] == p['id']:
                                in_cart = cart_item['quantity']
                                break
                        
                        remaining = stock - in_cart
                        if remaining > 0:
                            if st.button(f"加入", key=f"add_{p['id']}"):
                                # 庫存再次檢查
                                check = check_stock_available(store_id, p['id'], 1)
                                if check['available']:
                                    found = False
                                    for item in st.session_state.cart:
                                        if item['product_id'] == p['id']:
                                            # 檢查總數不超過庫存
                                            if item['quantity'] < stock:
                                                item['quantity'] += 1
                                                item['subtotal'] = item['quantity'] * item['price']
                                                found = True
                                            else:
                                                st.error(f"庫存不足！最多還能加 {remaining} 件")
                                            break
                                    if not found:
                                        st.session_state.cart.append({
                                            'product_id': p['id'],
                                            'name': p['name'],
                                            'price': price,
                                            'quantity': 1,
                                            'subtotal': price
                                        })
                                    st.rerun()
                                else:
                                    st.error(check['message'])
                        else:
                            st.caption("❌ 庫存不足")
                    else:
                        st.caption("❌ 無庫存")

    with col2:
        st.markdown("### 🛒 購物車")
        
        # 會員
        st.markdown("#### 👤 會員")
        if 'selected_member' not in st.session_state:
            st.session_state.selected_member = None
        
        member_search = st.text_input("會員電話", placeholder="09xxxxxxxx", key="member_search")
        if member_search:
            member = get_member_by_phone(member_search)
            if member:
                st.session_state.selected_member = member
                # 檢查生日優惠
                birthday_coupon = get_birthday_coupon()
                if birthday_coupon:
                    st.success(f"✅ {member['name']} | 積分: {member['points']} | 🎂 生日優惠可適用")
                else:
                    st.success(f"✅ {member['name']} | 積分: {member['points']}")
            else:
                st.warning("找不到會員")
        
        if st.session_state.selected_member:
            m = st.session_state.selected_member
            if st.button("解除登入"):
                st.session_state.selected_member = None
                st.rerun()
        
        st.markdown("---")
        
        # 購物車內容
        for i, item in enumerate(st.session_state.cart):
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{item['name']}**")
            c2.write(f"x{item['quantity']}")
            
            if c3.button("❌", key=f"del_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
            
            st.write(f"💰 ${item['subtotal']}")
        
        if st.session_state.cart:
            st.markdown("---")
            subtotal = sum(item['subtotal'] for item in st.session_state.cart)
            
            # 會員折扣
            member_discount = 0
            birthday_discount = 0
            if st.session_state.selected_member:
                member = dict(st.session_state.selected_member)
                levels = get_member_levels()
                for lv in levels:
                    if lv['name'] == member['level']:
                        member_discount = subtotal * (lv['discount_percent'] / 100)
                        break
                
                # 生日優惠檢查
                birthday_discount = check_birthday_discount(member['id'], subtotal)
            
            # 促銷折扣
            promo_discount = 0
            for item in st.session_state.cart:
                promos = get_promotions(item['product_id'])
                if promos:
                    promo_discount += calculate_promotion(item, promos)
            
            discount = st.number_input("折扣", 0, int(subtotal), 0)
            total = int(subtotal - discount - promo_discount - member_discount - birthday_discount + 0.5)
            
            if member_discount > 0:
                st.success(f"👤 會員折扣: -${member_discount:.1f}")
            if birthday_discount > 0:
                st.success(f"🎂 生日折扣: -${birthday_discount:.1f}")
            if promo_discount > 0:
                st.success(f"🎉 促銷折扣: -${promo_discount:.1f}")
            
            st.markdown(f"**小計:** ${subtotal}<br>**總計:** ${total}", unsafe_allow_html=True)
            
            # 庫存最終檢查
            stock_check = check_cart_stock(store_id, st.session_state.cart)
            if not stock_check['all_available']:
                st.error("⚠️ 庫存不足：")
                for item in stock_check['items']:
                    st.write(f"  - {item['name']}: 需{item['requested']}件, 只剩{item['available']}件")
            
            cash = st.number_input("收款", min_value=0, value=total)
            change = cash - total if cash >= total else 0
            st.metric("找零", f"${change}")
            
            # 結帳按鈕（庫存不足時禁用）
            if st.button("💰 結帳", type="primary", disabled=not stock_check['all_available']):
                member_id = st.session_state.selected_member['id'] if st.session_state.selected_member else None
                member_phone = st.session_state.selected_member['phone'] if st.session_state.selected_member else ""
                member_email = st.session_state.selected_member['email'] if st.session_state.selected_member else ""
                
                # 建立銷售記錄
                sale_id = create_sale(
                    store_id=store_id,
                    member_id=member_id,
                    subtotal=subtotal,
                    discount=discount,
                    promo_discount=promo_discount,
                    member_discount=member_discount + birthday_discount,
                    total=total,
                    cash=cash,
                    change_amount=change,
                    payment_method='cash',
                    created_by=st.session_state.user_id,
                    items=st.session_state.cart
                )
                
                # 建立電子發票
                invoice_id, invoice_number = create_invoice(
                    store_id=store_id,
                    sale_id=sale_id,
                    member_id=member_id,
                    total_amount=total,
                    items=st.session_state.cart,
                    member_phone=member_phone,
                    member_email=member_email
                )
                
                st.session_state.cart = []
                st.session_state.selected_member = None
                st.success(f"✅ 交易完成！\n\n找零 ${change}\n\n🧾 發票號碼: {invoice_number}")
                st.rerun()
        
        if st.button("🗑️ 清空"):
            st.session_state.cart = []
            st.rerun()


# ===== 分店管理 =====
def stores_page():
    st.title("🏪 分店管理")
    
    if st.session_state.user_role != 'admin':
        st.error("權限不足")
        return
    
    with st.expander("➕ 新增分店"):
        with st.form("add_store"):
            name = st.text_input("分店名稱")
            code = st.text_input("代碼")
            address = st.text_input("地址")
            phone = st.text_input("電話")
            is_hq = st.checkbox("是否為總部")
            submit = st.form_submit_button("新增")
            
            if submit and name:
                from database import add_store
                add_store(name, code, address, phone, 1 if is_hq else 0)
                st.success("✅ 分店已新增")
                st.rerun()
    
    stores = get_stores()
    if stores:
        df = pd.DataFrame([{
            'ID': s['id'],
            '名稱': s['name'],
            '代碼': s['code'],
            '電話': s['phone'],
            '類型': '總部' if s['is_hq'] else '分店',
            '狀態': '啟用' if s['is_active'] else '停用'
        } for s in stores])
        st.dataframe(df)


# ===== 商品管理 =====
def products_page():
    st.title("📦 商品管理")
    
    store_id = st.session_state.user_store_id
    is_admin = st.session_state.user_role == 'admin'
    
    # 新增商品（總部）
    if is_admin:
        with st.expander("➕ 新增商品"):
            with st.form("add_product"):
                name = st.text_input("商品名稱")
                price_ex = st.number_input("售價未稅", min_value=0.0, step=10.0)
                cost = st.number_input("成本", min_value=0.0, step=10.0)
                barcode = st.text_input("條碼")
                category = st.text_input("類別")
                
                if st.form_submit_button("新增"):
                    price_inc = calculate_price_inc_tax(price_ex)
                    pid = add_product(name, price_ex, price_inc, cost, barcode, category)
                    st.success(f"✅ 商品已新增 (ID: {pid})")
                    st.rerun()
    
    # 商品列表
    products = get_products(store_id=store_id if not is_admin else None)
    
    if products:
        df = pd.DataFrame([{
            'ID': p['id'],
            '名稱': p['name'],
            '售價未稅': p.get('store_price', p['price_ex_tax']),
            '售價含稅': p.get('store_price_inc', p['price_inc_tax']),
            '庫存': p.get('stock', '-'),
            '條碼': p['barcode'],
            '類別': p['category']
        } for p in products])
        st.dataframe(df)


# ===== 會員管理 =====
def members_page():
    st.title("👥 會員管理")
    
    # 新增會員
    with st.expander("➕ 新增會員"):
        with st.form("add_member"):
            name = st.text_input("姓名")
            phone = st.text_input("電話")
            email = st.text_input("Email")
            birthday = st.date_input("生日")
            address = st.text_input("地址")
            
            if st.form_submit_button("新增"):
                member_id = add_member(name, str(phone), email, str(birthday), address)
                st.success(f"✅ 會員已新增 (ID: {member_id})")
                st.rerun()
    
    # 會員等級設定（總部）
    if st.session_state.user_role == 'admin':
        with st.expander("🏆 會員等級"):
            levels = get_member_levels()
            if levels:
                st.dataframe(pd.DataFrame(levels))
            
            with st.form("add_level"):
                name = st.text_input("等級名稱")
                min_points = st.number_input("最低積分", value=0)
                min_spent = st.number_input("最低消費", value=0.0)
                discount = st.slider("折扣%", 0, 100, 0)
                
                if st.form_submit_button("新增等級"):
                    add_member_level(name, min_points, min_spent, discount)
                    st.success("✅ 等級已新增")
                    st.rerun()
        
        # 生日優惠設定
        with st.expander("🎂 生日優惠"):
            birthday_coupon = get_birthday_coupon()
            if birthday_coupon:
                st.write("### 當前生日優惠")
                st.json(dict(birthday_coupon))
            
            with st.form("add_birthday_coupon"):
                st.write("設定生日優惠")
                name = st.text_input("優惠名稱", value="生日優惠")
                discount_percent = st.slider("折扣%", 0, 100, 10)
                discount_amount = st.number_input("或固定金額折扣", min_value=0.0, value=0.0)
                min_spent = st.number_input("最低消費", min_value=0.0, value=100.0)
                
                if st.form_submit_button("設定"):
                    add_birthday_coupon(name, discount_percent, discount_amount, min_spent)
                    st.success("✅ 生日優惠已設定")
                    st.rerun()
            
            st.caption("💡 會員生日當月及前後一個月可使用此優惠")
    
    # 會員列表
    members = get_members()
    if members:
        df = pd.DataFrame([{
            'ID': m['id'],
            '姓名': m['name'],
            '電話': m['phone'],
            '等級': m['level'],
            '積分': m['points'],
            '總消費': m['total_spent'],
            '入會日': m['created_at']
        } for m in members])
        st.dataframe(df)


# ===== 促銷管理 =====
def promotions_page():
    st.title("🏷️ 促銷管理")
    
    is_admin = st.session_state.user_role == 'admin'
    
    # 促銷列表
    promos = get_promotions(active_only=False)
    if promos:
        df = pd.DataFrame([{
            'ID': p['id'],
            '名稱': p['name'],
            '類型': p['type'],
            '值': p['value'],
            '開始': p['start_date'] or '無限制',
            '結束': p['end_date'] or '無限制',
            '狀態': '啟用' if p['is_active'] else '停用'
        } for p in promos])
        st.dataframe(df)
    
    # 新增促銷（總部）
    if is_admin:
        with st.expander("➕ 新增促銷"):
            with st.form("add_promo"):
                name = st.text_input("促銷名稱")
                promo_type = st.selectbox("類型", ['percent', 'fixed', 'bogo', 'second_discount', 'amount'])
                value = st.number_input("折扣值")
                min_amount = st.number_input("最低消費", value=0.0)
                start_date = st.date_input("開始日期")
                end_date = st.date_input("結束日期")
                
                if st.form_submit_button("新增"):
                    add_promotion(name, promo_type, value, min_amount, start_date=str(start_date), end_date=str(end_date))
                    st.success("✅ 促銷已新增")
                    st.rerun()
        
        # 節慶促銷模板
        with st.expander("🎄 節慶促銷模板"):
            templates = get_holiday_templates()
            if templates:
                st.write("### 現有模板")
                df = pd.DataFrame([{
                    'ID': t['id'],
                    '名稱': t['name'],
                    '類型': t['type'],
                    '值': t['value']
                } for t in templates])
                st.dataframe(df)
            
            with st.form("add_holiday"):
                st.write("新增節慶模板")
                name = st.text_input("模板名稱", placeholder="例如：春節特價")
                promo_type = st.selectbox("類型", ['percent', 'fixed', 'bogo', 'second_discount', 'amount'])
                value = st.number_input("折扣值")
                min_amount = st.number_input("最低消費", value=0.0)
                
                if st.form_submit_button("儲存模板"):
                    add_holiday_template(name, promo_type, value, min_amount)
                    st.success("✅ 模板已儲存")
                    st.rerun()
            
            st.write("---")
            st.write("### 套用模板")
            if templates:
                with st.form("apply_template"):
                    template_id = st.selectbox("選擇模板", 
                        [f"{t['name']} ({t['type']} - {t['value']})" for t in templates],
                        index=0)
                    start = st.date_input("開始日期")
                    end = st.date_input("結束日期")
                    
                    if st.form_submit_button("套用"):
                        idx = [t['name'] for t in templates].index(template_id.split(' (')[0])
                        apply_holiday_template(templates[idx]['id'], str(start), str(end))
                        st.success("✅ 已套用模板建立促銷")
                        st.rerun()


# ===== 庫存調度 =====
def inventory_page():
    st.title("📦 庫存調度")
    
    is_admin = st.session_state.user_role == 'admin'
    store_id = st.session_state.user_store_id
    
    # 調货申請
    with st.expander("📝 申請調貨"):
        stores = get_stores(is_active=1)
        stores_options = {s['name']: s['id'] for s in stores if s['id'] != store_id}
        
        products = get_products(store_id=store_id)
        
        with st.form("transfer"):
            to_store = st.selectbox("調至分店", list(stores_options.keys()))
            product = st.selectbox("商品", [p['name'] for p in products])
            quantity = st.number_input("數量", min_value=1, value=1)
            notes = st.text_input("備註")
            
            if st.form_submit_button("申請"):
                product_id = products[[p['name'] for p in products].index(product)]['id']
                create_transfer(store_id, stores_options[to_store], product_id, quantity, notes)
                st.success("✅ 調貨申請已提交")
                st.rerun()
    
    # 調貨記錄
    transfers = get_transfers(store_id if not is_admin else None)
    if transfers:
        df = pd.DataFrame([{
            'ID': t['id'],
            '調出': t['from_store'],
            '調入': t['to_store'],
            '商品': t['product_name'],
            '數量': t['quantity'],
            '狀態': t['status'],
            '日期': t['created_at']
        } for t in transfers])
        st.dataframe(df)
        
        # 審核（總部）
        if is_admin:
            pending = [t for t in transfers if t['status'] == 'pending']
            if pending:
                st.subheader("✅ 待審核")
                for t in pending:
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"{t['from_store']} → {t['to_store']}: {t['product_name']} x{t['quantity']}")
                    if col2.button("核准", key=f"approve_{t['id']}"):
                        approve_transfer(t['id'], st.session_state.user_id)
                        st.rerun()


# ===== 銷售報表 =====
def reports_page():
    st.title("📊 銷售報表")
    
    store_id = st.session_state.user_store_id if st.session_state.user_role != 'admin' else None
    
    # 基本統計
    sales = get_sales(store_id, limit=500)
    if sales:
        df = pd.DataFrame([{
            'ID': s['id'],
            '分店': s.get('store_name', '-'),
            '會員': s.get('member_name', '-'),
            '小計': s['subtotal'],
            '折扣': s['discount'],
            '總額': s['total'],
            '付款': s['payment_method'],
            '時間': s['created_at']
        } for s in sales])
        st.dataframe(df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("總營收", f"${df['總額'].sum():,.0f}")
        col2.metric("訂單數", len(df))
        col3.metric("平均訂單", f"${df['總額'].mean():,.0f}")
        
        # 熱銷商品
        st.subheader("🔥 熱銷商品")
        top = get_top_products(store_id)
        if top:
            st.dataframe(pd.DataFrame([{
                '商品': t['product_name'],
                '銷售數量': t['total_qty'],
                '銷售額': t['total_sales']
            } for t in top]))
        
        # 低庫存警示
        if store_id:
            st.subheader("⚠️ 低庫存警示")
            low = get_low_stock_products(store_id)
            if low:
                st.dataframe(pd.DataFrame([{
                    '商品': l['product_name'],
                    '庫存': l['stock'],
                    '警示值': l['low_stock_alert']
                } for l in low]))
            else:
                st.success("庫存正常")


# ===== 電子發票管理（MIG 4.1） =====
def invoices_page():
    st.title("🧾 電子發票管理")
    
    is_admin = st.session_state.user_role == 'admin'
    store_id = st.session_state.user_store_id
    
    # 取得店家資訊
    if store_id:
        store = get_store_by_id(store_id)
        seller_id = store['code'] if store else None
    else:
        seller_id = None
    
    # 發票統計（MIG 4.1格式）
    st.subheader("📊 發票統計")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    stats = get_einvoice_statistics(seller_id)
    col1.metric("總張數", stats['total_count'])
    col2.metric("開立金額", f"${stats['issued_amount']:,.0f}")
    col3.metric("作廢金額", f"${stats['voided_amount']:,.0f}")
    col4.metric("銷售額", f"${stats['total_sales']:,.0f}")
    col5.metric("稅額", f"${stats['total_tax']:,.0f}")
    col6.metric("免稅額", f"${stats['total_free']:,.0f}")
    
    st.markdown("---")
    
    # 字軌管理（總部）
    if is_admin:
        with st.expander("📝 字軌號碼管理"):
            st.write("### 新增字軌（政府配發）")
            with st.form("add_track"):
                c1, c2 = st.columns(2)
                with c1:
                    track1 = st.text_input("字軌1", max_chars=2, placeholder="如：AB")
                    start_num = st.number_input("起始流水號", min_value=1, value=1)
                with c2:
                    track2 = st.text_input("字軌2", max_chars=2, placeholder="如：VB")
                    end_num = st.number_input("結束流水號", min_value=1, value=10000000)
                
                issue_date = st.date_input("配發日期")
                
                if st.form_submit_button("➕ 新增字軌"):
                    add_track_number(track1.upper(), track2.upper(), start_num, end_num, str(issue_date))
                    st.success("✅ 字軌已新增")
                    st.rerun()
            
            # 現有字軌
            available = get_available_track()
            if available:
                st.info(f"📍 當前可用字軌: {available['track_code1']}{available['track_code2']}{available['current_number']:08d}")
            else:
                st.warning("⚠️ 無可用字軌，請先新增")
    
    st.markdown("---")
    
    # 查詢發票
    st.subheader("🔍 查詢發票")
    
    with st.expander("依發票號碼查詢"):
        search_num = st.text_input("輸入發票號碼", placeholder="如：AB1234567890")
        if search_num:
            invoice = get_einvoice(search_num.upper())
            if invoice:
                # 發票主檔
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**發票號碼:** {invoice['invoice_number']}")
                    st.write(f"**發票日期:** {invoice['invoice_date']}")
                    st.write(f"**發票時間:** {invoice['invoice_time']}")
                    st.write(f"**隨機碼:** {invoice['random_number']}")
                    st.write(f"**狀態:** {'✅ 已開立' if invoice['invoice_status'] == 'issued' else '❌ 已作廢'}")
                with col2:
                    st.write(f"**銷售額:** ${invoice['sales_amount']:,.0f}")
                    st.write(f"**稅額:** ${invoice['tax_amount']:,.0f}")
                    st.write(f"**免稅額:** ${invoice['free_amount']:,.0f}")
                    st.write(f"**總金額:** ${invoice['total_amount']:,.0f}")
                    tax_type_name = {'1': '應稅', '2': '零稅率', '3': '免稅', '4': '特種', '9': '混合'}
                    st.write(f"**課稅別:** {tax_type_name.get(invoice['tax_type'], invoice['tax_type'])}")
                
                # 買方資訊
                st.write("### 買方資訊")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**買方統編:** {invoice['buyer_identifier']}")
                    st.write(f"**買方名稱:** {invoice['buyer_name']}")
                with col2:
                    st.write(f"**Email:** {invoice.get('buyer_email', '-')}")
                    st.write(f"**電話:** {invoice.get('buyer_phone', '-')}")
                
                # 發票明細
                items = get_einvoice_details(invoice['id'])
                if items:
                    st.write("### 發票明細")
                    item_data = [{
                        '項次': f"{i['sequence_number']:03d}",
                        '品名': i['product_name'],
                        '數量': i['quantity'],
                        '單位': i.get('unit', '件'),
                        '單價': i['unit_price'],
                        '金額': i['amount'],
                        '課稅別': tax_type_name.get(i['tax_type'], i['tax_type'])
                    } for i in items]
                    st.dataframe(pd.DataFrame(item_data))
                
                st.markdown("---")
                
                # 操作按鈕
                c1, c2, c3 = st.columns(3)
                
                # 產生MIG XML
                if c1.button("📄 產生MIG XML"):
                    xml = generate_mig_xml(search_num.upper())
                    if xml:
                        st.code(xml, language="xml")
                
                # 列印格式預覽
                if c2.button("🖨️ 列印預覽"):
                    print_data = {
                        '發票號碼': invoice['invoice_number'],
                        '日期': invoice['invoice_date'],
                        '時間': invoice['invoice_time'],
                        '隨機碼': invoice['random_number'],
                        '賣方': invoice['seller_name'],
                        '賣方統編': invoice['seller_identifier'],
                        '買方': invoice['buyer_name'],
                        '銷售額': invoice['sales_amount'],
                        '稅額': invoice['tax_amount'],
                        '總金額': invoice['total_amount']
                    }
                    st.json(print_data)
                
                # 作廢（總部）
                if is_admin and invoice['invoice_status'] == 'issued':
                    with c3.form("void_einvoice"):
                        void_reason = st.text_input("作廢原因")
                        if st.form_submit_button("❌ 作廢"):
                            void_einvoice(search_num.upper(), void_reason)
                            st.success("✅ 發票已作廢")
                            st.rerun()
            else:
                st.warning("找不到發票，請檢查發票號碼格式")
    
    st.markdown("---")
    
    # 發票列表
    st.subheader("📋 最近發票")
    
    # 取得發票列表
    conn = get_connection()
    cursor = conn.cursor()
    if seller_id:
        cursor.execute("SELECT * FROM einvoice_main WHERE seller_identifier = ? ORDER BY created_at DESC LIMIT 50", (seller_id,))
    else:
        cursor.execute("SELECT * FROM einvoice_main ORDER BY created_at DESC LIMIT 50")
    invoices = cursor.fetchall()
    conn.close()
    
    if invoices:
        df = pd.DataFrame([{
            '發票號碼': i['invoice_number'],
            '日期': i['invoice_date'],
            '時間': i['invoice_time'],
            '銷售額': i['sales_amount'],
            '稅額': i['tax_amount'],
            '總金額': i['total_amount'],
            '課稅別': i['tax_type'],
            '狀態': '✅' if i['invoice_status'] == 'issued' else '❌'
        } for i in invoices])
        st.dataframe(df)
    else:
        st.info("尚無發票記錄")


# ===== 主程式 =====
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.cart = []

if not st.session_state.logged_in:
    login_page()
else:
    page = render_sidebar()
    
    if page == "儀表板":
        dashboard_page()
    elif page == "收銀前台":
        pos_page()
    elif page == "分店管理":
        stores_page()
    elif page == "商品管理":
        products_page()
    elif page == "會員管理":
        members_page()
    elif page == "促銷管理" or page == "促銷":
        promotions_page()
    elif page == "庫存調度":
        inventory_page()
    elif page == "我的分店":
        inventory_page()
    elif page == "銷售報表":
        reports_page()
    elif page == "電子發票":
        invoices_page()
