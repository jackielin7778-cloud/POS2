# 電子發票欄位對照表 (MIG 4.1 F0401)

## 1. einvoice_main (發票主檔)
| 欄位名稱 | 資料類型 | 說明 | 必要 |
|---------|---------|------|-----|
| id | INTEGER | 主鍵 | 是 |
| invoice_number | TEXT | 發票號碼 | 是 |
| invoice_date | TEXT | 發票日期(YYYYMMDD) | 是 |
| invoice_time | TEXT | 發票時間(HHMMSS) | 是 |
| invoice_type | TEXT | 發票類型(07/08/09) | 否 |
| random_number | TEXT | 隨機碼 | 否 |
| group_mark | TEXT | 組合商品註記(*) | 否 |
| donate_mark | TEXT | 捐贈註記(0/1) | 否 |
| print_mark | TEXT | 列印標記(Y/N) | 否 |
| seller_identifier | TEXT | 賣方統編 | 是 |
| seller_name | TEXT | 賣方名稱 | 是 |
| seller_address | TEXT | 賣方地址 | 否 |
| seller_person | TEXT | 賣方負責人 | 否 |
| seller_phone | TEXT | 賣方電話 | 否 |
| seller_email | TEXT | 賣方Email | 否 |
| seller_fax_number | TEXT | 賣方傳真號碼 | 否 |
| seller_bank_code | TEXT | 賣方銀行代碼 | 否 |
| seller_bank_account | TEXT | 賣方銀行帳號 | 否 |
| seller_bank_name | TEXT | 賣方銀行名稱 | 否 |
| seller_business_bank_code | TEXT | 營業人銀行代碼 | 否 |
| seller_remark | TEXT | 賣方備註 | 否 |
| buyer_identifier | TEXT | 買方統編 | 否 |
| buyer_name | TEXT | 買方名稱 | 否 |
| buyer_address | TEXT | 買方地址 | 否 |
| buyer_person | TEXT | 買方代表人 | 否 |
| buyer_phone | TEXT | 買方電話 | 否 |
| buyer_email | TEXT | 買方Email | 否 |
| buyer_fax_number | TEXT | 買方傳真號碼 | 否 |
| carrier_type | TEXT | 載具類型 | 否 |
| carrier_id1 | TEXT | 載具編號1 | 否 |
| carrier_id2 | TEXT | 載具編號2 | 否 |
| npoaban | TEXT | 非加值型營業人稅籍編號 | 否 |
| bonded_area_confirm | TEXT | 保稅區確認 | 否 |
| customs_clearance_method | TEXT | 通關方式註記 | 否 |
| zero_tax_sales_message | TEXT | 零稅率原因說明 | 否 |
| remark | TEXT | 備註 | 否 |
| invoice_status | TEXT | 發票狀態 | 否 |
| upload_time | TEXT | 上傳時間 | 否 |
| upload_response | TEXT | 上傳回應 | 否 |
| mpi_inv_m税务机关 | TEXT | 發票所屬税务机关 | 否 |
| void_reason | TEXT | 作廢原因 | 否 |
| void_time | TIMESTAMP | 作廢時間 | 否 |
| created_at | TIMESTAMP | 建立時間 | 否 |

---

## 2. einvoice_details (發票明細)
| 欄位名稱 | 資料類型 | 說明 | 必要 |
|---------|---------|------|-----|
| id | INTEGER | 主鍵 | 是 |
| invoice_id | INTEGER | 發票主檔ID | 是 |
| sequence_number | INTEGER | 項次(3位數) | 是 |
| product_id | INTEGER | 商品ID | 否 |
| product_name | TEXT | 品名 | 是 |
| product_specification | TEXT | 規格 | 否 |
| quantity | REAL | 數量 | 是 |
| unit | TEXT | 單位 | 否 |
| unit_price | REAL | 單價 | 是 |
| amount | REAL | 金額 | 是 |
| tax_type | TEXT | 課稅別(1/2/3/4/9) | 否 |
| tax_rate | REAL | 稅率 | 否 |
| sales_amount | REAL | 銷售額 | 否 |
| tax_amount | REAL | 稅額 | 否 |
| free_amount | REAL | 免稅金額 | 否 |
| zero_rate_amount | REAL | 零稅率金額 | 否 |
| original_invoice_number | TEXT | 原始發票號碼 | 否 |
| original_sequence_number | INTEGER | 原始項次 | 否 |
| original_description | TEXT | 原始說明 | 否 |
| allowance_sequence_number | TEXT | 折讓項次 | 否 |
| barcode | TEXT | 條碼 | 否 |
| relate_number | TEXT | 關聯號 | 否 |
| fund_type | TEXT | 基金類型 | 否 |
| insurance_fee | REAL | 保險費 | 否 |
| service_fee | REAL | 服務費 | 否 |

---

## 3. einvoice_amount (發票金額匯總)
| 欄位名稱 | 資料類型 | 說明 | 必要 |
|---------|---------|------|-----|
| id | INTEGER | 主鍵 | 是 |
| invoice_id | INTEGER | 發票主檔ID | 是 |
| sales_amount | REAL | 銷售額 | 是 |
| tax_type | TEXT | 課稅別 | 否 |
| tax_rate | REAL | 稅率 | 否 |
| tax_amount | REAL | 稅額 | 是 |
| total_amount | REAL | 總金額 | 是 |
| discount_amount | REAL | 折扣金額 | 否 |
| free_tax_sales_amount | REAL | 免稅銷售額合計 | 否 |
| zero_tax_sales_amount | REAL | 零稅率銷售額合計 | 否 |
| original_currency_amount | REAL | 原幣金額 | 否 |
| exchange_rate | REAL | 匯率 | 否 |
| currency | TEXT | 幣別 | 否 |
| remark | TEXT | 備註 | 否 |

---

## 4. XML 輸出對照

### Main 區塊
```
<Main>
  <InvoiceNumber></InvoiceNumber>
  <InvoiceDate></InvoiceDate>
  <InvoiceTime></InvoiceTime>
  <InvoiceType></InvoiceType>
  <RandomNumber></RandomNumber>
  <GroupMark></GroupMark>
  <DonateMark></DonateMark>
  <Seller>
    <Identifier></Identifier>
    <Name></Name>
    <Address></Address>
    <Person></Person>
    <PhoneNumber></PhoneNumber>
    <EmailAddress></EmailAddress>
    <FaxNumber></FaxNumber>
    <BankCode></BankCode>
    <BankAccount></BankAccount>
  </Seller>
  <Buyer>
    <Identifier></Identifier>
    <Name></Name>
    <Address></Address>
    <Person></Person>
    <PhoneNumber></PhoneNumber>
    <EmailAddress></EmailAddress>
    <FaxNumber></FaxNumber>
  </Buyer>
  <CarrierType></CarrierType>
  <CarrierId1></CarrierId1>
  <CarrierId2></CarrierId2>
  <PrintMark></PrintMark>
  <NPOBAN></NPOBAN>
  <BondedAreaConfirm></BondedAreaConfirm>
</Main>
```

### Details 區塊
```
<Details>
  <ProductItem>
    <SequenceNumber></SequenceNumber>
    <ProductName></ProductName>
    <ProductSpec></ProductSpec>
    <Quantity></Quantity>
    <Unit></Unit>
    <UnitPrice></UnitPrice>
    <Amount></Amount>
    <TaxType></TaxType>
    <TaxRate></TaxRate>
    <SalesAmount></SalesAmount>
    <TaxAmount></TaxAmount>
    <FreeTaxSalesAmount></FreeTaxSalesAmount>
    <ZeroTaxSalesAmount></ZeroTaxSalesAmount>
    <Barcode></Barcode>
    <RelateNumber></RelateNumber>
  </ProductItem>
</Details>
```

### Amount 區塊
```
<Amount>
  <SalesAmount></SalesAmount>
  <FreeTaxSalesAmount></FreeTaxSalesAmount>
  <ZeroTaxSalesAmount></ZeroTaxSalesAmount>
  <TaxAmount></TaxAmount>
  <TaxType></TaxType>
  <TaxRate></TaxRate>
  <TotalAmount></TotalAmount>
  <DiscountAmount></DiscountAmount>
  <OriginalCurrencyAmount></OriginalCurrencyAmount>
  <ExchangeRate></ExchangeRate>
  <Currency></Currency>
</Amount>
```
