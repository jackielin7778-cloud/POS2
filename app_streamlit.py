# POS 連鎖店系統 v2.0
# Streamlit Web 介面

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_db, get_connection,
    get_stores, create_store, get_store_by_id,
    get_products, create_product, get_product_by_id,
    create_einvoice, generate_mig_xml, get_einvoice, get_einvoice_details, get_einvoice_amount,
    get_members, create_member, add_points, use_points,
    get_promotions, create_promotion,
    get_inventory, transfer_inventory,
    get_all_tracks, add_track_number,
    get_all_einvoices
)

# 頁面設定
st.set_page_config(
    page_title="POS 連鎖店系統 v2.0",
    page_icon="🏪",
    layout="wide"
)

# 樣式
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .sidebar .sidebar-content {
        background: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# 初始化
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# 側邊欄
st.sidebar.title("🏪 POS 系統")
page = st.sidebar.selectbox(
    "選單",
    ["首頁", "門市管理", "商品管理", "銷售 POS", "電子發票", "會員管理", "促銷管理", "庫存管理"]
)

# ===== 首頁 =====
if page == "首頁":
    st.title("🏪 POS 連鎖店系統 v2.0")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("門市數", "3")
    with col2:
        st.metric("商品數", "25")
    with col3:
        st.metric("會員數", "150")
    with col4:
        st.metric("今日發票", "42")
    
    st.markdown("### 功能選單")
    st.info("請由側邊欄選擇功能")

# ===== 門市管理 =====
elif page == "門市管理":
    st.title("🏪 門市管理")
    
    tab1, tab2 = st.tabs(["門市列表", "新增門市"])
    
    with tab1:
        stores = get_stores()
        for store in stores:
            with st.expander(f"{store['name']} ({store['code']})"):
                st.write(f"**地址:** {store.get('address', 'N/A')}")
                st.write(f"**電話:** {store.get('phone', 'N/A')}")
                st.write(f"**狀態:** {'啟用' if store.get('is_active') else '停用'}")
    
    with tab2:
        with st.form("new_store"):
            name = st.text_input("門市名稱")
            code = st.text_input("統編/代碼")
            address = st.text_input("地址")
            phone = st.text_input("電話")
            submit = st.form_submit_button("新增")
            
            if submit and name and code:
                create_store(name, code, address, phone)
                st.success("門市建立成功!")
                st.rerun()

# ===== 商品管理 =====
elif page == "商品管理":
    st.title("📦 商品管理")
    
    tab1, tab2 = st.tabs(["商品列表", "新增商品"])
    
    with tab1:
        products = get_products()
        for p in products:
            with st.expander(f"{p['name']} - NT${p.get('price_inc_tax', 0)}"):
                st.write(f"**條碼:** {p.get('barcode', 'N/A')}")
                st.write(f"**類別:** {p.get('category', 'N/A')}")
                st.write(f"**成本:** NT${p.get('cost', 0)}")
    
    with tab2:
        with st.form("new_product"):
            name = st.text_input("商品名稱")
            barcode = st.text_input("條碼")
            price = st.number_input("含稅價格", min_value=0, value=0)
            cost = st.number_input("成本", min_value=0, value=0)
            category = st.selectbox("類別", ["飲料", "食品", "文具", "其他"])
            submit = st.form_submit_button("新增")
            
            if submit and name:
                create_product(name, barcode, price, cost, category)
                st.success("商品建立成功!")
                st.rerun()

# ===== 銷售 POS =====
elif page == "銷售 POS":
    st.title("💳 銷售 POS")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("選擇商品")
        products = get_products()
        
        if 'cart' not in st.session_state:
            st.session_state.cart = []
        
        # 商品網格
        cols = st.columns(3)
        for i, p in enumerate(products):
            with cols[i % 3]:
                if st.button(f"{p['name']}\nNT${p.get('price_inc_tax', 0)}", key=f"prod_{p['id']}"):
                    st.session_state.cart.append({
                        'product_id': p['id'],
                        'name': p['name'],
                        'price': p.get('price_inc_tax', 0),
                        'quantity': 1
                    })
        
        # 購物車
        st.subheader("購物車")
        if st.session_state.cart:
            total = 0
            for idx, item in enumerate(st.session_state.cart):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"{item['name']} x{item['quantity']}")
                c2.write(f"NT${item['price'] * item['quantity']}")
                if c3.button("🗑️", key=f"del_{idx}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()
                total += item['price'] * item['quantity']
            
            st.markdown(f"**合計: NT${total}**")
            
            if st.button("清空購物車"):
                st.session_state.cart = []
                st.rerun()
        else:
            st.info("購物車是空的")
    
    with col2:
        st.subheader("結帳資訊")
        
        with st.form("checkout"):
            store = st.selectbox("門市", ["總部", "門市A", "門市B"])
            
            buyer_type = st.radio("買方類型", ["消費者", "公司行號"])
            
            buyer_info = {}
            if buyer_type == "公司行號":
                buyer_info['identifier'] = st.text_input("統一編號")
                buyer_info['name'] = st.text_input("公司名稱")
            else:
                buyer_info['identifier'] = '0000000000'
                buyer_info['name'] = '消費者'
            
            member = st.selectbox("會員", ["無", "會員A", "會員B"])
            
            carrier = st.selectbox("載具", ["無", "手機條碼", "自然人憑證"])
            
            submit = st.form_submit_button("開立發票")
            
            if submit and st.session_state.cart:
                # 建立發票
                store_info = {'code': '12345678', 'name': store, 'address': '', 'phone': ''}
                items = [{'product_id': c['product_id'], 'name': c['name'], 'quantity': c['quantity'], 
                          'unit_price': c['price'], 'amount': c['price'] * c['quantity']} for c in st.session_state.cart]
                
                invoice_id, invoice_number = create_einvoice(store_info, buyer_info, items)
                
                if invoice_id:
                    st.success(f"發票開立成功!\n發票號碼: {invoice_number}")
                    st.session_state.cart = []
                    st.rerun()
                else:
                    st.error(f"發票開立失敗: {invoice_number}")

# ===== 電子發票 =====
elif page == "電子發票":
    st.title("🧾 電子發票管理")
    
    tab1, tab2, tab3, tab4 = st.tabs(["發票查詢", "已開發票", "發票統計", "字軌管理"])
    
    with tab1:
        invoice_num = st.text_input("發票號碼")
        if st.button("查詢"):
            invoice = get_einvoice(invoice_num)
            if invoice:
                st.success(f"發票號碼: {invoice['invoice_number']}")
                st.write(f"賣方: {invoice['seller_name']}")
                st.write(f"買方: {invoice.get('buyer_name', 'N/A')}")
                st.write(f"日期: {invoice['invoice_date']}")
                
                details = get_einvoice_details(invoice['id'])
                st.write("### 明細")
                for d in details:
                    st.write(f"- {d['product_name']} x{d['quantity']} = NT${d['amount']}")
                
                amount = get_einvoice_amount(invoice['id'])
                if amount:
                    st.write(f"**總金額: NT${amount['total_amount']}**")
                
                # 顯示 XML
                xml = generate_mig_xml(invoice_num)
                if xml:
                    with st.expander("MIG XML"):
                        st.code(xml, language="xml")
            else:
                st.error("找不到發票")
    
    with tab2:
        st.subheader("📋 已開發票列表")
        einvoices = get_all_einvoices()
        
        if einvoices:
            for inv in einvoices:
                amount = get_einvoice_amount(inv['id'])
                total = amount['total_amount'] if amount else 0
                with st.expander(f"{inv['invoice_number']} - NT${total}"):
                    st.write(f"**日期:** {inv['invoice_date']}")
                    st.write(f"**時間:** {inv['invoice_time']}")
                    st.write(f"**賣方:** {inv['seller_name']}")
                    st.write(f"**買方:** {inv.get('buyer_name', 'N/A')}")
                    st.write(f"**隨機碼:** {inv.get('random_number', 'N/A')}")
                    
                    details = get_einvoice_details(inv['id'])
                    if details:
                        st.write("### 明細")
                        for d in details:
                            st.write(f"- {d['product_name']} x{d['quantity']} = NT${d['amount']}")
                    
                    # 顯示 XML
                    xml = generate_mig_xml(inv['invoice_number'])
                    if xml:
                        with st.expander("MIG XML"):
                            st.code(xml, language="xml")
        else:
            st.info("尚無已開發票")
        st.caption("請至「銷售 POS」開立新發票")
    
    with tab3:
        st.subheader("發票統計")
        from database import get_einvoice_statistics
        stats = get_einvoice_statistics()
        col1, col2, col3 = st.columns(3)
        col1.metric("總發票數", stats['total_count'])
        col2.metric("已開立金額", f"NT${stats['issued_amount']}")
        col3.metric("作廢金額", f"NT${stats['voided_amount']}")
    
    with tab4:
        st.subheader("📋 字軌管理")
        
        # 顯示現有字軌
        tracks = get_all_tracks()
        if tracks:
            st.write("### 現有字軌")
            for t in tracks:
                with st.expander(f"{t['track_code1']}{t['track_code2']} - {t['current_number']}/{t['end_number']}"):
                    st.write(f"起始號碼: {t['start_number']}")
                    st.write(f"結束號碼: {t['end_number']}")
                    st.write(f"目前號碼: {t['current_number']}")
                    st.write(f"發放日期: {t.get('issue_date', 'N/A')}")
                    st.write(f"狀態: {'啟用' if t.get('is_active') else '停用'}")
        else:
            st.warning("尚無字軌資料")
        
        # 新增字軌表單
        st.write("### 新增字軌")
        with st.form("add_track"):
            col1, col2 = st.columns(2)
            track_code1 = col1.text_input("字軌代號1", value="AB")
            track_code2 = col2.text_input("字軌代號2", value="01")
            start_num = st.number_input("起始號碼", min_value=1, value=1)
            end_num = st.number_input("結束號碼", min_value=1, value=1000)
            issue_date = st.date_input("發放日期")
            
            if st.form_submit_button("新增字軌"):
                add_track_number(track_code1, track_code2, start_num, end_num, str(issue_date))
                st.success("字軌新增成功！請重新整理頁面")
                st.rerun()

# ===== 會員管理 =====
elif page == "會員管理":
    st.title("👤 會員管理")
    
    tab1, tab2 = st.tabs(["會員列表", "新增會員"])
    
    with tab1:
        members = get_members()
        for m in members:
            with st.expander(f"{m['name']} - {m['phone']}"):
                st.write(f"**等級:** {m.get('level', '普通')}")
                st.write(f"**累積消費:** NT${m.get('total_spent', 0)}")
                st.write(f"**點數:** {m.get('points', 0)}")
    
    with tab2:
        with st.form("new_member"):
            name = st.text_input("姓名")
            phone = st.text_input("電話")
            email = st.text_input("Email")
            submit = st.form_submit_button("新增")
            
            if submit and name and phone:
                create_member(name, phone, email)
                st.success("會員建立成功!")
                st.rerun()

# ===== 促銷管理 =====
elif page == "促銷管理":
    st.title("🏷️ 促銷管理")
    
    tab1, tab2 = st.tabs(["促銷列表", "新增促銷"])
    
    with tab1:
        promos = get_promotions()
        for p in promos:
            with st.expander(f"{p['name']}"):
                st.write(f"**折扣:** {p.get('discount_type', '')} {p.get('discount_value', 0)}")
                st.write(f"**期間:** {p.get('start_date', '')} ~ {p.get('end_date', '')}")
    
    with tab2:
        with st.form("new_promo"):
            name = st.text_input("促銷名稱")
            discount_type = st.selectbox("折扣類型", ["percentage", "fixed"])
            discount_value = st.number_input("折扣值", min_value=0, value=0)
            submit = st.form_submit_button("新增")
            
            if submit and name:
                create_promotion(name, discount_type, discount_value)
                st.success("促銷建立成功!")
                st.rerun()

# ===== 庫存管理 =====
elif page == "庫存管理":
    st.title("📊 庫存管理")
    
    tab1, tab2 = st.tabs(["庫存查詢", "庫存調拨"])
    
    with tab1:
        st.subheader("各店庫存")
        inventory = get_inventory()
        st.dataframe(inventory)
    
    with tab2:
        st.info("庫存調拨功能")
