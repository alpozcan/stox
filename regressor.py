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
    def __init__(self, kind, size, seed, verbosity, val_x, val_y):
        self.kind, self.size, self.seed, self.verbosity = kind, size, seed, verbosity
        self.val_x, self.val_y = val_x, val_y # Validation data for the Keras model
        self.needs_feature_scaling = False
        self.supports_feature_importance = True

        self.model = self.init_model(kind)


    def init_model(self, kind):
        if kind == 'LGB':
            from lightgbm import LGBMRegressor
            model = LGBMRegressor( boosting_type='gbdt', class_weight=None, colsample_bytree=1.0,
                                        importance_type='split', learning_rate=0.1, max_depth=-1,
                                        min_child_samples=20, min_child_weight=0.001, min_split_gain=0.001,
                                        n_jobs=-1, num_leaves=127, objective='mae',
                                        reg_alpha=0.001, reg_lambda=0.0, silent=False,
                                        subsample_for_bin=200000, subsample_freq=0,
                                        n_estimators=self.size, random_state=self.seed, verbosity=self.verbosity )

        elif kind == 'GBR':
            from sklearn.ensemble import GradientBoostingRegressor
            model = GradientBoostingRegressor( loss="lad", min_samples_leaf=11, min_samples_split=8,
                                                    n_estimators=self.size, random_state=self.seed, verbose=self.verbosity )

        elif kind == 'ETR':
            from sklearn.ensemble import ExtraTreesRegressor
            model = ExtraTreesRegressor(   n_jobs=-1, 
                                                n_estimators=self.size, random_state=self.seed, verbose=self.verbosity )

        elif kind == 'MLP':
            from sklearn.neural_network import MLPRegressor

            self.needs_feature_scaling = True
            self.supports_feature_importance = False

            model = MLPRegressor(  hidden_layer_sizes= (    int(self.size / 4),
                                                            int(self.size / 4),
                                                            int(self.size / 8)
                                                        ),
                                        batch_size=64,
                                        activation='relu', # logistic, tanh, relu
                                        solver='adam',
                                        alpha=0.01, #default 0.0001
                                        validation_fraction=.1,
                                        tol=1e-05, # default: 1e-04
                                        learning_rate_init=1e-05, # default 1e-03
                                        random_state=self.seed,
                                        verbose=self.verbosity,
                                        early_stopping=True,
                                        learning_rate='constant', # also 'adaptive' (sgd only)
                                        max_iter=1000)

        elif kind == 'KTF':
            from tensorflow.keras.wrappers.scikit_learn import KerasRegressor
            from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, TensorBoard, ProgbarLogger

            self.needs_feature_scaling = True
            self.supports_feature_importance = False

            callbacks = [TensorBoard()]
            if self.val_x is not None and self.val_y is not None:
                callbacks += [EarlyStopping    (monitor='val_loss', min_delta=.001, patience=13, verbose=self.verbosity)]
                callbacks += [ReduceLROnPlateau(monitor='val_loss', min_delta=.002, factor=1/3, patience=10, verbose=self.verbosity)]

            model =(KerasRegressor(build_fn=self.keras_model,
                                        epochs=1000,
                                        batch_size=64,
                                        verbose=self.verbosity,
                                        callbacks=callbacks,
                                        validation_data=(self.val_x, self.val_y)
                                        )
            )
        
        else:
            print(f"Unrecognised regressor type '{kind}'")

        if self.verbosity > 0:
            print(model)

        return model

    def keras_model(self):
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.optimizers import SGD, RMSprop, Adam, Adagrad, Adadelta, Adamax, Nadam
        from tensorflow.keras.layers import Dense, Activation, BatchNormalization, PReLU

        model = Sequential()

        model.add(Dense(int(self.size / 4), activation='relu', input_shape=(((self.val_x.shape)[1]),)))
        model.add(Dense(int(self.size / 4), activation='relu'))
        model.add(Dense(int(self.size / 8), activation='relu'))
        model.add(Dense(1))

        optimiser = Adam(lr=1e-03, epsilon=None, decay=0.0, amsgrad=False)
        model.compile(loss='mean_absolute_error', optimizer=optimiser)
        if self.verbosity > 0:
            print(model.summary())

        return model
