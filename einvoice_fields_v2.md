# 電子發票欄位對照表 (MIG 4.1 F0401) - v2.0

## 1. einvoice_main (發票主檔)
| 欄位名稱 | 資料類型 | XML 對應 | 必要性 |
|---------|---------|---------|-------|
| id | INTEGER | - | 主鍵 |
| invoice_number | TEXT | InvoiceNumber | M |
| invoice_date | TEXT | InvoiceDate | M |
| invoice_time | TEXT | InvoiceTime | M |
| invoice_type | TEXT | InvoiceType | M |
| random_number | TEXT | RandomNumber | O |
| group_mark | TEXT | GroupMark | O |
| donate_mark | TEXT | DonateMark | M |
| print_mark | TEXT | PrintMark | M |
| **seller_identifier** | TEXT | Seller/Identifier | M |
| **seller_name** | TEXT | Seller/Name | M |
| **seller_address** | TEXT | Seller/Address | M |
| **seller_person_in_charge** | TEXT | Seller/PersonInCharge | O |
| **seller_phone** | TEXT | Seller/TelephoneNumber | O |
| **seller_fax_number** | TEXT | Seller/FacsimileNumber | O |
| **seller_email** | TEXT | Seller/EmailAddress | O |
| **seller_customer_number** | TEXT | Seller/CustomerNumber | O |
| **seller_role_remark** | TEXT | Seller/RoleRemark | O |
| seller_bank_code | TEXT | Seller/BankCode | O |
| seller_bank_account | TEXT | Seller/BankAccount | O |
| seller_remark | TEXT | - | O |
| **buyer_identifier** | TEXT | Buyer/Identifier | O |
| **buyer_name** | TEXT | Buyer/Name | O |
| **buyer_address** | TEXT | Buyer/Address | O |
| **buyer_person_in_charge** | TEXT | Buyer/PersonInCharge | O |
| **buyer_phone** | TEXT | Buyer/TelephoneNumber | O |
| **buyer_fax_number** | TEXT | Buyer/FacsimileNumber | O |
| **buyer_email** | TEXT | Buyer/EmailAddress | O |
| **buyer_customer_number** | TEXT | Buyer/CustomerNumber | O |
| **buyer_role_remark** | TEXT | Buyer/RoleRemark | O |
| **buyer_remark** | TEXT | BuyerRemark | O |
| carrier_type | TEXT | CarrierType | O |
| carrier_id1 | TEXT | CarrierId1 | O |
| carrier_id2 | TEXT | CarrierId2 | O |
| npoaban | TEXT | NPOBAN | O |
| bonded_area_confirm | TEXT | BondedAreaConfirm | O |
| customs_clearance_method | TEXT | CustomsClearanceMark | O |
| zero_tax_rate_reason | TEXT | ZeroTaxRateReason | O |
| **main_remark** | TEXT | MainRemark | O |
| **category** | TEXT | Category | O |
| **relate_number** | TEXT | RelateNumber | O |
| remark | TEXT | - | O |
| invoice_status | TEXT | - | O |
| upload_time | TEXT | - | O |
| upload_response | TEXT | - | O |
| void_reason | TEXT | - | O |
| void_time | TIMESTAMP | - | O |
| created_at | TIMESTAMP | - | O |

---

## 2. einvoice_details (發票明細)
| 欄位名稱 | 資料類型 | XML 對應 | 必要性 |
|---------|---------|---------|-------|
| id | INTEGER | - | 主鍵 |
| invoice_id | INTEGER | - | 外鍵 |
| sequence_number | INTEGER | SequenceNumber | M |
| product_id | INTEGER | - | O |
| product_name | TEXT | Description | M |
| product_specification | TEXT | ProductSpec | O |
| quantity | REAL | Quantity | M |
| unit | TEXT | Unit | O |
| unit_price | REAL | UnitPrice | M |
| amount | REAL | Amount | M |
| tax_type | TEXT | TaxType | M |
| tax_rate | REAL | TaxRate | O |
| sales_amount | REAL | - | O |
| tax_amount | REAL | - | O |
| free_amount | REAL | FreeTaxSalesAmount | O |
| zero_rate_amount | REAL | ZeroTaxSalesAmount | O |
| **remark** | TEXT | Remark | O |
| original_invoice_number | TEXT | - | O |
| original_sequence_number | INTEGER | - | O |
| original_description | TEXT | - | O |
| allowance_sequence_number | TEXT | - | O |
| barcode | TEXT | Barcode | O |
| relate_number | TEXT | RelateNumber | O |
| fund_type | TEXT | - | O |
| insurance_fee | REAL | - | O |
| service_fee | REAL | - | O |

---

## 3. einvoice_amount (發票金額匯總)
| 欄位名稱 | 資料類型 | XML 對應 | 必要性 |
|---------|---------|---------|-------|
| id | INTEGER | - | 主鍵 |
| invoice_id | INTEGER | - | 外鍵 |
| sales_amount | REAL | SalesAmount | M |
| tax_type | TEXT | TaxType | M |
| tax_rate | REAL | TaxRate | M |
| tax_amount | REAL | TaxAmount | M |
| total_amount | REAL | TotalAmount | M |
| discount_amount | REAL | DiscountAmount | O |
| free_tax_sales_amount | REAL | FreeTaxSalesAmount | M |
| zero_tax_sales_amount | REAL | ZeroTaxSalesAmount | M |
| original_currency_amount | REAL | OriginalCurrencyAmount | O |
| exchange_rate | REAL | ExchangeRate | O |
| currency | TEXT | Currency | O |
| remark | TEXT | - | O |

---

## 欄位變更說明 (v1.0 → v2.0)

### Main 新增欄位：
- ✅ seller_person_in_charge (PersonInCharge)
- ✅ seller_customer_number (CustomerNumber)
- ✅ seller_role_remark (RoleRemark)
- ✅ buyer_person_in_charge (PersonInCharge)
- ✅ buyer_customer_number (CustomerNumber)
- ✅ buyer_role_remark (RoleRemark)
- ✅ buyer_remark (BuyerRemark)
- ✅ main_remark (MainRemark)
- ✅ customs_clearance_method → CustomsClearanceMark
- ✅ category (Category)
- ✅ relate_number (RelateNumber)
- ✅ zero_tax_rate_reason (ZeroTaxRateReason)

### Details 新增欄位：
- ✅ remark (Remark)
