import hashlib
import json
import requests

class Easebuzz:
    def __init__(self, merchant_key, salt, env):
        self.merchant_key = merchant_key
        self.salt = salt
        self.env = env
        
        if env == 'prod':
            self.url = 'https://pay.easebuzz.in/'
        else:
            self.url = 'https://testpay.easebuzz.in/'

    def _generate_hash(self, data):
        hash_string = (
            f"{self.merchant_key}|{data['txnid']}|{data['amount']}|{data['productinfo']}|"
            f"{data['firstname']}|{data['email']}|{data['udf1']}|{data['udf2']}|{data['udf3']}|"
            f"{data['udf4']}|{data['udf5']}||||||{self.salt}"
        )
        return hashlib.sha512(hash_string.encode()).hexdigest()

    def initiatePaymentAPI(self, params):
        params['key'] = self.merchant_key
        params['hash'] = self._generate_hash(params)
        
        response = requests.post(
            f"{self.url}payment/initiateLink",
            data=params
        )
        return response.text

    def easebuzzResponse(self, response_params):
        return self._verify_payment(response_params)

    def _verify_payment(self, data):
        hash_string = (
            f"{self.salt}|{data.get('status')}|{self.merchant_key}|{data.get('txnid')}|"
            f"{data.get('amount')}|{data.get('productinfo')}|{data.get('firstname')}|"
            f"{data.get('email')}|{data.get('phone')}|{data.get('udf1')}|{data.get('udf2')}|"
            f"{data.get('udf3')}|{data.get('udf4')}|{data.get('udf5')}||||||"
        )
        generated_hash = hashlib.sha512(hash_string.encode()).hexdigest()
        return data.get('hash') == generated_hash 