import pandas as pd

from sklearn.compose import make_column_transformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, OneHotEncoder
from sklearn.preprocessing import StandardScaler 
from sklearn.linear_model import LinearRegression, LogisticRegression


class UserPredictor:
    def __init__(self):
        self.model = LogisticRegression(max_iter=1000)
        
    def fit(self, train_users, train_logs, train_y):
        # train data preprocessing 
        self.training_data, self.training_trans, self.training_features = self.data_preprocessing(train_users, train_logs)
        
        # select features to train        
        self.xcols = self.training_features
        
        # build data pipeline       
        pipe = Pipeline([
            ("trans", self.training_trans),
            ("lr", self.model)
        ])
       
        self.model_after = pipe.fit(self.training_data[self.xcols], train_y['y'])
        
        return self.model_after
    
    def predict(self, test_users, test_logs):        
        # test data preprocessing 
        self.testing_data, self.testing_trans, self.testing_features = self.data_preprocessing(test_users, test_logs)
        
        # select features to test, then store in df 
        y_preds = self.model_after.predict(self.testing_data[self.testing_features])
        
        # return as numpy array
        return y_preds
    
    def data_preprocessing(self, users, logs):        
        # get the frequency of total time, count of url
        logs_total_seconds = logs.groupby('user_id', as_index=False).agg({"seconds": "sum",
                                                                       "url": "count"})     
        # combine two table
        data = pd.merge(users, logs_total_seconds, how='left', left_on="user_id", right_on="user_id")
        
        # remove NaN
        data["seconds"] = data.seconds.fillna(0)
        data["url"] = data.url.fillna(0)
        
        ## Add Checkers
        # 1. create age group
        age_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        age_labels = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100']

        data['age_group'] = pd.cut(data['age'], age_bins, right=False, labels=age_labels)   

        # 2. create age group
        ppa_bins = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000]
        ppa_labels = ['0-250', '250-500', '500-750', '750-1000', '1000-1250', '1250-1500', '1500-1750', '1750-2000']
        data['past_purchase_amt_group'] = pd.cut(data['past_purchase_amt'], ppa_bins, right=False, labels=ppa_labels)

        # 3. TODO: create data group
        
        # transform 
        trans = make_column_transformer(
            (PolynomialFeatures(degree=1), ["seconds", "url"]),
            (StandardScaler(), ["seconds", "url"]),
            (OneHotEncoder(), ["badge", "age_group", "past_purchase_amt_group"])
        )
        
        features = ["badge", "seconds", "url", "age_group", "past_purchase_amt_group"]
        
        return data, trans, features
