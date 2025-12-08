import requests
import base64
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class DarajaAPI:
    """
    Wrapper class for Safaricom Daraja API
    Handles M-Pesa STK Push and B2C payments
    """
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.initiator_name = settings.MPESA_INITIATOR_NAME
        self.security_credential = settings.MPESA_SECURITY_CREDENTIAL
        
        # API URLs - Sandbox or Production
        if settings.MPESA_ENVIRONMENT == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
        
        self.access_token = None
    
    def get_access_token(self):
        """
        Generate OAuth access token
        Returns: access_token string
        """
        url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        
        try:
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret)
            )
            response.raise_for_status()
            result = response.json()
            self.access_token = result.get('access_token')
            logger.info("Access token generated successfully")
            return self.access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting access token: {str(e)}")
            raise Exception(f"Failed to get access token: {str(e)}")
    
    def generate_password(self):
        """
        Generate password for STK Push
        Returns: tuple (password, timestamp)
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(data_to_encode.encode()).decode('utf-8')
        return password, timestamp
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        """
        Initiate STK Push (Lipa Na M-Pesa Online)
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge
            account_reference: Reference for the transaction (e.g., sale number)
            transaction_desc: Description of the transaction
            callback_url: URL to receive payment confirmation
        
        Returns:
            dict with response data
        """
        if not self.access_token:
            self.get_access_token()
        
        url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
        password, timestamp = self.generate_password()
        
        # Format phone number
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        elif phone_number.startswith('7') or phone_number.startswith('1'):
            phone_number = '254' + phone_number
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"STK Push initiated: {result}")
            return {
                'success': True,
                'merchant_request_id': result.get('MerchantRequestID'),
                'checkout_request_id': result.get('CheckoutRequestID'),
                'response_code': result.get('ResponseCode'),
                'response_description': result.get('ResponseDescription'),
                'customer_message': result.get('CustomerMessage')
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def stk_push_query(self, checkout_request_id):
        """
        Query STK Push transaction status
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push response
        
        Returns:
            dict with transaction status
        """
        if not self.access_token:
            self.get_access_token()
        
        url = f'{self.base_url}/mpesa/stkpushquery/v1/query'
        password, timestamp = self.generate_password()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'result_code': result.get('ResultCode'),
                'result_desc': result.get('ResultDesc')
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push query error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def b2c_payment(self, phone_number, amount, occasion, remarks, result_url, timeout_url):
        """
        Initiate B2C payment (Business to Customer)
        Used for supplier payments and customer refunds
        
        Args:
            phone_number: Recipient phone number (format: 254XXXXXXXXX)
            amount: Amount to send
            occasion: Occasion for payment
            remarks: Payment remarks
            result_url: URL to receive payment result
            timeout_url: URL to receive timeout notification
        
        Returns:
            dict with response data
        """
        if not self.access_token:
            self.get_access_token()
        
        url = f'{self.base_url}/mpesa/b2c/v1/paymentrequest'
        
        # Format phone number
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        elif phone_number.startswith('7') or phone_number.startswith('1'):
            phone_number = '254' + phone_number
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'InitiatorName': self.initiator_name,
            'SecurityCredential': self.security_credential,
            'CommandID': 'BusinessPayment',  # or 'SalaryPayment', 'PromotionPayment'
            'Amount': int(amount),
            'PartyA': self.shortcode,
            'PartyB': phone_number,
            'Remarks': remarks,
            'QueueTimeOutURL': timeout_url,
            'ResultURL': result_url,
            'Occasion': occasion
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"B2C payment initiated: {result}")
            return {
                'success': True,
                'conversation_id': result.get('ConversationID'),
                'originator_conversation_id': result.get('OriginatorConversationID'),
                'response_code': result.get('ResponseCode'),
                'response_description': result.get('ResponseDescription')
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"B2C payment error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def register_urls(self, validation_url, confirmation_url):
        """
        Register C2B validation and confirmation URLs
        Only needed for C2B (if implementing)
        """
        if not self.access_token:
            self.get_access_token()
        
        url = f'{self.base_url}/mpesa/c2b/v1/registerurl'
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'ShortCode': self.shortcode,
            'ResponseType': 'Completed',  # or 'Cancelled'
            'ConfirmationURL': confirmation_url,
            'ValidationURL': validation_url
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"URLs registered: {result}")
            return {
                'success': True,
                'response': result
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"URL registration error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Utility functions

def format_phone_number(phone):
    """Format phone number to 254XXXXXXXXX"""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('0'):
        return '254' + phone[1:]
    elif phone.startswith('+'):
        return phone[1:]
    elif phone.startswith('7') or phone.startswith('1'):
        return '254' + phone
    return phone


def validate_phone_number(phone):
    """Validate Kenyan phone number format"""
    phone = format_phone_number(phone)
    if len(phone) == 12 and phone.startswith('254'):
        return True
    return False