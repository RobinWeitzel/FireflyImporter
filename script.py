import logging
from datetime import date, timedelta
from fints.client import FinTS3PinTanClient
import requests
import json
import schedule
import time
import os
import sys

### Bank data
blz = os.environ['BANK_BLZ'] # Your bank's BLZ
username = os.environ['BANK_USERNAME'] # Your login name
pin = os.environ['BANK_PIN'] # Your banking PIN
bank_url = os.environ['BANK_URL'] # your banks fints url
product_id = os.environ['BANK_PRODUCT_ID'] # your fints product id

### Firefly data
token = os.environ['FIREFLY_TOKEN']
firefly_url = os.environ['FIREFLY_URL']
headers = {'Authorization' : 'Bearer ' + token, 'Accept' : 'application/json', 'Content-Type' : 'application/json'}

req = requests.get(firefly_url + '/api/v1/accounts', headers=headers)

if(req.status_code != 200):
    logging.error("Could not get accounts from Firefly. Aborting.")
    sys.exit()

account_ids = {} # a map of IBAN to Firefly account id

resp = json.loads(req.text)

for a in resp["data"]:
    if a["type"] == "accounts" and a["attributes"]["iban"] is not None:
        account_ids[a["attributes"]["iban"]] = int(a["id"])

logging.info("Retrieved accounts from firefly")

# Establish connection
logging.basicConfig(level=logging.INFO)
f = FinTS3PinTanClient(
    blz,  
    username,  
    pin,  
    bank_url,
    product_id=product_id
)



def create_transactions(account, transactions):
    for transaction in transactions:
        t = {
            "amount": abs(transaction.data['amount'].amount).to_eng_string(),
            "currency_code": transaction.data['amount'].currency,
            "date": transaction.data['date'].strftime('%Y-%m-%dT08:00+02:00'),
            "reconciled": False,
            "description": transaction.data['purpose'],
            "external_id": transaction.data['id']
        }

        if transaction.data['status'] == "C": # a deposit
            t["type"] = "deposit"
            t["source_name"] = transaction.data["applicant_name"]
            t["destination_id"] = account_ids[account.iban]
        else:
            t["type"] = "withdrawal"
            t["source_id"] = account_ids[account.iban]
            t["destination_name"] = transaction.data["applicant_name"]
        
        data = {
            "error_if_duplicate_hash": True,
            "apply_rules": True,
            "group_title": transaction.data['posting_text'],
            "transactions": [t]
        }
        r = requests.post(firefly_url + '/api/v1/transactions', data=json.dumps(data), headers=headers)

        if(r.status_code != 200 and "Duplicate of transaction" not in r.text):
            logging.error('Failed posting transaction to api with error code: ' + str(r.status_code) + '.')
            logging.error('Error message is: ' + r.text)
            logging.error(json.dumps(data))

def get_transactions():
    with f:
        # Since PSD2, a TAN might be needed for dialog initialization. Let's check if there is one required
        if f.init_tan_response:
            logging.error('Bank access requires TAN which is not supported.')

        # Fetch accounts
        accounts = f.get_sepa_accounts()

        logging.info('Retrieved ' + str(len(accounts)) + ' accounts from bank.')

        # get the transactions for each account
        for account in accounts:
            transactions = f.get_transactions(account, date.today() - timedelta(days=7), date.today())
            logging.info('Retrieved ' + str(len(transactions)) + ' for account ' + account.iban + ' that took place in the last 7 days.')
            create_transactions(account, transactions)

schedule.every().hour.do(get_transactions)

logging.info("Started scheduled job")

while True:
    schedule.run_pending()
    time.sleep(1)