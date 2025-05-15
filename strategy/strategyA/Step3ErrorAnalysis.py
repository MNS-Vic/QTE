#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 14 10:33:51 2022

@author: heshuangji
"""

from __future__ import division
import warnings
import sys;sys.path.append(r"/home/heshuangji/FactorResearch")
from apitool import *
warnings.filterwarnings("ignore")
from queue import Queue
import pandas as pd
import numpy as np
import time
from statsmodels.tsa.stattools import adfuller
from mlfinlab.features.fracdiff import frac_diff_ffd
import os
from sklearn import metrics
from sklearn.metrics import log_loss, accuracy_score
from sklearn.tree import DecisionTreeClassifier,DecisionTreeRegressor
from sklearn.tree import plot_tree,export_text,export_graphviz
from sklearn.ensemble import BaggingClassifier,BaggingRegressor
import pickle
import lightgbm as lgb
#%%
open_=pd.read_csv(r'/home/heshuangji/Data/DATA_DAY_WEIGHT/Open.csv',index_col=0)
close_=pd.read_csv(r'/home/heshuangji/Data//DATA_DAY_WEIGHT/Close.csv',index_col=0)
close0_=pd.read_csv(r'/home/heshuangji/Data//DATA_DAY_ORIGIN/Close.csv',index_col=0)
ret=((close_-open_)/close0_*100).shift(-1)
ret['BU']=ret['BU'][ret['BU'].index>='2015-01-01']
dfy=ret.stack(dropna=False)
#
ratio=pd.read_csv(r'/home/heshuangji/FactorResearch/Amount_1minavg.csv',index_col=0)
ratio.ratio=ratio.ratio/ratio.ratio['RB']*100
weight=ret.applymap(lambda x:np.nan)
weight.loc[weight.index[0],:]=ratio.ratio
weight=weight.fillna(method='ffill')
#
corr0=pd.read_csv(r"/home/heshuangji/FactorResearch/Matrix_Corr(kendall).csv",index_col=0)
ic=pd.read_csv(r"/home/heshuangji/FactorResearch/MIC_xy.csv",index_col=0)
#
used_col=ic['mic'].sort_values()[:].index
dfx=pd.read_csv(r'/home/heshuangji/FactorResearch/df_2nd.csv')
dfx.index=pd.MultiIndex.from_frame(dfx[['Unnamed: 0', 'Unnamed: 1']])
dfx=dfx.drop(['Unnamed: 0', 'Unnamed: 1'],axis=1).loc[:,used_col]
dfx['weight']=weight.stack()
dfx['y']=dfy
dfx=dfx.dropna(subset=['y'])
#--------error Decomposition----------
'''
针对单个数据点分解
'''
from sklearn.metrics import mean_squared_error  as  mse  
from sklearn.metrics import mean_absolute_error as  mae  
predict_train=dict([(k,[]) for k in fs_rd.keys()])
predict_test=dict([(k,[]) for k in fs_rd.keys()])
for k in num_feature:
    print(k)
    data=pkl_load(r'/home/heshuangji/FactorResearch/ModelSave/lgb1_%s.pkl'%(k))
    for i,gbm in enumerate(data['model']):
        col=gbm.feature_name()  
        #
        y_pred=gbm.predict(X_train[col],num_iteration=140)
        y_true=y_train.values
        predict_train[k].append(y_pred)
        #
        y_pred=gbm.predict(X_test[col],num_iteration=140)
        y_true=y_test.values
        predict_test[k].append(y_pred)
y_pred=[]
for k in num_feature:
    y_pred.append(pd.DataFrame(predict_test[k]).T)
y_pred=pd.concat(y_pred,axis=1)  
y_pred.columns=range(y_pred.shape[1])
var=y_pred.var(axis=1)
error=y_pred.apply(lambda x:(x-y_test.values)**2).mean(axis=1)
error.plot(label='error',legend=True);var.plot(label='var',legend=True,secondary_y=True)
#