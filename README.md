# Stox

Stox is a simple machine learning system for making short term future predictions on financial time series data.

Various types of regression learners are supperted from [scikit-learn](https://scikit-learn.org) and [LightGBM](https://github.com/microsoft/LightGBM). [TA-Lib](https://github.com/mrjbq7/ta-lib) is used for calculating technical indicators and chart pattern recognition.

Notable features:

* Domain-aware imputation for missing data and resampling to any arbitrary period supported by Pandas,

* 14 different technical indicators applied across different rolling windows of past data,

* Outlier detection and filtering,

* A scoring system based on the predicted price change and prediction confidence per ticker,

* Gap detection, so that only the actual data representing a current company is used, in case the same ticker code had been used for another company in the past.

## Prerequisites

* Python 3 - most extensively tested on Python 3.6

* TA-Lib C library for successful installation of its Python wrapper. Follow the instructions at [TA-Lib documentation](https://github.com/mrjbq7/ta-lib/blob/master/README.md)

* Python libraries numpy, pandas, TA-Lib, lightgbm, scikit-learn, SQLAlchemy, PyYAML. Install using the included requirements.txt: `pip3 install -r requirements.txt`

## The Data

Stox comes with batteries included. `stox.db` is an SQLite database of the daily time series data in row format `ticker, date, open, high, low, close, volume`

## Sampling and Prediction

By default, the daily time series data is resampled to weekly. In this case, the start day of the week is the current day of week at runtime, with weekend days corresponding to Friday. With weekly resampling, if Stox is run on 21 Oct 2019, with a lookforward value of one (default), the predictions will be for the 28 Oct 2019 - one week into the future.

Passing in `--resample no` will turn off resampling. Note that this will increase the memory requirement greatly since there will be many more samples at daily frequency than the default resampling frequency of weekly.

There is no hard requirement for the data to be at daily frequency, so for example 15-minute data could be used just as is.

## Usage

```
stox.py [-h] [--ticker TICKER] [--index INDEX] [--ratio RATIO]
               [--size SIZE] [--seed SEED] [--verbose VERBOSE]
               [--lookback LOOKBACK] [--lookfwd LOOKFWD] [--resample RESAMPLE]
               [--regressor REGRESSOR]

optional arguments:
  -h, --help            show this help message and exit
  --ticker TICKER       Single ticker code, or _MOCK_EASY or _MOCK_HARD for
                        mock tests
  --index INDEX         One of the keys of stock indices as defined in
                        data/indices.yml, to populate the dataset with.
                        Default: XAO
  --ratio RATIO         Denominator of train/test split ratio. Default is 5,
                        meaning a 80/20 percent train/test split.
  --size SIZE           Number of estimator trees to build. Default: 240.
  --seed SEED           Seed for initialising the model weights with
  --verbose VERBOSE     Integer greater than zero. Greater this number, more
                        info is printed during run. Default: 1.
  --lookback LOOKBACK   The number of periods for look-back features. Default:
                        6.
  --lookfwd LOOKFWD     The number of periods into the future to predict at.
                        Default: 1.
  --resample RESAMPLE   Period size. 'no' to turn off resampling, or any
                        pandas-format resampling specification. Default is
                        weekly resampling on the current workday
  --regressor REGRESSOR
                        String alias for the regressor model to use, as
                        defined in regressor.py. Default: LGB
```

### The Regressors

* `LGB`: [LightGBM Regressor](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMRegressor.html)

* `GBR`: [Scikit-learn's Gradient Boosting Regressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html)

* `ETR` : [Extra-Trees](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesRegressor.html)

* `MLP` : [Multi-layer Perceptron](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPRegressor.html)

* `KTF` : [Tensorflow via Keras](https://keras.io/scikit-learn-api/)

## Predictions and Performance Metrics

A table of per-ticker prediction results will be printed at the end. The results are sorted based on 'potential', where a high value of this metric can be interpreted as a BUY, and a low, negative value as a SELL signal.

[Here's a results example](https://github.com/alpozcan/stox/blob/master/results/2019-12-23-12-30-19.csv) that was produced using `--resample 'W-THU'`.

Result Attributes:

* `predicted_at` : The date stamp of the most recent sample of data for the ticker that was used for prediction.

* `prediction` : The predicted percentage change for the ticker code.

* `volatility` : Average change in price based on all test samples.

* `MAE` : Mean Absolute Error against test samples.

* `alpha` : `volatility / MAE`

* `var_score`: Explained variance score.

* `train_samples`: The number of samples for the ticker code that were used in training the model.

* `test_samples` : The number of samples for the ticker code that were used in testing the model for computing `MAE` and `var_score`.

* `potential` : `prediction * alpha`

Full results will be saved in a date stamped CSV file under `results/`.

In addition to the per-ticker results presented in the table, overall volatility, error and alpha metrics will also be printed. These are computed based on ALL test samples. The `alpha` score is the single most important metric for evaluating the model performance, and usually comes in at around ~34 with the included data.

WIth the provided data and using the default configuration, a run should not take more than a few minutes on a reasonably modern CPU. It takes about 2 minutes on a 4 core / 8 thread Intel i5 8259u.

## Mock Testing with Synthetic Data

It is possible to run Stox with mock data generated at runtime via special ticker codes passed as arguments:

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

* Implement a more efficient way to store lookback features (i.e. day -1, day -2 etc). Currently we use a 'ribbon' of trailing features for each LOOKBACK number of past periods, which means there's a lot of duplication in the data set. Similarly for the 'market' features that get tacked on alongside every ticker sample. Perhaps a proper implementation of an LSTM or GRU should fit well here.


## License

This software is licensed under GNU GENERAL PUBLIC LICENSE, Version 3. Check the LICENSE file for the full license text. 

Stox is Copyright (C) 2019 Gokalp Ozcan.

## Disclaimer

Stox and the bundled data is provided for educational purposes only, and its predictions alone should not be used in trading of actual money. There is no guarantee on the correctness or applicability of this program. By using this program, you accept to take full responsibility for any losses, financial or otherwise.
