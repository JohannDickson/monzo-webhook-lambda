#! /usr/bin/env python

import logging
from datetime import datetime as dt
from dateutil import tz
from dateutil.parser import parse

## ----- Global vars -----
dateOutFmt = "%d/%m/%Y %H:%M:%S"
lunch_start = '1100'
lunch_end   = '1430'

## ----- Setup logging -----
log = logging.getLogger()
log.setLevel(logging.INFO)


def newTransaction(event, context):
    transaction = event['data']
    merchant = transaction['merchant']

    txUTC = parse(transaction['created'])
    txTime = txUTC.astimezone(tz.gettz(merchant['address']['country']))
    log.debug("Transaction time:  %s (UTC)", dt.strftime(txUTC, dateOutFmt))
    log.debug("Local transaction: %s (%s)", dt.strftime(txTime, dateOutFmt), merchant['address']['country'])

    ## Transform cents into units
    amount = float(transaction['amount']) / 100
    log.debug("Amount: %s", amount)

    ## Transform foreign currencies
    local_amount = ''
    if transaction['local_currency'] != 'GBP':
        local_amount = "%.2f %s" % (
                float(transaction['local_amount'])/100, transaction['local_currency']
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
        '__PowerAppsId__': context.aws_request_id,
    }
    log.info(output)

    return {'statusCode': 200}
