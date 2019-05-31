#!/usr/bin/python3

import logging
import time
import schedule
import argparse
import requests
import numpy as np
import pandas as pd
from datetime import datetime
import h5py

periods_dict = {
    '1m': '60',
    '3m': '180',
    '5m': '300',
    '15m': '900',
    '30m': '1800',
    '1h': '3600',
    '2h': '7200',
    '4h': '14400',
    '6h': '21600',
    '12h': '43200',
    '1d': '86400',
    '3d': '259200',
    '1w': '604800',
}

'''
Fetch the requested pair from the cryptowatch API. At the beginning, we force "after" to be at 1 to get the maximum amount of data
'''


def fetch_pair(pair, period, after=None):
    url_base = 'https://api.cryptowat.ch/markets/kraken'
    url_full = "{}/{}/ohlc?periods={}".format(
        url_base, pair, periods_dict[period])
    if after == None:
        url_full = url_full + '&after=1'
    resp = requests.get(url=url_full)
    data = resp.json()["result"]
    allowance = resp.json()["allowance"]
    print("Remaining allowance: {}".format(allowance['remaining']))
    df = pd.DataFrame(data[periods_dict[period]], columns=[
                      'time', 'open', 'high', 'low', 'close', 'volume_base', 'volume_quote'])
    return df


def fetch_data(filepath, exchange, pair, period):

    log.info("Opening/Creating store file: {}".format(filepath))
    with h5py.File(filepath, 'a') as f:
        datapath = '/{}/{}/{}'.format(exchange, pair, period)
        dset = f[datapath]

        # Set doesnt exist, we'll create it
        if dset.shape[0] == 0:
            new_data = fetch_pair(pair, period)
            f.create_dataset(datapath, data=new_data)
        # Set exists, we'll fetch the last data of it, to know after what timestamp to query the data
        else:
            last_row = dset[-1]
            print(last_row)
        # Open current CSV file
        # try:
        #     existing_data = pd.read_hdf(
        #         filepath, key=key, index_col="datetime", parse_dates=True)
        # except FileNotFoundError:
        #     log.info("Data file does not exist yet")
        #     pass

        # If theres already data, fetch the date from when the data should be added
        after = None
        if existing_data.shape[0] > 0:
            after_datetime = existing_data.index[-1].to_pydatetime()
            after = int(datetime.timestamp(after_datetime))




'''
Parses the args according to the usage
'''

def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'crypto-data-fetcher'
        )
    )

    parser.add_argument('-f', '--filepath', required=True, type=str,
                        help='file path in which to store the fetched data, or on which to complete existing data')

    # Defaults for dates
    parser.add_argument('-e', '--exchange', required=True, type=str,
                        help='exchange symbol on which to fetch the data (exchange listing https://api.cryptowat.ch/exchanges)')

    parser.add_argument('-s', '--symbol', required=True, type=str,
                        help='pair symbol for which to fetch the data (find pair listing for every exchange here https://cryptowat.ch/exchanges). Ex: btceur or etheur or zecbtc etc.')

    parser.add_argument('-p', '--period', required=False, type=str, default='1m',
                        help='time period of the data, must be one of: "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", 6h", "12h", "1d", "3d", "1w"')

    return parser.parse_args(pargs)


if __name__ == "__main__":

    # Setup logging
    log = logging.getLogger("crypto-data-fetcher")
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    log.setLevel(logging.INFO)

    # Parse args
    args = parse_args()
    filepath = getattr(args, "filepath")
    exchange = getattr(args, "exchange")
    pair = getattr(args, "symbol")
    period = getattr(args, "period")
    # TODO: delete, for debug only now
    print("{} {} {} {}".format(filepath, exchange, pair, period))

    # Fetch data
    fetch_data(filepath, exchange, pair, period)