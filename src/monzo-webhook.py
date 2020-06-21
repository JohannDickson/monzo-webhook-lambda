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

# Spreadsheet headers:
# Timestamp | Item | Vendor | Amount | Local amount | ID

def convert_amount(amount):
    return float(amount) / 100


def get_worksheet():
    log.debug("Retrieving credentials")
    credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPE)
    log.debug("Authorizing credentials")
    gc = gspread.authorize(credentials)

    log.debug("Accessing sheet %s in %s", WORKSHEET, SPREADSHEET_ID)
    sheet = gc.open_by_key(SPREADSHEET_ID)
    ws = sheet.worksheet(WORKSHEET)

    return ws


def update_amount(transactionId, amount):
    ws = get_worksheet()
    cell = ws.find(transactionId)

    log.info("Found initial transaction at Row %s:Col %s", cell.row, cell.col)

    log.debug("Updating amount to %s", amount)
    result = ws.update_cell(cell.row, cell.col - 2, amount)
    log.info(result)


def newTransfer(transaction):
    counterparty = transaction['counterparty']

    txUTC = parse(transaction['created'])
    txCountry = "GB"
    txTime = txUTC.astimezone(tz.gettz(txCountry))
    log.debug("Transfer time:  %s (UTC)", dt.strftime(txUTC, dateOutFmt))

    amount = convert_amount(transaction['amount'])
    log.debug("Amount: %s", amount)

    values = {
        'Timestamp': dt.strftime(txTime, dateOutFmt),
        'Item': transaction['notes'],
        'Vendor': counterparty['name'],
        'Amount': "%.2f" % amount,
        'Local': None,
        'ID': transaction['id'],
    }
    log.info(values)

    write_new_entry_to_spreadsheet(values)


def newTransaction(transaction):

    if transaction['settled']:
        if transaction['local_currency'] != 'GBP':
            log.info("Updating settled foreign transaction %s", transaction['id'])
            update_amount(transaction['id'], convert_amount(transaction['amount']))
            return
        else:
            log.info("Local transaction settled, exiting")
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
        log.debug("Local amount: %s", local_amount)

    ## Set category
    item = transaction['category']
    # Lunch hours and a weekday (5 = sat)
    if lunch_start < txTime.strftime('%H%M') < lunch_end and txTime.weekday() < 5:
        item = "Lunch"
    else:
        item = "Groceries"


    ## What we'll send to spreadsheet
    values = {
        'Timestamp': dt.strftime(txTime, dateOutFmt),
        'Item': item,
        'Vendor': merchant['name'],
        'Amount': "%.2f" % amount,
        'Local': local_amount,
        'ID': transaction['id'],
    }
    log.info(values)

    write_new_entry_to_spreadsheet(values)


def write_new_entry_to_spreadsheet(values):
    newEntry = [
        values['Timestamp'],
        values['Item'],
        values['Vendor'],
        values['Amount'],
        values['Local'],
        values['ID'],
    ]

    ws = get_worksheet()

    log.info("Inserting values: %s", newEntry)
    result = ws.append_row(newEntry, VALUE_INPUT)
    log.info("Values added at cells: %s", result['updates']['updatedRange'].split('!')[-1])


def lambda_handler(event, context):
    log.info(event)
    transaction = event['data']

    ## event type is always "transaction.created"
    ## instead use the contents of transaction to identify transaction/transfer

    if transaction['merchant']:
        log.debug("Processing transaction")
        newTransaction(transaction)

    elif transaction['counterparty']:
        log.debug("Processing transfer")
        newTransfer(transaction)

    log.debug("Processing complete")

    return {'statusCode': 200}
