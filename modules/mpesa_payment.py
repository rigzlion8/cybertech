"""
M-Pesa Payment Integration Module
Integrates with Safaricom Daraja API for STK Push payments
"""

import os
import logging
import requests
import base64
from datetime import datetime
from typing import Dict, Optional
import json

logger = logging.getLogger(__name__)


class MPesaPayment:
    """M-Pesa Daraja API integration for payments"""
    
    # Daraja API URLs
    SANDBOX_BASE_URL = 'https://sandbox.safaricom.co.ke'
    PRODUCTION_BASE_URL = 'https://api.safaricom.co.ke'
    
    def __init__(self, environment='sandbox'):
        """
        Initialize M-Pesa payment handler
        
        Args:
            environment: 'sandbox' or 'production'
        """
        self.environment = environment
        self.base_url = self.SANDBOX_BASE_URL if environment == 'sandbox' else self.PRODUCTION_BASE_URL
        
        # Load credentials from environment
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.business_short_code = os.getenv('MPESA_SHORTCODE')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL', 'https://cybertech-security-scanner.fly.dev/api/payment/callback')
        
        self.access_token = None
        self.token_expiry = None
        
    def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth access token from Daraja API
        
        Returns:
            Access token string or None
        """
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expiry:
                if datetime.now() < self.token_expiry:
                    return self.access_token
            
            # Generate new token
            auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Create basic auth header
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            auth_bytes = auth_string.encode('ascii')
            base64_bytes = base64.b64encode(auth_bytes)
            base64_string = base64_bytes.decode('ascii')
            
            headers = {
                'Authorization': f'Basic {base64_string}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(auth_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            # Token expires in 3600 seconds (1 hour)
            from datetime import timedelta
            self.token_expiry = datetime.now() + timedelta(seconds=3500)
            
            logger.info("M-Pesa access token obtained successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get M-Pesa access token: {str(e)}")
            return None
    
    def initiate_stk_push(self, phone_number: str, amount: int, account_reference: str, 
                          transaction_desc: str = "CyberTech Payment") -> Dict:
        """
        Initiate STK Push payment request
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge (in KSH)
            account_reference: Reference for the transaction (e.g., scan_id)
            transaction_desc: Description of the transaction
            
        Returns:
            Dict with payment initiation response
        """
        try:
            access_token = self._get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to authenticate with M-Pesa'
                }
            
            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Generate password
            password_string = f"{self.business_short_code}{self.passkey}{timestamp}"
            password_bytes = password_string.encode('ascii')
            password_base64 = base64.b64encode(password_bytes).decode('ascii')
            
            # STK Push URL
            stk_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.business_short_code,
                'Password': password_base64,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': amount,
                'PartyA': phone_number,
                'PartyB': self.business_short_code,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }
            
            logger.info(f"Initiating STK push for {phone_number}, Amount: {amount} KSH")
            
            response = requests.post(stk_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'merchant_request_id': result.get('MerchantRequestID'),
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'response_code': result.get('ResponseCode'),
                    'response_description': result.get('ResponseDescription'),
                    'customer_message': result.get('CustomerMessage')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('errorMessage', 'Unknown error'),
                    'response_code': result.get('ResponseCode')
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"M-Pesa API error: {str(e)}")
            return {
                'success': False,
                'error': f'M-Pesa API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"M-Pesa payment error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_transaction_status(self, checkout_request_id: str) -> Dict:
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id: CheckoutRequestID from STK push response
            
        Returns:
            Dict with transaction status
        """
        try:
            access_token = self._get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to authenticate with M-Pesa'
                }
            
            # Generate timestamp and password
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_string = f"{self.business_short_code}{self.passkey}{timestamp}"
            password_bytes = password_string.encode('ascii')
            password_base64 = base64.b64encode(password_bytes).decode('ascii')
            
            # Query URL
            query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.business_short_code,
                'Password': password_base64,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            response = requests.post(query_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'result_code': result.get('ResultCode'),
                'result_desc': result.get('ResultDesc'),
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error querying transaction status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_callback(self, callback_data: Dict) -> Dict:
        """
        Validate and parse M-Pesa callback data
        
        Args:
            callback_data: Callback data from M-Pesa
            
        Returns:
            Dict with parsed payment information
        """
        try:
            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            result_code = stk_callback.get('ResultCode')
            
            if result_code == 0:
                # Payment successful
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                payment_data = {}
                for item in items:
                    name = item.get('Name')
                    value = item.get('Value')
                    payment_data[name] = value
                
                return {
                    'success': True,
                    'merchant_request_id': stk_callback.get('MerchantRequestID'),
                    'checkout_request_id': stk_callback.get('CheckoutRequestID'),
                    'amount': payment_data.get('Amount'),
                    'mpesa_receipt': payment_data.get('MpesaReceiptNumber'),
                    'transaction_date': payment_data.get('TransactionDate'),
                    'phone_number': payment_data.get('PhoneNumber')
                }
            else:
                # Payment failed or cancelled
                return {
                    'success': False,
                    'merchant_request_id': stk_callback.get('MerchantRequestID'),
                    'checkout_request_id': stk_callback.get('CheckoutRequestID'),
                    'result_code': result_code,
                    'result_desc': stk_callback.get('ResultDesc'),
                    'error_message': stk_callback.get('ResultDesc')
                }
            
        except Exception as e:
            logger.error(f"Error validating callback: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

