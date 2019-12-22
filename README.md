# stox

Stox is a simple machine learning system for making short term future predictions on financial time series data.

It uses [LightGBM](https://github.com/microsoft/LightGBM) for a gradient-boosting learner and [TA-Lib](https://github.com/mrjbq7/ta-lib) for technical indicators and chart pattern recognition.

Notable features:

* Domain-aware imputation for missing data and resampling to any arbitrary period supported by Pandas,

* 14 different technical indicators applied across different rolling windows of past data,

* Simple outlier detection and filtering,

* A scoring system based on the predicted price change and prediction confidence per ticker,

* Gap detection, so that only the actual data representing a current company is used, in case the same ticker code had been used for another company in the past.

## Prerequisites

* Python 3 - most extensively tested on Python 3.6

* TA-Lib C library for successful installation of its Python wrapper. Follow the instructions at [TA-Lib documentation](https://github.com/mrjbq7/ta-lib/blob/master/README.md)

* Python libraries numpy, pandas, TA-Lib, lightgbm, scikit-learn, SQLAlchemy, PyYAML. Install using the included requirements.txt: `pip3 install -r requirements.txt`

## The Data

Stox comes with batteries included. The provided end-of-day time series data covers the stocks listed in ASX All Ordinaries index for a period between 2003-03-01 and 2019-10-25.

Three sources for various types of data are provided in the data/ subdirectory:

* `stox.db` : SQLite database of the daily time series data in row format `ticker, date, open, high, low, close, volume`

* `indices.yml` : Defines groups of ticker codes to use for training and prediction.

* `companies/ASXListedCompanies.csv` : List of all ASX listed companies as [published by ASX](https://www.asx.com.au/asx/research/listedCompanies.do) with company name and sector information. This is not used currently.

## Sampling and Prediction

By default, the daily time series data is resampled to weekly. The last work day of the week depends on the week day at runtime, i.e. if you run stox on 21 Oct 2019, with a lookforward value of one (default), the predictions will be for the 28 OCt 2019 (one week into the future).

Passing in `--resample no` will turn off resampling. Note that this will increase the memory requirement greatly since there will be many more samples at daily frequency than the default resampling frequency of weekly.

There is no hard requirement for the data to be at daily frequency, so for example 15-minute data could be used just as is.

## Usage

```
stox.py [-h] [--ticker TICKER] [--index INDEX] [--ratio RATIO]
        [--size SIZE] [--seed SEED] [--verbose VERBOSE]
        [--lookback LOOKBACK] [--lookfwd LOOKFWD] [--resample RESAMPLE]

optional arguments:
  -h, --help           show this help message and exit
  --ticker TICKER      single ticker code, or _MOCK_EASY or _MOCK_HARD for mock tests
  --index INDEX        one of the keys of stock indices as defined in data/indices.yml, to populate the dataset with. Default: XAO
  --ratio RATIO        denominator of train/test split ratio. Default is 4, meaning a 75/25 percent train/test split.
  --size SIZE          Number of estimator trees to build. Default: 240.
  --seed SEED          Seed for initialising the model weights with
  --verbose VERBOSE    Integer greater than zero. Greater this number, more info is printed during run. Default: 1.
  --lookback LOOKBACK  The number of periods for look-back features. Default: 6.
  --lookfwd LOOKFWD    The number of periods into the future to predict at. Default: 1.
  --resample RESAMPLE  Period size. 'no' for daily, or any pandas-format resampling specification. Default is weekly resampling on the current workday
```

## Predictions and Performance Metrics

A table of prediction results will be printed at the end, per ticker. The results are sorted based on 'potential', where a high value of this metric can be interpreted as BUY, and a low, negive value as SELL.

Result Attributes:

* `predicted_at` : The most recent sample of data for the ticker that was used for prediction.

* `prediction` : The predicted percentage change for the ticker code.

* `volatility` : Average change in price based on all samples.

* `MAE` : Mean Absolute Error against test data.

* `alpha` : `MAE / volatility`

* `var_score`: Explained variance score.

* `train_samples`: The number of samples for the ticker code that were used in training the model.

* `test_samples` : The number of samples for the ticker code that were used in testing the model for computing `MAE` and `var_score`.

* `potential` : `prediction * alpha`

Full results will be saved in a date stamped CSV file under `results/`.

In addition to the per-ticker results presented in the table, overall volatility, error and alpha metrics will also be printed and are computed based on ALL test samples. The `alpha` score is the most important single metric for evaluating the model performance, and usually comes in at around ~35 with the included data.

WIth the provided data and using the default configuration, a run should not take more than a few minutes on a reasonably modern CPU. On a 4 core / 8 thread Intel i5 8259u, it takes about 2 minutes.

## Mock Testing with Synthetic Data

It is possible to run stox with using mock data generated at runtime via special ticker codes passed as arguments:

* `--ticker _MOCK_EASY` : Monotonous data that is very predictable. Should result in an alpha score of ~2600.

* `--ticker _MOCK_HARD` : Gaussian-distributed random data that should be unpredictable. Should result in an alpha score of below 30 and possibly negative.

## Contributing

**Pull Requests, suggestions, bug reports and forks would be most welcome and are encouraged.**

## TODO / Feature Wishlist

* In addition to weekly, include daily failures for the last LOOKBACK number of days

* Add a second pass with all samples used for training

* Save the model trained above to a file if -s switch is passed (date stamped)

* Load a saved model if one for the current day exists, and use near-realtime predictors to predict on it intra day.

* Find out why using the close price directly for `d['price']` sinks the scores!

* Implement a more efficient way to store lookback features (i.e. day -1, day -2 etc). Currently we use a 'ribbon' of trailing features for each LOOKBACK number of past periods, which means there's a lot of duplication in the data set. Similarly for the 'market' features that get tacked on alongside every ticker sample.

## License

This software is licensed under GNU GENERAL PUBLIC LICENSE, Version 3. Check the LICENSE file for the full license text. 

Stox is Copyright (C) 2019 Gokalp Ozcan.

## Disclaimer

Stox and the bundled data is provided for educational purposes only, and its predictions alone should not be used in trading of actual money. There is no guarantee on the correctness or applicability of this program; you are responsible for any losses, financial or otherwise.
