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

        if kind == 'LGB':
            from lightgbm import LGBMRegressor
            self.model = LGBMRegressor( boosting_type='gbdt', class_weight=None, colsample_bytree=1.0,
                                        importance_type='split', learning_rate=0.1, max_depth=-1,
                                        min_child_samples=20, min_child_weight=0.001, min_split_gain=0.001,
                                        n_jobs=-1, num_leaves=127, objective='mae',
                                        reg_alpha=0.001, reg_lambda=0.0, silent=False,
                                        subsample_for_bin=200000, subsample_freq=0,
                                        n_estimators=self.size, random_state=self.seed, verbosity=self.verbosity )

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

        elif kind == 'TPOT':
            from tpot import TPOTRegressor
            self.model = TPOTRegressor(     generations=100, population_size=100, offspring_size=None,
                                            mutation_rate=0.9, crossover_rate=0.1,
                                            scoring='neg_mean_absolute_error', cv=4,
                                            subsample=1.0, n_jobs=-1,
                                            max_time_mins=None, max_eval_time_mins=360,
                                            random_state=None, config_dict=None,
                                            template=None, use_dask=False,
                                            periodic_checkpoint_folder=f'{BASE_DIR}/tpot-pipelines',
                                            early_stop=5, verbosity=2,
                                            disable_update_check=True)

        else:
            print(f"Unrecognised regressor type '{kind}'")
