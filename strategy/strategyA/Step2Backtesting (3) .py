#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 17:40:43 2021

@author: heshuangji

plan of CPCV
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
rev_num=(11-1)/2
#
open_=pd.read_csv(r'/home/heshuangji/Data/DATA_DAY_WEIGHT/Open.csv',index_col=0)
close_=pd.read_csv(r'/home/heshuangji/Data//DATA_DAY_WEIGHT/Close.csv',index_col=0)
close0_=pd.read_csv(r'/home/heshuangji/Data//DATA_DAY_ORIGIN/Close.csv',index_col=0)
ret=((open_.shift(-1)-open_)/close0_*100).shift(-1)
ret['BU']=ret['BU'][ret['BU'].index>='2015-01-01']
ret.loc[:,['SF','SM']]=np.nan
temp=ret.parallel_apply(lambda x:myqcut_ts(x,num=11,expanding=600))
dfy=pd.concat([temp[n].dropna() for n in temp.columns],axis=1,ignore_index=True).sort_index()
dfy.columns=temp.columns
#  
ratio=pd.read_csv(r'/home/heshuangji/Data/Amount_1minavg.csv',index_col=0)
ratio.ratio=ratio.ratio/ratio.ratio['RB']*100
weight=ret.applymap(lambda x:np.nan)
weight.loc[weight.index[0],:]=ratio.ratio
weight=weight.fillna(method='ffill')
#
# corr0=pd.read_csv(r"/home/heshuangji/Data/Matrix_Corr(kendall).csv",index_col=0)
# ic=pd.read_csv(r"/home/heshuangji/Data/MIC_xy.csv",index_col=0)
#
dfx=pd.read_csv(r'/home/heshuangji/Data/df_2nd.csv')
dfx.index=pd.MultiIndex.from_frame(dfx[['Unnamed: 0', 'Unnamed: 1']])
dfx=dfx.drop(['Unnamed: 0', 'Unnamed: 1'],axis=1).loc[:,:]
dfx['weight']=weight.stack()
dfx['y']=dfy.stack(dropna=False)
dfx['yret']=ret.stack(dropna=False)
dfx=dfx.dropna(subset=['yret','y'])

#%%Bench3 CPCV
gapday=100
for i in range(0,dfx.index.levels[0].shape[0]-gapday,gapday):
    date=dfx.index.levels[0][i]#start date of OOS
    date2=dfx.index.levels[0][i+gapday-1]#start date of OOS
    print(date)
    #
    train1=dfx.loc[idx[dfx.index.levels[0][:i],:],:]
    train2=dfx.loc[idx[dfx.index.levels[0][i+gapday:],:],:]
    train=pd.concat([train1,train2])
    
    test=dfx.loc[idx[dfx.index.levels[0][i:i+gapday],:],:]
    X_train=train.loc[:,train.columns[:-3]];y_train=train['y'];W_train=train['weight']
    # X_test=test.loc[:,test.columns[:-3]];y_test=test['y'];W_test=test['weight']
    #
    num_feature=[0.5]#[0.3,0.5,0.7]#
    num_bagging=[]
    fs_rd=dict( [(k,[]) for k in num_feature])
    fs_ew=dict( [(k,[]) for k in num_feature])
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
        'boosting_type': 'gbdt',
        'objective': 'multiclass',
        'num_class':11,
        'metric': {'multi_logloss'},
        'max_depth': 4,
        'learning_rate': 0.1,
        'bagging_freq': 0,
        'feature_fraction': 1.0,
        'bagging_fraction': 1.0,        
        'extra_trees ':True,
        'lambda_l1':3,
        'lambda_l2':2,
        'min_data_in_leaf':11,
        'path_smooth':1,    
        # 'drop_rate':0.5,
        # 'skip_drop':0.8,
        'num_threads':0,
        'verbose':-1
    }
    for k,v in fs_rd.items():
        print(k)
        result={'model':[],'error':[]}
        for col in v:
            
            lgb_train = lgb.Dataset(X_train[col], y_train,
                                    weight=W_train, free_raw_data=False)
            # lgb_test = lgb.Dataset(X_test[col], y_test, reference=lgb_train,
            #                        weight=W_test, free_raw_data=False)
            evals_result = {}  # to record eval results for plotting
            # train
            gbm = lgb.train(params,
                            lgb_train,
                            num_boost_round=100,
                            # valid_sets=[lgb_train, lgb_test],
                            # evals_result=evals_result,
                            # verbose_eval=True
                            )
            result['model'].append(gbm)
            result['error'].append(evals_result)
        pkl_save(r'/home/heshuangji/FactorResearch/ModelSave/CPCV/lgb%s_%s_%s.pkl'%(k,date,date2), result)
#%%analysis2
#-----------num_iteration analysis---------
numtree=[100]
predict_train=dict([(kt,[]) for kt in numtree])
predict_test=dict([(kt,[]) for kt in numtree])
for kt in numtree:
    gapday=100
    for i in range(0,dfx.index.levels[0].shape[0]-gapday,gapday):
        date=dfx.index.levels[0][i]#start date of OOS
        date2=dfx.index.levels[0][i+gapday-1]#start date of OOS
        print(kt,date,date2)
        #
        train1=dfx.loc[idx[dfx.index.levels[0][:i],:],:]
        train2=dfx.loc[idx[dfx.index.levels[0][i+gapday:],:],:]
        train=pd.concat([train1,train2])      
        test=dfx.loc[idx[dfx.index.levels[0][i:i+gapday],:],:]
        
        #
        X_train=train.loc[:,train.columns[:-3]];y_train=train['y'];W_train=train['weight']
        X_test=test.loc[:,test.columns[:-3]];y_test=test['y'];W_test=test['weight']
        
        data=pkl_load(r'/home/heshuangji/FactorResearch/ModelSave/CPCV/lgb%s_%s_%s.pkl'%(0.5,date,date2))
        temptrain=[];temptest=[]
        for _,gbm in enumerate(data['model']):
            col=gbm.feature_name()  
            #
            temp=gbm.predict(X_train[col],num_iteration=kt)  
            temp=pd.DataFrame(temp)
            multiclass=pd.Series(range(int(rev_num)*2+1))-rev_num
            y_pred=(temp*multiclass).mean(axis=1)+rev_num#multiclass
            y_true=y_train.values
            temptrain.append(y_pred)
            #    
            temp=gbm.predict(X_test[col],num_iteration=kt)
            temp=pd.DataFrame(temp)
            multiclass=pd.Series(range(int(rev_num)*2+1))-rev_num
            y_pred=(temp*multiclass).mean(axis=1)+rev_num#multiclass
            y_true=y_test.values
            temptest.append(y_pred)      
        train=pd.DataFrame(temptrain).T.mean(axis=1)        
        train.index=X_train.index
        test=pd.DataFrame(temptest).T.mean(axis=1)        
        test.index=X_test.index        
        predict_train[kt].append(train)
        predict_test[kt].append(test)

yret=dfx['yret'];W=dfx['weight']
for kt in numtree:
    temp=pd.concat(predict_train[kt],axis=1)
    res_train=temp.mean(axis=1).unstack()-rev_num
    res_test=pd.concat(predict_test[kt]).unstack()-rev_num
    #
    yval=yret.unstack();xval=res_train; wval=W.unstack()
    calc_pnl(xval,yval,wval,title='numtree%s_train'%(kt),standard=False)  
    
    yval=yret.unstack();xval=res_test; wval=W.unstack() 
    # usecol=(yval*xval).apply(lambda x:calc_rmdd(x)).T[2].sort_values().index[:]#年化Ret/MDD
    usecol=(yval*xval).cumsum().min().sort_values().index[:]
    calc_pnl(xval.loc[:,usecol],yval.loc[:,usecol], wval.loc[:,usecol],
             title='numtree%s_test_col(%s)'%(kt,round(len(usecol)/yval.shape[1],2)),standard=False)    
#-----------overlap analysis---------
overlap=[0,1,2,3,5,8,13,21]
predict_test2=dict([(k,[]) for k in overlap])
for k in overlap:
    for i in range(benchday+k*10,dfx.index.levels[0].size-10,10):
        date=dfx.index.levels[0][i]#start date of OOS
        dateoverlap=dfx.index.levels[0][i-10*k]
        print(date)
        #
        test=dfx.loc[idx[dfx.index.levels[0][i:i+10],:],:]
        X_test=test.loc[:,test.columns[:-3]];y_test=test['y'];W_test=test['weight']
        #
        data=pkl_load(r'/home/heshuangji/FactorResearch/ModelSave/RollingDay2/lgb%s_%s.pkl'%(0.5,dateoverlap))
        temptrain=[];temptest=[]
        for _,gbm in enumerate(data['model']):
            col=gbm.feature_name()  
            #
            y_pred=gbm.predict(X_test[col],num_iteration=120)
            y_true=y_test.values
            temptest.append(y_pred)      
        test=pd.DataFrame(temptest).T.mean(axis=1)        
        test.index=X_test.index        
        predict_test2[k].append(test)
test=dfx.loc[idx[dfx.index.levels[0][benchday:],:],:]
y_test=test['y'];W_test=test['weight']
out=dict([(k,None) for k in overlap])
for k in overlap:
    res_test=pd.concat(predict_test2[k]).unstack()
    # 
    xval=res_test;yval=y_test.unstack().loc[xval.index]; wval=W_test.unstack().loc[xval.index]
    #年化Ret/MDD
    usecol=(yval*xval).apply(lambda x:calc_rmdd(x)).T[2].sort_values().index[:]
    calc_pnl(xval.loc[:,usecol],yval.loc[:,usecol],wval.loc[:,usecol],title='overlap%s_test'%(k),standard=True) 
    out[k]=(wval*xval*yval).loc[:,usecol].sum(axis=1)
#-------final pnl--------
sharp=lambda x:round(x.mean()/x.std()*np.sqrt(250),2)
res=pd.DataFrame(out)
res.cumsum().plot()
pd.DataFrame([sharp(res),res.mean()],index=['sharp','ret']).T.plot(kind='bar')

res_test=[]
for k in list(out.keys()):
    res_test.append(pd.concat(predict_test2[k]))
y_pred=pd.DataFrame(res_test).T
var=y_pred.var(axis=1)
error=y_pred.apply(lambda x:(x-y_test.loc[y_pred.index].values)**2).mean(axis=1)
error.plot(label='error',legend=True);var.plot(label='var',legend=True,secondary_y=True)
filt=(1*(error.rolling(15).mean().shift()<=error.quantile(0.75))).unstack()
#
xval=y_pred.mean(axis=1).unstack()*filt;yval=y_test.unstack().loc[xval.index]; wval=W_test.unstack().loc[xval.index]
usecol=(yval*xval).apply(lambda x:calc_rmdd(x)).T[2].sort_values().index[-25:]#年化Ret/MDD
calc_pnl(xval.loc[:,usecol],yval.loc[:,usecol],wval.loc[:,usecol],
         title='sumall_test(sharp=%s)'%(sharp((wval*xval*yval).loc[:,usecol].sum(axis=1))  ),standard=False) 






