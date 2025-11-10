"""
Database Schemas for BizEdge (Vyapar++ prototype)

Each Pydantic model maps to a MongoDB collection (lowercased class name).
Use these for validation and persistence via database helpers.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class Party(BaseModel):
    """
    Customers/Suppliers
    Collection: "party"
    """
    name: str = Field(..., min_length=2)
    type: Literal["customer", "supplier"] = "customer"
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    credit_limit: float = 0.0
    outstanding: float = 0.0

class Product(BaseModel):
    """Inventory items. Collection: "product"""
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    hsn: Optional[str] = None
    price: float = Field(..., ge=0)
    purchase_price: Optional[float] = Field(None, ge=0)
    gst_rate: float = Field(0, ge=0)
    stock_qty: float = Field(0, ge=0)
    low_stock_threshold: float = Field(0, ge=0)
    unit: str = "pcs"

class InvoiceItem(BaseModel):
    product_id: str
    name: str
    qty: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    gst_rate: float = Field(0, ge=0)
    total: float = Field(..., ge=0)

class Invoice(BaseModel):
    """Sales/Purchase invoices. Collection: "invoice"""
    type: Literal["sale", "purchase"] = "sale"
    number: str
    party_id: str
    party_name: str
    items: List[InvoiceItem]
    subtotal: float = Field(..., ge=0)
    gst_amount: float = Field(0, ge=0)
    discount: float = Field(0, ge=0)
    round_off: float = 0
    total: float = Field(..., ge=0)
    paid: float = Field(0, ge=0)
    mode: Literal["cash", "bank", "upi", "card"] = "upi"
    notes: Optional[str] = None
    date: Optional[datetime] = None

class Transaction(BaseModel):
    """Bank/Cash ledger. Collection: "transaction"""
    type: Literal["in", "out"]
    method: Literal["cash", "bank", "upi", "card"] = "bank"
    amount: float = Field(..., gt=0)
    reference: Optional[str] = None
    tag: Optional[str] = None
    date: Optional[datetime] = None

class User(BaseModel):
    name: str
    email: str
    role: Literal["admin", "accountant", "sales"] = "sales"
    locale: str = "en"
    is_active: bool = True
