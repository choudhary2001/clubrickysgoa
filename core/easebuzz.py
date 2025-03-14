import hashlib
from django.conf import settings
import json

class EasebuzzPayment:
    def __init__(self):
        self.MERCHANT_KEY = "EFTU4F7D2P"
        self.SALT = "VLJEMDDX7X"
        self.ENV = "prod"  # prod for production
        self.PAYMENT_URL = "https://pay.easebuzz.in/payment/initiateLink"
    
    def generate_hash(self, data):
        # Hash string format according to Easebuzz documentation
        hash_string = (
            f"{self.MERCHANT_KEY}|{data['txnid']}|{data['amount']}|{data['productinfo']}|"
            f"{data['firstname']}|{data['email']}|{data['udf1']}|{data['udf2']}|{data['udf3']}|"
            f"{data['udf4']}|{data['udf5']}||||||{self.SALT}"
        )
        return hashlib.sha512(hash_string.encode()).hexdigest()
    
    def verify_payment(self, data):
        received_hash = data.get('hash')
        # Verification hash string format
        hash_string = (
            f"{self.SALT}|{data.get('status')}|{self.MERCHANT_KEY}|{data.get('txnid')}|"
            f"{data.get('amount')}|{data.get('productinfo')}|{data.get('firstname')}|"
            f"{data.get('email')}|{data.get('phone')}|{data.get('udf1')}|{data.get('udf2')}|"
            f"{data.get('udf3')}|{data.get('udf4')}|{data.get('udf5')}||||||"
        )
        generated_hash = hashlib.sha512(hash_string.encode()).hexdigest()
        return received_hash == generated_hash

    def create_payment_data(self, booking):
        # Get phone number or use a default
        phone = "9999999999"  # Default phone number if none available
        if hasattr(booking.user, 'profile') and booking.user.profile.phone:
            # Remove any non-digit characters and ensure it's 10 digits
            phone = ''.join(filter(str.isdigit, booking.user.profile.phone))
            if len(phone) > 10:
                phone = phone[-10:]  # Take last 10 digits
            elif len(phone) < 10:
                phone = "9999999999"  # Use default if invalid

        data = {
            'key': self.MERCHANT_KEY,
            'txnid': booking.booking_reference,
            'amount': str(booking.total_amount),
            'productinfo': f"Event Booking - {booking.event.title}",
            'firstname': booking.user.first_name or booking.user.username,
            'email': booking.user.email,
            'phone': phone,
            'surl': 'https://clubrickeygoa.com/payment/success/',
            'furl': 'https://clubrickeygoa.com/payment/failure/',
            'udf1': str(booking.id),
            'udf2': '',
            'udf3': '',
            'udf4': '',
            'udf5': '',
        }
        
        # Generate access key for iframe integration
        data['hash'] = self.generate_hash(data)
        return data 