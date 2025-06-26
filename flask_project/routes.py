from flask import Blueprint, render_template, request, session, redirect, current_app, jsonify

from flask_project.gocardless import init_gocardless_client, create_redirect_flow, complete_redirect_flow, create_payment, verify_webhook_signature
import os
import time 
from flask_project.utils import get_quote_data
# Initialize GoCardless client
gc_client = init_gocardless_client()
bp= Blueprint('main',__name__)

@bp.route('/')
def home():
    return render_template('index.html')


@bp.route('/api/customers', methods=['GET', 'POST'])
def handle_customers():
    if request.method == 'GET':
        email=request.args.get('email')
        if not email:
            return jsonify({'message':'Email parameter is required'}), 400
        return gc_service.get_customer_by_email(email)



@bp.route('/get-quote', methods=['POST'])
def get_quote():
    try:
        # Get user data from form
        user_data = {
            "full_name": request.form.get('full_name', ''),
            "email": request.form.get('email', ''),
            "phone": request.form.get('phone', ''),
            "insurance_type": request.form.get('insurance_type', ''),
            "date_of_birth": request.form.get('dob', '1990-01-01')  # Added for payment
        }
        
        # Validate required fields
        if not all([user_data['full_name'], user_data['email'], user_data['insurance_type']]):
            return render_template('error.html', 
                                  message="Full name, email and insurance type are required"), 400
        
        # Store in session
        session['user_data'] = user_data
        
        # Simulate SchemeServe response (will be replaced with real integration later)
        quote_data = {
            "quote_id": f"SIM-{int(time.time())}",
            "premium": 85.00,
            "currency": "GBP",
            "valid_until": "2025-12-31",
            "details": f"{user_data['insurance_type'].capitalize()} Insurance Policy",
            "product_code": "CAR-001" if user_data['insurance_type'] == 'auto' else "GEN-001"
        }
        
        # Store quote in session
        session['quote_data'] = quote_data
        
        # Prepare data for template
        processed_quote = {
            "quote_id": quote_data['quote_id'],
            "premium": quote_data['premium'],
            "currency": quote_data['currency'],
            "valid_until": quote_data['valid_until'],
            "details": quote_data['details']
        }
        
        return render_template('quote_result.html', 
                               user=user_data, 
                               quote=processed_quote)
    
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in get_quote: {str(e)}")
        return render_template('error.html',
                              message="An unexpected error occurred. Please contact support."), 500
  

@bp.route('/initiate-payment', methods=['POST'])
def initiate_payment():
    try:
        quote_data = session.get('quote_data', {})
        user_data = session.get('user_data', {})
        
        redirect_flow = create_redirect_flow(
            gc_client,
            quote_data['quote_id'],
            user_data,
            os.getenv("GC_SUCCESS_URL", "http://localhost:5000/payment-success")
        )
        
        session['redirect_flow_id'] = redirect_flow.id
        return redirect(redirect_flow.redirect_url)
    
    except Exception as e:
        logger.exception(f"Payment initiation failed: {str(e)}")
        return render_template('error.html', 
                              message="Could not initiate payment. Please try again."), 500

@bp.route('/payment-success', methods=['GET'])
def payment_success():
    try:
        flow_id = session.get('redirect_flow_id')
        if not flow_id:
            return redirect('/')
            
        mandate_id = complete_redirect_flow(
            gc_client,
            flow_id,
            request.args.get('session_token')
        )
        
        quote_data = session.get('quote_data', {})
        payment = create_payment(
            gc_client,
            mandate_id,
            quote_data['premium'],
            quote_data.get('currency', 'GBP'),
            {
                "quote_id": quote_data['quote_id'],
                "insurance_type": session['user_data']['insurance_type']
            }
        )
        
        session['payment_data'] = {
            "payment_id": payment.id,
            "mandate_id": mandate_id,
            "amount": payment.amount / 100,
            "currency": payment.currency,
            "status": payment.status,
            "created_at": payment.created_at
        }
        
        return render_template('payment_success.html', 
                               payment=session['payment_data'],
                               quote=quote_data)
    
    except Exception as e:
        logger.exception(f"Payment completion failed: {str(e)}")
        return render_template('error.html', 
                              message="Payment processing failed. Please contact support."), 500

@bp.route('/gocardless-webhooks', methods=['POST'])
def gocardless_webhooks():
    try:
        secret = os.getenv("GC_WEBHOOK_SECRET", "")
        if not secret or not verify_webhook_signature(request, secret):
            return "Invalid signature", 401
        
        # Process events (simplified)
        for event in request.json.get('events', []):
            resource_type = event['resource_type']
            action = event['action']
            resource_id = event['links'][resource_type]
            logger.info(f"Webhook: {resource_type}.{action} - {resource_id}")
            
            # Handle payment events
            if resource_type == 'payments' and action == 'confirmed':
                payment = gc_client.payments.get(resource_id)
                logger.info(f"Payment confirmed: {payment.id}")
                
        return "", 204
    
    except Exception as e:
        logger.exception(f"Webhook processing failed: {str(e)}")
        return "Server error", 500
    

