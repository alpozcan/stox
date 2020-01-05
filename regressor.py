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

class Regressor():
    def __init__(self, kind, size, seed, verbosity):
        self.kind, self.size, self.seed, self.verbosity = kind, size, seed, verbosity
        self.needs_feature_scaling = True if kind in ['MLP', 'KTF'] else False
        self.supports_feature_importance = True

    def init_model(self, X_val=None, y_val=None):
        self.input_dim = X_val.shape[1] if len(X_val) > 0 else None

        if self.kind == 'LGB':
            from lightgbm import LGBMRegressor
            self.model = LGBMRegressor( boosting_type='gbdt', class_weight=None, colsample_bytree=1.0,
                                        importance_type='split', learning_rate=0.1, max_depth=-1,
                                        min_child_samples=20, min_child_weight=0.001, min_split_gain=0.001,
                                        n_jobs=-1, num_leaves=127, objective='mae',
                                        reg_alpha=0.001, reg_lambda=0.0, silent=False,
                                        subsample_for_bin=200000, subsample_freq=0,
                                        n_estimators=self.size, random_state=self.seed, verbosity=self.verbosity )

        elif self.kind == 'GBR':
            from sklearn.ensemble import GradientBoostingRegressor
            self.model = GradientBoostingRegressor( loss="lad", min_samples_leaf=11, min_samples_split=8,
                                                    n_estimators=self.size, random_state=self.seed, verbose=self.verbosity )

        elif self.kind == 'ETR':
            from sklearn.ensemble import ExtraTreesRegressor
            self.model = ExtraTreesRegressor(   n_jobs=-1, 
                                                n_estimators=self.size, random_state=self.seed, verbose=self.verbosity )

        elif self.kind == 'MLP':
            from sklearn.neural_network import MLPRegressor

            self.supports_feature_importance = False

            self.model = MLPRegressor(  hidden_layer_sizes= (   int(self.size / 4),
                                                                int(self.size / 4),
                                                                int(self.size / 8)
                                                            ),
                                        batch_size=128,
                                        activation='relu', # logistic, tanh, relu
                                        solver='sgd',
                                        alpha=1e-03, # default 1e-04
                                        validation_fraction=.1,
                                        tol=1e-05, # default: 1e-04
                                        learning_rate_init=5e-04, # default 1e-03
                                        random_state=self.seed,
                                        verbose=self.verbosity,
                                        early_stopping=True,
                                        learning_rate='adaptive',
                                        max_iter=1000)

        elif self.kind == 'KTF':
            from tensorflow.keras.wrappers.scikit_learn import KerasRegressor
            from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, TensorBoard, ProgbarLogger

            self.supports_feature_importance = False

            callbacks =  [EarlyStopping     (monitor='val_loss', min_delta=1e-05, patience=13, verbose=self.verbosity)]
            callbacks += [ReduceLROnPlateau (monitor='val_loss', min_delta=1e-05, factor=1/5, patience=10, verbose=self.verbosity)]
            callbacks += [ProgbarLogger     (count_mode='samples', stateful_metrics=None)]
            # callbacks +=  [TensorBoard()]

            self.model =(KerasRegressor (   build_fn=self.keras_model,
                                            epochs=1000,
                                            batch_size=128,
                                            random_state=self.seed,
                                            verbose=False,
                                            callbacks=callbacks,
                                            validation_data=(X_val, y_val)
                                        ))

        else:
            print(f"Unrecognised regressor type '{self.kind}'")

        if self.verbosity > 0:
            print(self.model)

        return self.model

    def keras_model(self):
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.optimizers import SGD, RMSprop, Adam, Adagrad, Adadelta, Adamax, Nadam
        from tensorflow.keras import layers

        model = Sequential()

        model.add(layers.Dense(int(self.size / 4), activation='relu', input_shape=(self.input_dim,)))
        model.add(layers.Dense(int(self.size / 4), activation='relu'))
        model.add(layers.Dense(int(self.size / 8), activation='relu'))
        model.add(layers.Dense(1))

        optimiser = Adam(lr=1e-03, epsilon=None, decay=0.0, amsgrad=False)
        model.compile(loss='mean_absolute_error', optimizer=optimiser)
        if self.verbosity > 0:
            print(model.summary())

        return model
