import json
import os
from dotenv import load_dotenv
import gocardless_pro
from gocardless_pro import Client
import hmac
import hashlib


def init_gocardless_client():
    return Client(
        access_token=os.getenv("GC_ACCESS_TOKEN"),
        environment="sandbox"
    )

def create_redirect_flow(client, quote_id, user_data, success_url):
    """Create redirect flow for payment authorization"""
    name_parts = user_data['full_name'].split(' ', 1)
    return client.redirect_flows.create(params={
        "description": f"Insurance Payment - Quote #{quote_id}",
        "session_token": quote_id,
        "success_redirect_url": success_url,
        "prefilled_customer": {
            "email": user_data['email'],
            "given_name": name_parts[0],
            "family_name": name_parts[1] if len(name_parts) > 1 else "Customer",
            "phone_number": user_data.get('phone', '')
        }
    })


def create_payment(client, mandate_id, amount, currency, metadata):
    """Create payment from mandate"""
    return client.payments.create(params={
        "amount": int(amount * 100),  # Convert to pence/cents
        "currency": currency,
        "links": {"mandate": mandate_id},
        "metadata": metadata
    })


def verify_webhook_signature(request, secret):
    """Verify webhook signature for security"""
    received_signature = request.headers.get('Webhook-Signature')
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        request.data,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(received_signature, computed_signature)



def complete_redirect_flow(client, flow_id, session_token):
    """Complete redirect flow and get mandate ID"""
    flow = client.redirect_flows.complete(flow_id, params={"session_token": session_token})
    return flow.links.mandate