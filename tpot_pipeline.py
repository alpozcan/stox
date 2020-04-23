import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split

# NOTE: Make sure that the outcome column is labeled 'target' in the data file
tpot_data = pd.read_csv('PATH/TO/DATA/FILE', sep='COLUMN_SEPARATOR', dtype=np.float64)
features = tpot_data.drop('target', axis=1)
training_features, testing_features, training_target, testing_target = \
            train_test_split(features, tpot_data['target'], random_state=None)

# Average CV score on the training set was: -4.360707124345849
exported_pipeline = LGBMRegressor(colsample_bytree=0.69, learning_rate=0.05, min_child_samples=20, min_child_weight=0.001, min_split_gain=0.0, n_estimators=200, n_jobs=-1, num_leaves=63, objective="mae", reg_alpha=0.01, reg_lambda=0.1)

exported_pipeline.fit(training_features, training_target)
results = exported_pipeline.predict(testing_features)
