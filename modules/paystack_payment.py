"""
Paystack Payment Integration Module
International payment processing via Paystack
"""

import os
import logging
import requests
from typing import Dict
import hashlib
import hmac

logger = logging.getLogger(__name__)


class PaystackPayment:
    """Paystack payment integration for international payments"""
    
    API_URL = 'https://api.paystack.co'
    
    def __init__(self):
        """Initialize Paystack payment handler"""
        self.secret_key = os.getenv('PAYSTACK_SECRET_KEY')
        self.public_key = os.getenv('PAYSTACK_PUBLIC_KEY')
        self.webhook_secret = os.getenv('PAYSTACK_WEBHOOK_SECRET')
        
        if not self.secret_key:
            logger.warning("PAYSTACK_SECRET_KEY not found in environment")
    
    def initialize_transaction(self, email: str, amount: int, reference: str, 
                              metadata: Dict = None) -> Dict:
        """
        Initialize Paystack transaction
        
        Args:
            email: Customer email address
            amount: Amount in kobo (100 = 1 KSH, so multiply by 100)
            reference: Unique transaction reference
            metadata: Additional transaction data
            
        Returns:
            Dict with initialization response
        """
        try:
            if not self.secret_key:
                return {
                    'success': False,
                    'error': 'Paystack not configured'
                }
            
            headers = {
                'Authorization': f'Bearer {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            # Amount should be in kobo (multiply by 100)
            amount_kobo = amount * 100
            
            payload = {
                'email': email,
                'amount': amount_kobo,
                'reference': reference,
                'currency': 'KES',  # Kenyan Shillings
                'callback_url': f'https://cybertech-security-scanner.fly.dev/api/payment/paystack-callback',
                'metadata': metadata or {}
            }
            
            response = requests.post(
                f'{self.API_URL}/transaction/initialize',
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('status'):
                return {
                    'success': True,
                    'authorization_url': result['data']['authorization_url'],
                    'access_code': result['data']['access_code'],
                    'reference': result['data']['reference']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error')
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack API error: {str(e)}")
            return {
                'success': False,
                'error': f'Paystack API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Paystack error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_transaction(self, reference: str) -> Dict:
        """
        Verify Paystack transaction
        
        Args:
            reference: Transaction reference
            
        Returns:
            Dict with verification result
        """
        try:
            if not self.secret_key:
                return {'success': False, 'error': 'Paystack not configured'}
            
            headers = {
                'Authorization': f'Bearer {self.secret_key}'
            }
            
            response = requests.get(
                f'{self.API_URL}/transaction/verify/{reference}',
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('status') and result.get('data', {}).get('status') == 'success':
                data = result['data']
                return {
                    'success': True,
                    'verified': True,
                    'amount': data.get('amount') / 100,  # Convert from kobo to KSH
                    'reference': data.get('reference'),
                    'customer_email': data.get('customer', {}).get('email'),
                    'paid_at': data.get('paid_at'),
                    'metadata': data.get('metadata', {})
                }
            else:
                return {
                    'success': True,
                    'verified': False,
                    'message': 'Payment not completed'
                }
            
        except Exception as e:
            logger.error(f"Error verifying transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_webhook(self, request_data: bytes, signature: str) -> bool:
        """
        Validate Paystack webhook signature
        
        Args:
            request_data: Raw request body
            signature: X-Paystack-Signature header
            
        Returns:
            bool: True if signature is valid
        """
        try:
            if not self.webhook_secret:
                logger.warning("Webhook secret not configured")
                return False
            
            hash_obj = hmac.new(
                self.webhook_secret.encode('utf-8'),
                msg=request_data,
                digestmod=hashlib.sha512
            )
            
            expected_signature = hash_obj.hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error validating webhook: {str(e)}")
            return False

