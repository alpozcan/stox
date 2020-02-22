#!/usr/bin/env python3

# Encapsulates a variety to regressor models

# Stox, a prediction engine for financial time series data

# Copyright (C) 2017-2020 Gokalp Ozcan

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

import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

class Regressor():
    def __init__(self, kind, size, seed, verbosity):
        self.kind, self.size, self.seed, self.verbosity = kind, size, seed, verbosity

        if kind.startswith('LGB'):
            from lightgbm import LGBMRegressor
            self.model = LGBMRegressor( boosting_type='gbdt', colsample_bytree=0.8,
                                        min_child_samples=20, min_child_weight=0.01,
                                        n_estimators=self.size, num_leaves=63, learning_rate=0.1,
                                        reg_alpha=0.001, reg_lambda=1, objective='mae',
                                        random_state=self.seed, verbosity=self.verbosity, n_jobs=-1 )

            if kind == 'LGB_hypopt': # LightGBM with hypopt hyperparameter optimisation
                from hypopt import GridSearch
                param_grid = [{
                        'n_estimators': [ self.size ],
                        'objective': [ 'mae' ],
                        # 'boosting_type': [ 'gbdt', 'dart', 'goss', 'rf' ],
                        # 'num_leaves': [ 31, 63, 127 ],
                        # 'learning_rate': [ 0.05, 0.1, 0.15 ],
                        # 'subsample_for_bin': [ 200000, 500000 ],
                        # 'min_child_samples': [ 10, 20, 30 ],
                        # 'min_child_weight': [ 0.001, 0.01, 0.1 ],
                        # 'min_split_gain': [ 0.0, 0.001, 0.01 ],
                        'colsample_bytree': [ 1.0, 0.8, 0.6 ],
                        # 'reg_alpha': [ 0.001, 0.01, 0.1 ],
                        # 'reg_lambda': [ 0.01, 0.1, 1],
                        'verbosity': [ 0 ],
                    }]
                self.model = GridSearch(model=self.model, param_grid=param_grid, num_threads=1, seed=self.seed)

        elif kind == 'GBR':
            from sklearn.ensemble import GradientBoostingRegressor
            self.model = GradientBoostingRegressor( loss="lad", min_samples_leaf=11, min_samples_split=8,
                                                    n_estimators=self.size, random_state=self.seed, verbose=self.verbosity )

        elif kind == 'RFR':
            from sklearn.ensemble import RandomForestRegressor
            self.model = RandomForestRegressor(n_estimators=self.size, random_state=self.seed, verbose=self.verbosity, n_jobs=-1)

        elif kind == 'ETR':
            from sklearn.ensemble import ExtraTreesRegressor
            self.model = ExtraTreesRegressor(n_estimators=self.size, random_state=self.seed, verbose=self.verbosity, n_jobs=-1)

        elif kind == 'XGB':
            from xgboost import XGBRegressor
            self.model = XGBRegressor(  n_estimators=self.size, max_depth=15, learning_rate=0.05,
                                        min_child_weight=3, subsample=0.6,
                                        colsample_bylevel=0.6, colsample_bytree=0.9,
                                        reg_lambda=100, reg_alpha=0.01,
                                        random_state=self.seed, verbose=self.verbosity, n_jobs=-1)

        else:
            print(f"Unrecognised regressor type '{kind}'")
