#!/usr/bin/env python3

# Encapsulates a variety to regressor models

# Stox, a prediction engine for financial time series data

# Copyright (C) 2019 Gokalp Ozcan

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class Regressor():
    def __init__(self, kind, size, seed, verbosity):
        self.size, self.seed, self.verbosity = size, seed, verbosity
        self.needs_feature_scaling = False
        self.supports_feature_importance = True

        self.model = None

        if kind == 'LGB':
            from lightgbm import LGBMRegressor
            self.model = LGBMRegressor( boosting_type='gbdt', class_weight=None, colsample_bytree=1.0,
                                        importance_type='split', learning_rate=0.1, max_depth=-1,
                                        min_child_samples=20, min_child_weight=0.001, min_split_gain=0.001,
                                        n_jobs=-1, num_leaves=127, objective='mae',
                                        reg_alpha=0.001, reg_lambda=0.0, silent=False,
                                        subsample_for_bin=200000, subsample_freq=0,
                                        n_estimators=size, random_state=seed, verbosity=verbosity )

        elif kind == 'GBR':
            from sklearn.ensemble import GradientBoostingRegressor
            self.model = GradientBoostingRegressor( loss="lad", min_samples_leaf=11, min_samples_split=8,
                                                    n_estimators=size, random_state=seed, verbose=verbosity )

        elif kind == 'ETR':
            from sklearn.ensemble import ExtraTreesRegressor
            self.model = ExtraTreesRegressor(   n_jobs=-1, 
                                                n_estimators=size, random_state=seed, verbose=verbosity )

        elif kind == 'MLP':
            from sklearn.neural_network import MLPRegressor
            self.needs_feature_scaling = True
            self.supports_feature_importance = False
            self.model = MLPRegressor(  hidden_layer_sizes= (   int(size / 4),
                                                                int(size / 4),
                                                                int(size / 8)
                                                            ),
                                        batch_size=64,
                                        activation='relu', # logistic, tanh, relu
                                        solver='adam',
                                        alpha=0.01, #default 0.0001
                                        validation_fraction=.1,
                                        tol=1e-05, # default: 1e-04
                                        learning_rate_init=1e-05, # default 1e-03
                                        random_state=seed,
                                        verbose=verbosity,
                                        early_stopping=True,
                                        learning_rate='constant', # also 'adaptive' (sgd only)
                                        max_iter=1000)
