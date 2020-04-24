def reduce_features(subsampling=0.8):
    if subsampling < 1.0: # first, eliminate some useless features
        fi = pd.DataFrame(model.estimators_[0].feature_importances_, index=features, columns=['importance']).sort_values('importance', ascending=False)

        important_features = list(fi.head(round(len(features) * subsampling)).index)
        if VERBOSE > 1:
            print('important features:', important_features, f'({len(important_features)})')
        unimportant_features = [ f for f in features if f not in important_features]
        
        X_train.drop(unimportant_features, axis=1, inplace=True)
        X_test.drop(unimportant_features, axis=1, inplace=True)
        predictors.drop(unimportant_features, axis=1, inplace=True)

        model.fit(X_train, y_train) # fit a new model on reduced set of features
        print('alpha (reduced featureset):', alpha(y_test , model.predict(X_test)))