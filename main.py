import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Party, Product, Invoice, Transaction, User

app = FastAPI(title="BizEdge API", description="Vyapar++ prototype with MongoDB")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "BizEdge Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Lightweight CRUD samples to support the prototype UI

@app.post("/api/parties")
def create_party(party: Party):
    _id = create_document("party", party)
    return {"id": _id}

@app.get("/api/parties")
def list_parties():
    docs = get_documents("party")
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs

@app.post("/api/products")
def create_product(product: Product):
    _id = create_document("product", product)
    return {"id": _id}

@app.get("/api/products")
def list_products():
    docs = get_documents("product")
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs

@app.post("/api/invoices")
def create_invoice(invoice: Invoice):
    # Auto stock update (decrement on sale, increment on purchase)
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    items = invoice.items
    for item in items:
        try:
            pid = ObjectId(item.product_id)
        except Exception:
            continue
        delta = -item.qty if invoice.type == "sale" else item.qty
        db["product"].update_one({"_id": pid}, {"$inc": {"stock_qty": delta}})
    _id = create_document("invoice", invoice)
    return {"id": _id}

@app.get("/api/transactions")
def list_transactions():
    docs = get_documents("transaction")
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs

@app.post("/api/transactions")
def create_transaction(tx: Transaction):
    _id = create_document("transaction", tx)
    return {"id": _id}

# Simple insights endpoint (placeholder logic for prototype charts)
class InsightResponse(BaseModel):
    top_products: List[dict]
    low_stock: List[dict]
    totals: dict

@app.get("/api/insights", response_model=InsightResponse)
def insights():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    # Totals
    sales_total = sum(d.get("total", 0) for d in db["invoice"].find({"type": "sale"}))
    purchase_total = sum(d.get("total", 0) for d in db["invoice"].find({"type": "purchase"}))
    profit = sales_total - purchase_total
    # Low stock
    low_stock = list(db["product"].find({"$expr": {"$lte": ["$stock_qty", "$low_stock_threshold"]}}))
    for d in low_stock:
        d["id"] = str(d.pop("_id"))
    # Top products by quantity sold (simple aggregation)
    pipeline = [
        {"$match": {"type": "sale"}},
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.name", "qty": {"$sum": "$items.qty"}, "revenue": {"$sum": "$items.total"}}},
        {"$sort": {"revenue": -1}},
        {"$limit": 5}
    ]
    top_products = list(db["invoice"].aggregate(pipeline))
    for p in top_products:
        p["name"] = p.pop("_id")
    return InsightResponse(
        top_products=top_products,
        low_stock=low_stock,
        totals={"sales": sales_total, "purchase": purchase_total, "profit": profit}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
