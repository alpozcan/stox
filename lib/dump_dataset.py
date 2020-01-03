#!/usr/bin/env python3

# Functions for dumping the dataset to file

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

import sys
import pandas as pd
from random import shuffle

def dump_to_csv(    X_train, y_train, X_val, y_val, X_test, y_test,
                    mode='auto_ml', out_file='/mnt/d/stox-dataset-sorted.csv'):

    train = pd.concat([X_train, y_train], axis=1)
    val = pd.concat([X_val, y_val], axis=1)
    test = pd.concat([X_test, y_test], axis=1)

    if mode == 'auto_ml':
        train['SPLIT'] = 'TRAIN'
        val['SPLIT'] = 'VALIDATE'
        test['SPLIT'] = 'TEST'

    dataset = pd.concat([train, val, test], axis=0).sort_index()
    dataset.to_csv(out_file, index=False)
    print('Dumped the dataset to', out_file)
    sys.exit()
