# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 09:15:13 2023

@author: hesj
"""
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
if __name__ == '__main__':
    checktype=['RB','TA','NI','M','J','SC','CU','CF']
    #
    data1=get_mydata(mode='FQWEIGHT')
    data2=get_mydata(mode='ORIGIN')
    #
    ret=pd.DataFrame(columns=[1,2,5,15,30])#
    for l in ret.columns:
        ret[l]=((data1['open'].shift(-l-1)-data1['open'].shift(-1))/data2['open'].shift(-1)).stack(dropna=False)  

    
    #----随机值的基准评估:真实各品种return表现
    micbench=dict([(x,None) for x in ret.columns])
    for l in ret.columns:
        tempret=ret[l].unstack()
        tempout=pd.DataFrame(index=range(100),columns=tempret.columns)
        for i in tempout.index:          
            print(l,i)
            for n in tempret.columns:
                std=tempret[n].std()
                tempx=np.random.normal(0,std,tempret.shape[0])
                tempdf=pd.DataFrame([tempx,tempret[n]],index=['x','y']).T.dropna()
                if tempdf.shape[0]>200:
                    tempout.loc[i,n]=micfunc(tempdf['x'],tempdf['y'],alpha=0.5)  
        micbench[l]=tempout
    plt.figure()
    plt.subplots_adjust(wspace=0,hspace=0)  
    ax1=plt.subplot(2,1,1)
    plt.title('mean')  
    ax2=plt.subplot(2,1,2)
    plt.title('(max+min)/(max-min)**0.5')
    for l in ret.columns:
        resmic=micbench[l]
        resmic.mean().plot(ax=ax1,legend=True,label=str(l)+'_max%s_median%s'%(round(resmic.mean().max(),2),round(resmic.mean().median(),2)))
        temp=(resmic.max()+resmic.median())/(resmic.max()-resmic.median())**0.5
        temp.plot(ax=ax2,legend=True,label=str(l)+'_max%s_median%s'%(round(temp.max(),2),round(temp.median(),2)))
    #----随机值的基准评估:模拟数据长度的影响,并拟合输出mic值与数据长度关系
    l=1  
    micbench=pd.DataFrame(columns=[round(alpha,2) for alpha in np.arange(0.2,0.55,0.05)])
    tempdf=[]
    for t_ in checktype:
        tempret=ret[l].unstack()[t_]
        std=tempret.std()
        tempx=np.random.normal(0,std,tempret.shape[0])
        tempdf.append(pd.DataFrame([tempx,tempret],index=['x','y']).T.dropna() )
    tempdf=pd.concat(tempdf).reset_index(drop=True)    
    for alpha in micbench.columns:                      
        tempout=pd.DataFrame(index=range(100),columns=range(1,int(tempdf.shape[0]/100)))
        for i in tempout.index:    
            print(alpha,i)        
            for n in tempout.columns:
                try:
                    nn=n*100
                    start=random.randint(0,tempdf.shape[0]-nn)
                    tempout.loc[i,n]=micfunc(tempdf['x'][start:start+nn],tempdf['y'][start:start+nn],alpha=alpha)  
                except:
                    continue
        micbench[alpha]=tempout.mean()
    fig, ax = plt.subplots()
    micbench.plot(ax=ax,legend=False)

    #
    tempdf=micbench#[[0.2 , 0.35, 0.4 , 0.45, 0.5 ]]#
    df = tempdf.stack().reset_index()
    df.columns=['x1', 'x2','y']
    from scipy.optimize import curve_fit
    def nonlinear_function(x,w1,a1, b1, c1, d1,ct1,w2 ,a2, b2,c2, d2,ct2,ct0):
        rowf=w1*1/(1+(x[0]-a1)**2/b1**2)+ (1-w1)*c1*np.exp(d1/x[0])+ct1#lorenz(x,a,b)+exp(x,a,b)
        colf=w2*(x[1]+(x[1]-a2)**2/b2**2)+ (1-w2)*c2*np.exp(d2*x[1])+ct2
        return rowf*colf+ct0
    popt, pcov = curve_fit(nonlinear_function, (df['x1'], df['x2']), df['y'],maxfev = 222800)  
    for i in df.index:
        x=df.iloc[i][['x1','x2']]
        df.loc[i,'pred']=nonlinear_function(x,*popt)
    df[['y','pred']].plot();plt.title(str(df[['y','pred']].corr()))
    for alpha in tempdf.columns:
        temp=df[df['x2']==alpha][['y','pred']]
        temp.plot(label=alpha)
        plt.title(str(alpha)+str(temp.corr()))
    for alpha in tempdf.columns:
        x=pd.Series(range(1,100))
        y=x.apply(lambda x0:fitmic(x0,alpha));y.index=x.index
        y.plot(legend=True,label=str(alpha))        
    # fitmic=lambda x:(lorenz(x,-7.9,2.6)+exp(x,0.02,1.57))/2
    # yvals=fitmic(x)
    # plot1=plt.plot(x, y, '*',label='original values')
    # plot2=plt.plot(x, yvals, 'r',label='curve_fit values')
    # plt.xlabel('x axis')
    # plt.ylabel('y axis')
    # plt.legend(loc=4)#指定legend的位置,读者可以自己help它的用法
    # plt.title('curve_fit')
    # plt.show()
    #          
    #----x自相关性与预测衰减