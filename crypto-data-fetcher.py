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


def fetch_pair(exchange, pair, period, after=1):
    url_base = 'https://api.cryptowat.ch/markets'
    url_full = "{}/{}/{}/ohlc?periods={}".format(
        url_base, exchange, pair, periods_dict[period])
    url_full = url_full + '&after={}'.format(after)
    resp = requests.get(url=url_full)
    data = resp.json()["result"]
    allowance = resp.json()["allowance"]
    log.info("Cryptowatch remaining allowance: {}".format(
        allowance['remaining']))
    df = pd.DataFrame(data[periods_dict[period]], columns=[
                      'time', 'open', 'high', 'low', 'close', 'volume_base', 'volume_quote'])
    return df


def fetch_data(filepath, exchange, pair, period):

    log.info("Opening store file: {}".format(filepath))
    with h5py.File(filepath, 'a') as f:
        datapath = '/{}/{}/{}'.format(exchange, pair, period)

        # Set doesnt exist, we'll create it
        if datapath not in f:
            log.info("Dataset does not exist yet: creating a new one")
            new_data = fetch_pair(exchange, pair, period)
            new_data_size = new_data.shape[0]
            log.info("Added {} new rows".format(new_data_size))
            f.create_dataset(datapath, data=new_data,
                             maxshape=(None, 7), compression="gzip")

        # Set exists, we'll fetch the last data of it, to know after what timestamp to query the data
        else:
            dset = f[datapath]
            last_row = dset[-1]
            # The '+1' is made to ensure that the last data in the set won't be re-fetched
            last_timestamp = int(last_row[0])+1
            new_data = fetch_pair(exchange, pair, period, after=last_timestamp)
            new_data_size = new_data.shape[0]
            if(new_data_size > 0):
                dset.resize(dset.shape[0] + new_data_size, axis=0)
                dset[-new_data_size:] = new_data
                log.info("Added {} new rows".format(new_data_size))

    log.info("Data fetching successful!".format(new_data_size))


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

    parser.add_argument('-f', '--filepath', required=False, default='store.h5', type=str,
                        help='file path in which to store the fetched data, or on which to complete existing data')

    # Defaults for dates
    parser.add_argument('-e', '--exchange', required=True, type=str,
                        help='exchange symbol on which to fetch the data (exchange listing https://api.cryptowat.ch/exchanges)')

    parser.add_argument('-s', '--symbol', required=True, type=str,
                        help='pair symbol for which to fetch the data (find pair listing for every exchange here https://cryptowat.ch/exchanges). Ex: btceur or etheur or zecbtc etc.')

    parser.add_argument('-p', '--period', required=False, type=str, default='1m',
                        help='time period of the data, must be one of: "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", 6h", "12h", "1d", "3d", "1w"')

    parser.add_argument('-l', '--logfile', required=False, type=str,
                        help='filepath of the logfile in which to write the logs (if none is provided, no log file will be created)')

    return parser.parse_args(pargs)


if __name__ == "__main__":

    # Parse args
    args = parse_args()
    filepath = getattr(args, "filepath")
    exchange = getattr(args, "exchange")
    pair = getattr(args, "symbol")
    period = getattr(args, "period")
    logfile = getattr(args, "logfile")
    # TODO: delete, for debug only now

    # Setup logging
    log = logging.getLogger("crypto-data-fetcher")
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    log.setLevel(logging.INFO)
    if(logfile != None):
        fh = logging.FileHandler("{}".format(logfile))
        fh.setFormatter(formatter)
        log.addHandler(fh)

    # Fetch data
    fetch_data(filepath, exchange, pair, period)
