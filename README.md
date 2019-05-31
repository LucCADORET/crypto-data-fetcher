# crypto-data-fetcher

Crypto data fetcher is a simple wrapper of the [Cryptowatch REST API](https://cryptowat.ch/docs/api) OHLCV endpoint, providing useful features such as:

- Fetch OHLCV data on various exchanges and various pairs
- Recording fetched data in a hdf5 file
- Querying only missing data (according to existing h5 records)

I personally use this to on my Raspi to get minutely data of the Kraken OHLCV on the BTC/EUR pair, as I couldn't find any free dataset available. You can setup a cron job to poll the data. Fetched data is limited by Cryptowatch to an history of **6000** ticks, for any period of time (about 4 days ago for 1m data), so keep that in mind when you're setting up your polling period.

## Installation

Install required packages:

```
pip3 install logging time schedule argparse requests numpy pandas datetime h5py --user
```
## Usage

```
Usage:
crypto-data-fetcher.py [flags]
  -h, --help                show usage and exit
  -f, --filepath string     file path in which to store the fetched data, or on which to complete existing data (default ./store.h5)
  -e, --exchange string     exchange **symbol** on which to fetch the data (exchange listing https://api.cryptowat.ch/exchanges)
  -s, --symbol string       pair symbol for which to fetch the data (find pair listing for every exchange here https://cryptowat.ch/exchanges). Ex: btceur or etheur or zecbtc etc.
  -p, --period string       time period of the data, must be one of: "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", 6h", "12h", "1d", "3d", "1w" (default 1m)
```

Usage example: fetch 1-minute BTCEUR data from kraken
```
./crypto-data-fetcher.py -f store.h5 -e kraken -s btceur -p 1m
```

## Storage of the data

Fetched data is stored in a h5 file as a chunked table using gzip compression (default compression level for h5py: 4, you can easily change the code and set a higher compression level if you wish). To read and edit data, you can use a GUI tool such as [vitables](http://vitables.org/) (Version 3.x advised). If you use the data fetcher several time with the same .h5 file as storage, all the data will be stored in the same file. Data is ordered in subgroups: exchange / pair / period

Example:
Running 
```
./crypto-data-fetcher.py -f store.h5 -e kraken -s btceur -p 1m
```
Then
```
./crypto-data-fetcher.py -f store.h5 -e coinbase -s ethusd -p 3m
```
Will both use the same data/store.h5 file, but will store the datasets in ```/kraken/btceur/1m``` and ```/coinbase/ethusd/3m```

Columns are ***always*** in that order: ```['time', 'open', 'high', 'low', close', 'volume_base', 'volume_quote'] ``` (where ```'volume_base'``` and  ``` 'volume_quote'```
refer to the volume in the base asset currency, and the volume in the quote asset currency.

## Notes

One important thing to know is that the Cryptowatch API timestamps the data regarding the **end** of the period, which can differ from other dataset. For example, a data at minute 00:01 from the Kraken API will actually be at 00:02 for the Cryptowatch API. 

All data is recorded with UTC time.

The Cryptowatch API has a rate limitation of 8 seconds of CPU time per hour. This should be more than enough to fetch data even every minute, but keep that in mind if you ever spam their API. You can query https://api.cryptowat.ch to get your remaining CPU time (in nanoseconds).
