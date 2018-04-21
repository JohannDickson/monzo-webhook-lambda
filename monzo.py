#! /usr/bin/env python

import logging
from datetime import datetime as dt
from dateutil import tz
from dateutil.parser import parse

## ----- Global vars -----
dateOutFmt = "%d/%m/%Y %H:%M:%S"

## ----- Setup logging -----
log = logging.getLogger()
log.setLevel(logging.INFO)


def newTransaction(event, context):
    transaction = event['data']
    merchant = transaction['merchant']

    txUTC = parse(transaction['created'])
    txTime = txUTC.astimezone(tz.gettz(merchant['address']['country']))

    amount = float(transaction['amount']) / 100

    ## Transform foreign currencies
    local_amount = ''
    if transaction['local_currency'] != 'GBP':
        local_amount = "%.2f %s" % (
                float(transaction['local_amount'])/100, transaction['local_currency']
            )

    item = transaction['category']

    output = {
        'Timestamp': dt.strftime(txTime, dateOutFmt),
        'Item': item,
        'Vendor': merchant['name'],
        'Amount': "%.2f" % amount,
        '__PowerAppsId__': context.aws_request_id,
    }

    log.info(output)

    return {'statusCode': 200}
