"""
Payment and Subscription Management Module
Handles payment tracking and subscription management with MongoDB
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pymongo import MongoClient, DESCENDING
import os

logger = logging.getLogger(__name__)


class PaymentManager:
    """Manages payments and subscriptions"""
    
    # Payment types
    PAYMENT_TYPE_REPORT = 'report_download'
    PAYMENT_TYPE_SUBSCRIPTION = 'subscription'
    
    # Subscription plans
    PLANS = {
        'basic': {
            'name': 'Basic Plan',
            'price': 100,  # KSH per month
            'duration_days': 30,
            'features': [
                'Basic security scans',
                'SSL/TLS checks',
                'Header analysis',
                'Quick wins scanner',
                '2 scans per day',
                'View results online'
            ]
        },
        'pro': {
            'name': 'Professional Plan',
            'price': 2000,  # KSH per month
            'duration_days': 30,
            'features': [
                'All Basic features',
                'SQL Injection scanning',
                'XSS detection',
                'Directory enumeration',
                'Unlimited scans',
                'Priority support',
                'Advanced PDF reports',
                'Email reports',
                'Trend analysis',
                'API access'
            ]
        }
    }
    
    def __init__(self, mongodb_storage=None):
        """
        Initialize Payment Manager
        
        Args:
            mongodb_storage: MongoDBStorage instance (optional)
        """
        self.db = None
        self.payments_collection = None
        self.subscriptions_collection = None
        
        try:
            if mongodb_storage:
                self.db = mongodb_storage.db
            else:
                # Connect to MongoDB with timeout
                connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
                client = MongoClient(
                    connection_string,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000
                )
                # Test connection
                client.admin.command('ping')
                self.db = client[os.getenv('MONGODB_DB_NAME', 'cybertech')]
            
            if self.db:
                self.payments_collection = self.db['payments']
                self.subscriptions_collection = self.db['subscriptions']
                self._ensure_indexes()
                logger.info("Payment manager initialized with MongoDB")
        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB for payments: {e}")
            logger.warning("Payment tracking will be disabled. Set MONGODB_URI to enable payments.")
            self.db = None
    
    def _ensure_indexes(self):
        """Create necessary indexes"""
        try:
            # Payment indexes
            self.payments_collection.create_index('checkout_request_id', unique=True)
            self.payments_collection.create_index('phone_number')
            self.payments_collection.create_index('scan_id')
            self.payments_collection.create_index([('created_at', DESCENDING)])
            
            # Subscription indexes
            self.subscriptions_collection.create_index('phone_number')
            self.subscriptions_collection.create_index('expires_at')
            self.subscriptions_collection.create_index([('created_at', DESCENDING)])
            
            logger.info("Payment indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating payment indexes: {e}")
    
    def create_payment_record(self, payment_data: Dict) -> bool:
        """
        Create a payment record
        
        Args:
            payment_data: Payment information
            
        Returns:
            bool: True if created successfully
        """
        if not self.payments_collection:
            logger.warning("Payment collection not available. Cannot create payment record.")
            return False
            
        try:
            payment_doc = {
                'checkout_request_id': payment_data.get('checkout_request_id'),
                'merchant_request_id': payment_data.get('merchant_request_id'),
                'phone_number': payment_data.get('phone_number'),
                'amount': payment_data.get('amount'),
                'payment_type': payment_data.get('payment_type', self.PAYMENT_TYPE_REPORT),
                'scan_id': payment_data.get('scan_id'),
                'status': 'pending',
                'created_at': datetime.utcnow(),
                'metadata': payment_data.get('metadata', {})
            }
            
            self.payments_collection.insert_one(payment_doc)
            logger.info(f"Payment record created: {payment_doc['checkout_request_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating payment record: {e}")
            return False
    
    def update_payment_status(self, checkout_request_id: str, callback_data: Dict) -> bool:
        """
        Update payment status from M-Pesa callback
        
        Args:
            checkout_request_id: CheckoutRequestID
            callback_data: Callback data from M-Pesa
            
        Returns:
            bool: True if updated successfully
        """
        if not self.payments_collection:
            logger.warning("Payment collection not available")
            return False
            
        try:
            # Determine status based on M-Pesa result code
            if callback_data.get('success'):
                status = 'completed'
            else:
                result_code = callback_data.get('result_code', 0)
                # Result code 1032 = User cancelled (wrong PIN, etc.)
                # Result code 1 = Insufficient funds
                # Other codes = Failed
                if result_code == 1032:
                    status = 'cancelled'
                else:
                    status = 'failed'
            
            update_data = {
                'status': status,
                'mpesa_receipt': callback_data.get('mpesa_receipt'),
                'transaction_date': callback_data.get('transaction_date'),
                'result_code': callback_data.get('result_code'),
                'result_desc': callback_data.get('result_desc'),
                'updated_at': datetime.utcnow(),
                'callback_data': callback_data
            }
            
            logger.info(f"Updating payment {checkout_request_id} to status: {status}")
            
            result = self.payments_collection.update_one(
                {'checkout_request_id': checkout_request_id},
                {'$set': update_data}
            )
            
            # If payment was successful and it's a subscription, create subscription
            if callback_data.get('success'):
                payment = self.payments_collection.find_one({'checkout_request_id': checkout_request_id})
                if payment and payment.get('payment_type') == self.PAYMENT_TYPE_SUBSCRIPTION:
                    self._create_subscription(payment)
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
            return False
    
    def _create_subscription(self, payment: Dict) -> bool:
        """Create subscription from successful payment"""
        try:
            phone_number = payment.get('phone_number')
            plan = payment.get('metadata', {}).get('plan', 'pro')
            
            subscription_doc = {
                'phone_number': phone_number,
                'plan': plan,
                'amount_paid': payment.get('amount'),
                'payment_id': str(payment.get('_id')),
                'checkout_request_id': payment.get('checkout_request_id'),
                'status': 'active',
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=30),
                'features': self.PLANS.get(plan, {}).get('features', [])
            }
            
            # Deactivate any existing subscriptions
            self.subscriptions_collection.update_many(
                {'phone_number': phone_number, 'status': 'active'},
                {'$set': {'status': 'expired'}}
            )
            
            # Create new subscription
            self.subscriptions_collection.insert_one(subscription_doc)
            logger.info(f"Subscription created for {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return False
    
    def check_payment_status(self, checkout_request_id: str) -> Dict:
        """
        Check payment status
        
        Args:
            checkout_request_id: CheckoutRequestID to check
            
        Returns:
            Dict with payment status
        """
        try:
            payment = self.payments_collection.find_one(
                {'checkout_request_id': checkout_request_id},
                {'_id': 0}
            )
            
            if not payment:
                return {'found': False}
            
            return {
                'found': True,
                'status': payment.get('status'),
                'amount': payment.get('amount'),
                'payment_type': payment.get('payment_type'),
                'scan_id': payment.get('scan_id'),
                'mpesa_receipt': payment.get('mpesa_receipt'),
                'created_at': payment.get('created_at')
            }
            
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return {'found': False, 'error': str(e)}
    
    def has_active_subscription(self, phone_number: str) -> bool:
        """
        Check if phone number has active subscription
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            bool: True if has active subscription
        """
        if not self.subscriptions_collection:
            logger.warning("Subscription collection not available")
            return False
            
        try:
            subscription = self.subscriptions_collection.find_one({
                'phone_number': phone_number,
                'status': 'active',
                'expires_at': {'$gt': datetime.utcnow()}
            })
            
            return subscription is not None
            
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return False
    
    def has_active_subscription_by_email(self, email: str) -> bool:
        """
        Check if email has active subscription
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if has active subscription
        """
        if not self.subscriptions_collection:
            logger.warning("Subscription collection not available")
            return False
            
        try:
            subscription = self.subscriptions_collection.find_one({
                'email': email,
                'status': 'active',
                'expires_at': {'$gt': datetime.utcnow()}
            })
            
            return subscription is not None
            
        except Exception as e:
            logger.error(f"Error checking subscription by email: {e}")
            return False
    
    def get_subscription(self, phone_number: str) -> Optional[Dict]:
        """
        Get active subscription for phone number
        
        Args:
            phone_number: Phone number
            
        Returns:
            Dict with subscription details or None
        """
        try:
            subscription = self.subscriptions_collection.find_one(
                {
                    'phone_number': phone_number,
                    'status': 'active',
                    'expires_at': {'$gt': datetime.utcnow()}
                },
                {'_id': 0}
            )
            
            return subscription
            
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return None
    
    def check_report_payment(self, scan_id: str, phone_number: str) -> bool:
        """
        Check if report has been paid for
        
        Args:
            scan_id: Scan ID
            phone_number: Phone number
            
        Returns:
            bool: True if paid
        """
        if not self.payments_collection:
            logger.warning("Payment collection not available. Cannot check payment status.")
            return False
            
        try:
            # Check for active subscription (includes all features)
            if self.has_active_subscription(phone_number):
                return True
            
            # Check for one-time report payment
            payment = self.payments_collection.find_one({
                'scan_id': scan_id,
                'phone_number': phone_number,
                'payment_type': self.PAYMENT_TYPE_REPORT,
                'status': 'completed'
            })
            
            return payment is not None
            
        except Exception as e:
            logger.error(f"Error checking report payment: {e}")
            return False
    
    def check_report_payment_by_email(self, scan_id: str, email: str) -> bool:
        """
        Check if report has been paid for by email (Paystack)
        
        Args:
            scan_id: Scan ID
            email: Email address
            
        Returns:
            bool: True if paid
        """
        if not self.payments_collection:
            logger.warning("Payment collection not available. Cannot check payment status.")
            return False
            
        try:
            # Check for active subscription by email
            if self.has_active_subscription_by_email(email):
                return True
            
            # Check for one-time report payment by email
            payment = self.payments_collection.find_one({
                'scan_id': scan_id,
                'email': email,
                'payment_type': self.PAYMENT_TYPE_REPORT,
                'status': 'completed'
            })
            
            return payment is not None
            
        except Exception as e:
            logger.error(f"Error checking report payment by email: {e}")
            return False
    
    def get_payment_history(self, phone_number: str, limit: int = 20) -> List[Dict]:
        """
        Get payment history for a phone number
        
        Args:
            phone_number: Phone number
            limit: Maximum results to return
            
        Returns:
            List of payment records
        """
        try:
            cursor = self.payments_collection.find(
                {'phone_number': phone_number},
                {'_id': 0}
            ).sort('created_at', DESCENDING).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Error getting payment history: {e}")
            return []

