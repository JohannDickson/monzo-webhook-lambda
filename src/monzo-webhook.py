#! /usr/bin/env python

import os
import sys
import logging
# Date operations
from datetime import datetime as dt
from dateutil import tz
from dateutil.parser import parse
# Spreadsheet integration
import gspread
from oauth2client.service_account import ServiceAccountCredentials

## ----- Global vars -----
dateOutFmt = "%d/%m/%Y %H:%M:%S"
lunch_start = '1100'
lunch_end   = '1430'

## ----- Spreadsheet setup -----
SCOPE = 'https://www.googleapis.com/auth/spreadsheets'
VALUE_INPUT = 'USER_ENTERED'
SERVICE_ACCOUNT_FILE = os.environ['AUTHCREDS']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
WORKSHEET = os.environ['WORKSHEET']

## ----- Setup logging -----
log = logging.getLogger()
log.setLevel(logging.INFO)


def convert_amount(amount):
    return float(amount) / 100


def newTransaction(transaction):

    if transaction['settled']:
        log.info("Transaction settled, exiting")
        return

    merchant = transaction['merchant']

    txUTC = parse(transaction['created'])
    txCountry = "GB"
    txTime = txUTC.astimezone(tz.gettz(txCountry))
    log.debug("Transaction time:  %s (UTC)", dt.strftime(txUTC, dateOutFmt))
    log.debug("Local transaction: %s (%s)", dt.strftime(txTime, dateOutFmt), txCountry)

    ## Transform cents into units
    amount = convert_amount(transaction['amount'])
    log.debug("Amount: %s", amount)

    ## Transform foreign currencies
    local_amount = ''
    if transaction['local_currency'] != 'GBP':
        local_amount = "%.2f %s" % (
                convert_amount(transaction['local_amount']), transaction['local_currency']
            )
        log.debug("Local amount: ", local_amount)

    ## Set category
    item = transaction['category']
    # Lunch hours and a weekday (5 = sat)
    if lunch_start < txTime.strftime('%H%M') < lunch_end and txTime.weekday() < 5:
        item = "Lunch"
    else:
        item = "Groceries"


    ## What we'll send to spreadsheet
    output = {
        'Timestamp': dt.strftime(txTime, dateOutFmt),
        'Item': item,
        'Vendor': merchant['name'],
        'Amount': "%.2f" % amount,
        'Local': local_amount,
        'ID': transaction['id'],
    }
    log.info(output)

    values = [
        output['Timestamp'],
        output['Item'],
        output['Vendor'],
        output['Amount'],
        output['Local'],
        output['__PowerAppsId__'],
    ]

    log.debug("Retrieving credentials")
    credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPE)
    log.debug("Authorizing credentials")
    gc = gspread.authorize(credentials)

    log.debug("Accessing sheet")
    sheet = gc.open_by_key(SPREADSHEET_ID)
    ws = sheet.worksheet(WORKSHEET)

    log.info("Inserting values: %s", values)
    result = ws.append_row(values, VALUE_INPUT)
    log.info("Values added at cells: %s", result['updates']['updatedRange'].split('!')[-1])


def lambda_handler(event, context):
    transaction = event['data']

    if transaction['merchant']:
        log.debug("Processing transaction")
        log.info(transaction)
        newTransaction(transaction)

    log.debug("Processing complete")

    return {'statusCode': 200}
