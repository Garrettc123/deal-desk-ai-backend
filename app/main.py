from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from anthropic import Anthropic
import stripe, os

app = FastAPI(title="Deal Desk AI")
client = Anthropic()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ProposalRequest(BaseModel):
    client_brief: str
    user_id: int = 1

class CheckoutRequest(BaseModel):
    plan: str
    email: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "Deal Desk AI"}

@app.post("/generate-proposal")
def generate_proposal(req: ProposalRequest):
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""You are an expert proposal writer for agencies and consultants.
            
Generate a complete professional proposal based on this client brief:
{req.client_brief}

Return a JSON object with these exact keys:
- proposal: full proposal text (markdown formatted)
- suggested_price: numeric price in USD
- risk_flags: any risks or concerns
- confidence: score 0.0-1.0

Return ONLY valid JSON."""
        }]
    )
    import json
    try:
        return json.loads(message.content[0].text)
    except:
        return {"proposal": message.content[0].text, "suggested_price": 5000, "risk_flags": "None", "confidence": 0.8}

@app.post("/create-checkout-session")
def create_checkout(req: CheckoutRequest):
    price_map = {
        "starter": os.getenv("STRIPE_PRICE_STARTER", ""),
        "pro": os.getenv("STRIPE_PRICE_PRO", ""),
        "agency": os.getenv("STRIPE_PRICE_AGENCY", "")
    }
    session = stripe.checkout.Session.create(
        customer_email=req.email,
        payment_method_types=["card"],
        line_items=[{"price": price_map.get(req.plan), "quantity": 1}],
        mode="subscription",
        success_url="https://deal-desk-ai.vercel.app/success",
        cancel_url="https://deal-desk-ai.vercel.app/pricing"
    )
    return {"checkout_url": session.url}

@app.get("/metrics")
def metrics():
    return {"requests": 0, "proposals_generated": 0, "uptime": "100%"}
