#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 17:40:43 2021

@author: heshuangji

plan for once only
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
from sklearn.ensemble import BaggingClassifier,BaggingRegressor
import pickle
import lightgbm as lgb

#%%
rev_num=(11-1)/2
#
open_=pd.read_csv(r'/home/heshuangji/Data/DATA_DAY_WEIGHT/Open.csv',index_col=0)
close_=pd.read_csv(r'/home/heshuangji/Data//DATA_DAY_WEIGHT/Close.csv',index_col=0)
close0_=pd.read_csv(r'/home/heshuangji/Data//DATA_DAY_ORIGIN/Close.csv',index_col=0)
ret=((open_.shift(-7)-open_)/close0_*100).shift(-1)
ret['BU']=ret['BU'][ret['BU'].index>='2015-01-01']
ret.loc[:,['SF','SM']]=np.nan
ret7=ret
temp=ret.parallel_apply(lambda x:myqcut_ts(x,num=11,expanding=600))
dfy=pd.concat([temp[n].dropna() for n in temp.columns],axis=1,ignore_index=True).sort_index()
dfy.columns=temp.columns
#    
ratio=pd.read_csv(r'/home/heshuangji/Data/Amount_1minavg.csv',index_col=0)
temp=ratio.ratio
temp=temp/temp['RB']*100
weight=ret.applymap(lambda x:np.nan)
weight.loc[weight.index[0],:]=temp
weight=weight.fillna(method='ffill')
#
# corr0=pd.read_csv(r"/home/heshuangji/Data/Matrix_Corr(kendall).csv",index_col=0)
# ic=pd.read_csv(r"/home/heshuangji/Data/MIC_xy.csv",index_col=0)
#
dfx=pd.read_csv(r'/home/heshuangji/Data/df_2nd.csv')
dfx.index=pd.MultiIndex.from_frame(dfx[['Unnamed: 0', 'Unnamed: 1']])
dfx=dfx.drop(['Unnamed: 0', 'Unnamed: 1'],axis=1)
dfx['weight']=weight.stack()

dfx.loc[ret.stack().index,'ret']=ret.stack()
dfx.loc[dfy.stack().index,'y']=dfy.stack()
dfx['yret']=ret.stack(dropna=False)
dfx=dfx.dropna(subset=['yret','y'])

#%%Bench0
# benchtype=ic.abs().sort_values('mic').index[-1]
# flag0=pd.DataFrame(index=corr0.index,columns=np.arange(-0.0,-0.9,-0.2))
# for i in  flag0.columns:
#     for n in corr0.index:
#         if corr0[benchtype][n]<=i:flag0.loc[n,i]=-1
#         else:flag0.loc[n,i]=1
# #
# dfx_used0=(dfx/dfx.abs().median().apply(lambda x:max(1,x)) )[dfx.columns[:-2]]
# # select_feature=ic.index
# # select_feature=ic['mic'][feature_names[[selected_features]]].sort_values()[-50:].index
# select_feature=ic['mic'].sort_values()[-220:].index
# dfx_used=dfx_used0[select_feature]
# flag=flag0.loc[select_feature,:]

# res_ew=pd.DataFrame(columns=flag.columns);res_ww=pd.DataFrame(columns=flag.columns)
# for i in  flag.columns:
#     dfx_used=dfx_used*flag[i]
#     xval=dfx_used.sum(axis=1).unstack()
#     yval=dfx['y'].unstack()
#     wval=dfx['weight'].unstack()
#     out=calc_pnl(xval,yval,wval,title=i)
#     res_ew[i]=out.sum(axis=1)
#     res_ww[i]=(wval*out).sum(axis=1)
# res_ew.cumsum().plot()    
# res_ww.cumsum().plot()  
# res_ew.sum().plot(kind='bar')
# res_ww.sum().plot(kind='bar')
#%%Bench1
train=dfx.loc[idx[dfx.index.levels[0][:-200],:],:]
test=dfx.loc[idx[dfx.index.levels[0][-200]:,:],:]
X_train=train.loc[:,train.columns[:-3]];y_train=train['y'];W_train=train['weight']
yret_train=train['yret']
X_test=test.loc[:,test.columns[:-3]];y_test=test['y'];W_test=test['weight']
yret_test=test['yret']
#
num_feature=[0.5,0.7]
num_bagging=[]
fs_rd=dict( [(k,[]) for k in num_feature])
# fs_ew=dict( [(k,[]) for k in num_feature])
for nf in num_feature:
    nfr=int(nf*X_train.shape[1])
    temp=N_estimator(samples=X_train.shape[1],k=nfr)
    num_bagging.append(temp)
    for i in range(temp):
        fs_rd[nf].append(X_train.sample(n=nfr,replace=False,
                                        weights=None,axis=1).columns)
        # fs_ew[nf].append(X_train.sample(n=temp,replace=False,
        #                                 weights=None,axis=1).columns)        
# check=[]
# for k in fs_rd.keys():
#     a=pd.DataFrame(fs_rd[k])
#     temp=[]
#     for i in a.columns:
#         temp.append(a[i].value_counts())
#     check.append(pd.DataFrame(temp).sum())
# check=pd.DataFrame(check).sum()    

params = {
    'boosting_type': 'dart',
    'objective': 'multiclass',
    'num_class':11,
    'metric': {'multi_logloss'},
    'max_depth': 5,
    
    'learning_rate': 0.1,
    'feature_fraction': 1.0,
    'bagging_fraction': 0.8,
    'bagging_freq': 2,
    'extra_trees ':True,
    # 'lambda_l1':30,
    # 'lambda_l2':20,
    'min_data_in_leaf':12,
    'path_smooth':0.1,    
    'drop_rate':0.5,
    'skip_drop':0.8,
    'num_threads':0,
    'verbose':-1
}
for k,v in fs_rd.items():
    print(k)
    result={'model':[],'error':[]}
    for col in v:
        lgb_train = lgb.Dataset(X_train[col], y_train,
                                weight=W_train, free_raw_data=False)
        lgb_test = lgb.Dataset(X_test[col], y_test, reference=lgb_train,
                               weight=W_test, free_raw_data=False)
        evals_result = {}  # to record eval results for plotting
        # train
        gbm = lgb.train(params,
                        lgb_train,
                        num_boost_round=300,
                        valid_sets=[lgb_train, lgb_test],
                        evals_result=evals_result,
                        verbose_eval=10)
        result['model'].append(gbm)
        result['error'].append(evals_result)
    pkl_save(r'/home/heshuangji/FactorResearch/ModelSave/lgb1_%s.pkl'%(k), result)
#%%after analysis
#--------train_test error----------
for nf in num_feature:
    data=pkl_load(r'/home/heshuangji/FactorResearch/ModelSave/lgb1_%s.pkl'%(nf))
    #
    error_train=[];error_test=[]
    for i,evals_result in enumerate(data['error']):
        temp1=pd.DataFrame(evals_result['training'])
        temp2=pd.DataFrame(evals_result['valid_1'])
        temp1.columns=[c+'_%s_train'%(i) for c in temp1.columns]
        temp2.columns=[c+'_%s_test'%(i) for c in temp2.columns]
        error_train.append(temp1);error_test.append(temp2)
    traine=pd.concat(error_train,axis=1)
    teste=pd.concat(error_test,axis=1)
    traine.mean(axis=1).plot(label='train_'+str(nf),legend=True)
    teste.mean(axis=1).plot(label='test_'+str(nf),legend=True)
ax = lgb.plot_metric(evals_result, metric='multi_logloss')
  
#---------data get--------- 
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
        y_pred=gbm.predict(X_train[col],num_iteration=None)
        y_true=y_train.values
        predict_train[k].append(y_pred)
        #
        y_pred=gbm.predict(X_test[col],num_iteration=None)
        y_true=y_test.values
        predict_test[k].append(y_pred)
#---------Error-Var analysis--------- 
y_pred=[]
for k in num_feature:
    hold=[]
    for j in range(len(predict_test[k])):
        temp=pd.DataFrame(predict_test[k][j]).T
        hold.append((temp.T*pd.Series(temp.index.values)).sum(axis=1))
    y_pred.append(pd.DataFrame(hold).T)
y_pred=pd.concat(y_pred,axis=1)  
y_pred.columns=range(y_pred.shape[1])
var=y_pred.var(axis=1)
error=y_pred.apply(lambda x:(x-y_test.values)**2).mean(axis=1)
error.plot(label='error',legend=True);var.plot(label='var',legend=True,secondary_y=True)
#---------pnl analysis--------- 
res_bagging=pd.DataFrame(index=num_feature,columns=['train','test'])
predict_baggingtrain=[]
predict_baggingtest=[]
for k in num_feature:
    #----------train----------
    hold=[]
    for j in range(len(predict_train[k])):
        temp=pd.DataFrame(predict_train[k][j]).T
        hold.append((temp.T*pd.Series(temp.index.values)).sum(axis=1))       
    y_pred=pd.DataFrame(hold).T.mean(axis=1)
    y_true=y_train.values
    res_bagging.loc[k,'train']=mae(y_true,y_pred)+mse(y_true,y_pred)
    predict_baggingtrain.append(y_pred)
    #---------test-----------
    hold=[]
    for j in range(len(predict_test[k])):
        temp=pd.DataFrame(predict_test[k][j]).T
        hold.append((temp.T*pd.Series(temp.index.values)).sum(axis=1))       
    y_pred=pd.DataFrame(hold).T.mean(axis=1)
    y_true=y_test.values
    res_bagging.loc[k,'test']=mae(y_true,y_pred)+mse(y_true,y_pred)    
    predict_baggingtest.append(y_pred)
    #
    yval=yret_test.unstack()
    xval=pd.Series(y_pred.values,index=y_test.index).unstack()-rev_num
    wval=W_test.unstack()
    calc_pnl(xval,yval,wval,title='%s_test'%(k),standard=False)    
yval=yret_train.unstack()
y_pred=pd.DataFrame(predict_baggingtrain).T.mean(axis=1)
xval=pd.Series(y_pred.values,index=yret_train.index).unstack()-rev_num
wval=W_train.unstack()
calc_pnl(xval,yval,wval,title='all_train',standard=False)
yval=yret_test.unstack()
y_pred=pd.DataFrame(predict_baggingtest[:]).T.mean(axis=1)
xval=pd.Series(y_pred.values,index=yret_test.index).unstack()-rev_num
wval=W_test.unstack()
usecol=(yval*xval).apply(lambda x:calc_rmdd(x)).T[2].sort_values().index[-30:]
calc_pnl(xval.loc[:,usecol],yval.loc[:,usecol],wval.loc[:,usecol],title='all_test',standard=False)
#
temp=(yval*xval)
pd.DataFrame([temp.mean(),(temp.mean()/temp.std()*16),wval.mean()]).T.corr()
(temp.mean()/temp.std()*16).loc[wval.mean().sort_values().index].plot(kind='bar')
(temp.mean()).loc[wval.mean().sort_values().index].plot(kind='bar')










