# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 14:36:52 2021

@author: zss114
"""


import warnings
import sys;sys.path.append(r"D:\蓝天LT_Research")
from apitool import *
warnings.filterwarnings("ignore")
from queue import Queue
import pandas as pd
import numpy as np
import time
from statsmodels.tsa.stattools import adfuller
# from mlfinlab.features.fracdiff import frac_diff_ffd
import os
from sklearn import metrics
from sklearn.metrics import log_loss, accuracy_score
from sklearn.tree import DecisionTreeClassifier,DecisionTreeRegressor
from sklearn.tree import plot_tree,export_text,export_graphviz
from sklearn.ensemble import BaggingClassifier,BaggingRegressor
import pickle
import gc
#%%简单线性加权
#  
for i_ in range(len(namelist)):
  
    tempnames=namelist[i_]
    dfx=[]
    jobs=[];alpha=0.5;keys=[]
temp1=pd.read_csv(r'D:\蓝天LT_Research\NewResult\Factor1_corr.csv',index_col=0)['1']
temp2=pd.read_csv(r'D:\蓝天LT_Research\NewResult\Factor1_mic.csv',index_col=0)
temp=pd.concat([temp1,temp2],axis=1)
temp.columns=['corr','mic']
set1=temp['corr'][temp['corr']>=0.02].index
set2=temp['mic'][temp['mic']>=0.02].index
names0=list(set(set1).union(set(set2)))
namelist=[]
for n in names0:
    for m in names:
        if n in m:
            namelist.append(m)
            break
namelist=[namelist]
#
dfx=pd.read_csv(r'D:\蓝天LT_Research\df_2nd.csv')
dfx.index=pd.MultiIndex.from_frame(dfx[['Unnamed: 0', 'Unnamed: 1']])
dfx=dfx.drop(['Unnamed: 0', 'Unnamed: 1'],axis=1)
dfx.loc[ret.stack().index,'ret']=ret.stack()
xcol=dfx.columns[:-1]
corr=pd.Series(index=xcol)
corr0=pd.Series(index=xcol)
for n in xcol:
    print(n)
    temp=dfx[n].unstack()
    temp=temp/temp.abs().max()
    # dfx[n]=temp.stack()
    # corr[n]=dfx[n].corr(dfx['ret'])
    corr0[n]=dfx[n].corr(dfx['alphaZS_PDF96@5@101(logMR)'],method='kendall')    
for thresh in np.arange(-0.5,0.0,0.1):
    flag=2*(corr0>thresh)-1
    res0=(flag*dfx[xcol]).sum (axis=1).unstack()
    (res0.apply(lambda x:standardize(x))*ret).cumsum().sum(axis=1)[:-10].plot(label=str(thresh),legend=True)


#%%Notused：get data==
rev_num=(11-1)/2
#
open_=pd.read_csv(r'D:\蓝天LT_Research\DATA_DAY_WEIGHT/Open.csv',index_col=0)
close_=pd.read_csv(r'D:\蓝天LT_Research\/DATA_DAY_WEIGHT/Close.csv',index_col=0)
close0_=pd.read_csv(r'D:\蓝天LT_Research\/DATA_DAY_ORIGIN/Close.csv',index_col=0)
ret=((open_.shift(-1)-open_)/close0_*100).shift(-1)

temp=ret.parallel_apply(lambda x:myqcut_ts(x,num=11,expanding=600))
dfy=pd.concat([temp[n].dropna() for n in temp.columns],axis=1,ignore_index=True).sort_index()
dfy.columns=temp.columns
#    
# amt=pd.read_csv(r'D:\蓝天LT_Research\DFW_Data\DATA_DAY_ORIGIN\amt.csv',index_col=0)
# amt.mean().to_csv(r'D:\蓝天LT_Research\Amount_1minavg.csv')
ratiopd.read_csv(r'D:\蓝天LT_Research\Amount_1minavg.csv',index_col=0)['0']
ratio=ratio/ratio['RB']*100
weight=ret7.applymap(lambda x:np.nan)
weight.loc[weight.index[0],:]=ratio
weight=weight.fillna(method='ffill')
#
# corr0=pd.read_csv(r"D:\蓝天LT_Research\Matrix_Corr(kendall).csv",index_col=0)
# ic=pd.read_csv(r"D:\蓝天LT_Research\MIC_xy.csv",index_col=0)
#
dfx=pd.read_csv(r'D:\蓝天LT_Research\df_2nd.csv')
dfx.index=pd.MultiIndex.from_frame(dfx[['Unnamed: 0', 'Unnamed: 1']])
dfx=dfx.drop(['Unnamed: 0', 'Unnamed: 1'],axis=1).loc[:,:]
dfx['weight']=weight.stack()
dfx['y']=dfy.stack(dropna=False)
dfx['yret']=ret.stack(dropna=False)
dfx=dfx.dropna(subset=['yret','y'])

#analysis for simple
dfx=pd.read_csv(r'D:\蓝天LT_Research\df1_1st.csv')
dfx.index=pd.MultiIndex.from_frame(dfx[['Unnamed: 0', 'Unnamed: 1']])
dfx=dfx.drop(['Unnamed: 0', 'Unnamed: 1'],axis=1).loc[:,:]
black=pd.read_csv(r'D:\蓝天LT_Research\black.csv',index_col=0)['0']
dropcol=[]
for n in  dfx.columns:
    for m  in black.values:
        if m in n:
            print(n)
            dropcol.append(n)
            break
dfx=dfx.drop(dropcol,axis=1)   

#---corr
res=pd.DataFrame(columns=[0.4,0.5,0.6,0.7])
for alpha in [0.4,0.5,0.6,0.7]:
    res[alpha]=pd.read_csv(r'D:\蓝天LT_Research\MIC_xymclass_alpha%s.csv'%(alpha))['mic']
res.corr(method='kendall')
#=============t_stat for OOB============
num_feature=[0.5,0.7,0.9];num_bagging=[]
out=dict( [(nf,[]) for nf in num_feature])
for nf in num_feature:
    print(nf)
    nfr=int(nf*(dfx.shape[0]))
    num=N_estimator(samples=dfx.shape[0],k=nfr)
    num_bagging.append(num)
    for i in range(num):
        tempX=dfx.sample(n=nfr,replace=False,weights=None,axis=0)
        #
        keys=tempX.columns[:-3]
        jobs=[]
        for k in keys:
            job={'func':func,'x':tempX[k],'y':tempX['y'],'alpha':0.5}
            jobs.append(job)          
        result=dict([(k,None) for k in keys])        
        executor=ProcessPoolExecutor(120)
        for i,res in enumerate(executor.map(expandCall,jobs)):  
            k=keys[i]
            result[k]=res
        executor.shutdown(True)
        out[nf].append(pd.Series(result))
tot=[]
for nf in num_feature:
    temp=pd.DataFrame(out[nf]).T.corr(method='kendall')
    print(nf)
    plt.figure();plt.title(str(nf))
    sns.heatmap(temp,cmap='rainbow') 
    temp.mean.plot(kind='bar')
    tot.append(temp)
temp2=pd.concat(tot,axis=1).corr(method='kendall')
sns.heatmap(temp2,cmap='rainbow')
temp2.mean().plot(kind='bar') 
#


#%%FI
dfx_used=dfx.dropna()
y=dfx_used['y']
X=dfx_used[feature_names[[selected_features]]]
#
clf=DecisionTreeRegressor(criterion='squared_error',max_features=int(1))
clf=BaggingRegressor(base_estimator=clf,max_samples=float(1.),           
                      max_features=float(1.0),n_estimators=200,
                      oob_score=True,bootstrap=True,
                      bootstrap_features=False,n_jobs=-1)
model=clf.fit(X=X,y=y,sample_weight=dfx_used['weigth'])
from sklearn.inspection import permutation_importance
r=permutation_importance(clf,X,y,n_repeats=10,random_state=0)
res0=pd.Series(r.importances_mean,index=selected_features).sort_values()
res=pd.Series(r.importances_mean,index=feature_names[[selected_features]]).sort_values()
# find_in_CID(1222,cluster_id_to_feature_ids)
with open('FI_result(1).pkl','wb') as f:
    pickle.dump(r,f)
r=[]    
for file in ['FI_result(1).pkl','FI_result(0).pkl','FI_result(-1).pkl']:
    with open(file,'rb') as f:
        temp=pickle.load(f)
        r.append(temp)
mean=pd.DataFrame([r[0].importances_mean,r[1].importances_mean,
              r[2].importances_mean]).T
std=pd.DataFrame([r[0].importances_std,r[1].importances_std,
              r[2].importances_std]).T
mean[[1,2]].plot();mean[0].plot(secondary_y=True)

mean.index=feature_names[[selected_features]]
mean['mic']=ic['mic'].loc[mean.index]
mean['kendall']=ic['kendall'].loc[mean.index]
#-----------
samples=X.shape[1]
res=[]
for k in range(1,100):
    res.append(N_estimator(samples,k))
temp=pd.Series(res)
pivot_k=temp[temp.diff().diff().abs()/temp<=0.01].index[0]
pivot_estimators=temp[pivot_k]
#
clf=DecisionTreeRegressor(criterion='squared_error',max_features=float(1.0))
clf=BaggingRegressor(base_estimator=clf,max_samples=float(1.),           
                      max_features=pivot_k,n_estimators=pivot_estimators*2,
                      oob_score=True,bootstrap=True,
                      bootstrap_features=False,n_jobs=-1)