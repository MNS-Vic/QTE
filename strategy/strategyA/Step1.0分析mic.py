

import sys;sys.path.append(r"D:\蓝天LT_Research")
from apitool import *
from ml_functions import *
import warnings
warnings.filterwarnings("ignore")
from queue import Queue
import pandas as pd
import numpy as np
import time
from statsmodels.tsa.stattools import adfuller
from mlfinlab.features.fracdiff import frac_diff_ffd
from mlfinlab.util.multiprocess import mp_pandas_obj
import os
import pickle
from sklearn import metrics
from sklearn.metrics import log_loss, accuracy_score
from sklearn.tree import DecisionTreeClassifier,DecisionTreeRegressor
from sklearn.tree import plot_tree,export_text,export_graphviz
from sklearn.ensemble import BaggingClassifier,BaggingRegressor
import datatable as dt

#====
data1=get_mydata(mode='FQWEIGHT')
data2=get_mydata(mode='ORIGIN')
localpath=r'D:\蓝天LT_Research\FactorResearch\Temp'
#
temp=((data1['open'].shift(-2)-data1['open'].shift(-1))/data2['open'].shift(-1))
ret=temp[temp.index<='2023-05-31'].stack(dropna=False)  
#
newret,_=get_mqts(ret.unstack(),name='yqts',rolling=False)     

#====
# localpath=r'D:\蓝天LT_Research\FactorResearch\MrZhang'
# ret=pd.DataFrame()
# ret[1]=pd.read_csv(r'D:\蓝天LT_Research\FactorResearch\MrZhang\y.csv',index_col=0).stack(dropna=False)  
# newret=pd.DataFrame(columns=ret.columns)
# for l in ret.columns:
#     print(l)
#     res1,_=get_mqts(ret[l].unstack(),name='yqts',rolling=False)     
#     newret[l]=res1
# newret.to_csv(r'D:\蓝天LT_Research\FactorResearch\MrZhang\newret_qtsy.csv')
# newret=pd.read_csv(r'D:\蓝天LT_Research\FactorResearch\MrZhang\newret_qtsy.csv')
# newret.index=pd.MultiIndex.from_frame(newret[newret.columns[:2]])
# newret=newret.drop(newret.columns[:2],axis=1) 
#=====
print('data preparing...')
#=====

def find(name,clusterdict,outmic):    
    for k,v in clusterdict.items():
        if name in v:
            return outmic[v].sort_values()

if __name__ == '__main__':
   
    corr=pd.read_csv(r'%s\newdf0_corr.csv'%(localpath),index_col=0)  
    factortest=pd.read_csv(r'%s\Factortest1_1.csv'%(localpath),index_col=0)
    usedlist=get_usedlist(corr,factortest)

    #修正0：少数据权重
    temp=data1['close'].notna().sum()
    weight0=(temp/1000).apply(lambda x:min(1,x)).round(1)
    #修正1：指定品种权重
    # weight1=data2['amt'].mean()/data2['amt'].mean().max()
    weight1=pd.Series(1,data2['amt'].columns)
    tempw1={'s1_1':1, 's1_2':1, 's1_3':1, 's2_1':1, 's2_2':1, 's2_3':1, 's2_4':1, 's2_5':1,
            's2_6':1, 's3_1':1, 's3_2':0.8, 's3_3':1, 's4_1':1, 's4_2':1, 's4_3':0.5, 's4_4':0.2, 's5_1':1}
    for n in weight1.index:
        for k,v in get_sector(mode='sub').items():
            if n in v:break
        weight1[n]=tempw1[k]
    #修正2：减法
    weight2=data1['close'].notna().sum().apply(lambda x:fitmic(x/100))#    
 
#%%评估mic

    # newdf1_mic.index=[x.split('-MR')[0] for x in newdf1_mic.index]
    # usedlist=list(map(lambda x:x[:-4],os.listdir(r'D:\蓝天LT_Research\FactorResearch\Temp\newdf1_mic(handalpha0.5)')))
    
    newdf_mic=pd.DataFrame(index=usedlist,columns=['0.5','kendall'])  
    dictmic=dict([(i,newdf_mic.copy(deep=True)) for i in [1,2,5,15]])  
    for i in newdf_mic.columns:
        filepath=r'D:\蓝天LT_Research\FactorResearch\Temp\newdf1_mic(alpha%s)'%(i)    
        for n in newdf_mic.index:                
            temp=pd.read_csv(filepath+'/%s.csv'%(n),index_col=0)    
            for k in dictmic.keys():
                dictmic[k].loc[n,i]=temp.mean(axis=1)[k]
    dictmic[1].loc[dictmic[1]['kendall'].abs().sort_values().index,:].abs().plot()
    dictmic[1].loc[dictmic[1]['0.5'].abs().sort_values().index,:].abs().plot()
    #
    dictmic_=dictmic[1].loc[filter(lambda x:'expd' not in x,dictmic[1].index),:]
    dictmic_.index=[x.replace('(roll)','') for x in dictmic_.index]
    #
    # temp1=dictmic[1].loc[filter(lambda x:'(roll)' in x ,dictmic[1].index),:]
    # temp1.index=[x.split('(roll)')[0] for x in temp1.index]
    # temp1.columns=['roll_0.5','roll_kendall']
    # temp2=dictmic[1].loc[filter(lambda x:'(expd)' in x ,dictmic[1].index),:]
    # temp2.index=[x.split('(expd)')[0] for x in temp2.index]
    # temp2.columns=['expd_0.5','expd_kendall']    
    # temp=pd.concat([temp1,temp2],axis=1).dropna()
    #       
    # res=pd.DataFrame(index=['mom','band','hurst_pfe','adx','tsv','ttm','vpin','rsi','rsv','skewness' \
    #           ,'kurtosis','obvm','longterm_dma','longterm_newhl'],columns=['micmean','micmax','kendallmax','kendallmean'])
    # for n in ['mom','band','hurst_pfe','adx','tsv','ttm','vpin','rsi','rsv','skewness' \
    #           ,'kurtosis','obvm','longterm_dma','longterm_newhl']:
    #     temp=dictmic[1].loc[filter(lambda x:n in x ,dictmic[1].index),:].abs()
    #     res.loc[n,'micmean'] =temp.mean()['0.5']
    #     res.loc[n,'micmax'] =temp.max()['0.5']
    #     res.loc[n,'kendallmean'] =temp.mean()['kendall']
    #     res.loc[n,'kendallmax'] =temp.max()['kendall']
       
    # dfkd=pd.DataFrame(columns=[1, 2, 5, 15])           
    # for k in [1, 2, 5, 15]:
    #     dfkd[k]=dictmic[k]['0.5'].abs()
    # dfkd.sort_values(1).plot(alpha=0.75)
    # dfkd.loc[dfkd.mean(axis=1).sort_values().index,:].plot(kind='bar')    
        
    #----简单平均方法 
    factors=[]
    for x in usedlist:
        temp=x.split('@')[0]
        try:
            factors.append(temp.split('_')[0]+'_'+temp.split('_')[1])
        except:
            factors.append(temp)
    factors=list(set(factors)) 
    #
    outcorr=pd.DataFrame(index=factors,columns=factors)
    outmic=pd.DataFrame(index=factors,columns=['0.5','kendall'])
    for factor in factors:
        used=list(filter(lambda x:factor in x,usedlist))
        outmic.loc[factor,['0.5','kendall']]=dictmic_.loc[used,['0.5','kendall']].abs().mean()
        for factor2 in factors:
            used2=list(filter(lambda x:factor2 in x,corr.index))
            outcorr.loc[factor2,factor]=corr.loc[used2,used].mean().mean()
    for i in range(outcorr.shape[0]):
        outcorr.iloc[i,i]=1.0    
    #----MLDP方法
    # wIntra=pd.DataFrame(0,index=cov1.index,columns=clstrs.keys())
    # for i in clstrs:
    # wIntra.loc[clstrs[i],i]=minVarPort(cov1.loc[clstrs[i],
    # clstrs[i]]).flatten()
    # cov2=wIntra.T.dot(np.dot(cov1,wIntra)) # reduced covariance matrix  
    # cols=cov0.columns
    # cov1=deNoiseCov(cov0,q,bWidth=.01) # de-noise cov
    # cov1=pd.DataFrame(cov1,index=cols,columns=cols)
    # corr1=cov2corr(cov1)
    # corr1,clstrs,silh=clusterKMeansBase(corr1,
    # maxNumClusters=corr0.shape[0]/2,n_init=10)     
    # wInter=pd.Series(minVarPort(cov2).flatten(),index=cov2.index)
    # wAll0=wIntra.mul(wInter,axis=1).sum(axis=1).sort_index()
      
    #----生成单品种mic:最终指标=mic.mean
    # outmicdf=pd.DataFrame(columns=[1, 2, 5, 15])    
    # outmicdf2=pd.DataFrame(columns=[1, 2, 5, 15])  
    # for i in outmicdf.columns:
    #     #品种|历史|参数：均值后单维度评估
    #     factors=[]
    #     for x in usedlist:
    #         temp=x.split('@')[0]
    #         try:
    #             factors.append(temp.split('_')[0]+'_'+temp.split('_')[1])
    #         except:
    #             factors.append(temp)
    #     factors=list(set(factors))
    #     #
    #     filepath=r'D:\蓝天LT_Research\FactorResearch\Temp\Mic_Value\yd%s'%(i)
    #     # files=os.listdir(filepath)
    #     outmic=pd.Series(index=factors)
    #     outmic2=pd.Series(index=factors)
    #     for factor in factors:
    #         print(i,factor)
    #         usedfile=list(filter(lambda x:factor in x,usedlist))
    #         res=[];res2=[]
    #         for f in usedfile:                
    #             temp=pd.read_csv(filepath+'/%s.csv'%(f),index_col=0)    
    #             res.append((temp*weight0*weight1).sum(axis=1)/((weight0*weight1*temp.notna()).sum(axis=1)))#修正1
    #             temp2=(temp-weight2).applymap(lambda x:max(0,x))#修正2
    #             res2.append((temp2*weight0*weight1).sum(axis=1)/((weight0*weight1*temp2.notna()).sum(axis=1)))#修正1              
    #         resmic=pd.DataFrame(res)
    #         resmic2=pd.DataFrame(res2)
    #         outmic[factor]=resmic.mean().mean()
    #         outmic2[factor]=resmic2.mean().mean()
    #     outmicdf[i]=outmic
    #     outmicdf2[i]=outmic2
    # outmicdf.plot(kind='box')
    # ((outmicdf)/np.sqrt(outmicdf.columns)).plot(kind='box')
    # ((outmicdf2)/np.sqrt(outmicdf2.columns)).plot(kind='box')

    #----单因子分层评估                 
    clusterdicts=hpr(outcorr.fillna(0),distlist=[1.0,1.5,2.0])#----聚类后输出HRP    
    clusterdict=clusterdicts[1]
    
    find( 'alphaHand_mom' ,clusterdict,outmic['0.5']).sort_values()

    for k,v in clusterdict.items():
        temp=outmic['0.5'][v][outmic['0.5'][v]>0.015]
        if len(temp)==0:continue
        temp2=outcorr.loc[v,v].abs()
        print('corr=',round(temp2.replace(1,np.nan).mean().mean(),2))
               
        try:
            temp=temp#[temp2.index]
            res=temp[temp>=temp.sort_values().quantile(0.95)]  
            print(round(temp.mean(),2),round(res.mean(),2),res.index.values)
        except:
            continue
        
    random_choice = random.choices(outmic.index, weights=outmic.values, k=1)