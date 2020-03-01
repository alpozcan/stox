#!/usr/bin/env bash

time nice ./stox --load --regressor LGB_hypopt --verbose 0 | tee logs/grid_search.log
