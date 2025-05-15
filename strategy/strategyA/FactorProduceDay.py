from __future__ import division
import warnings
warnings.simplefilter(action = "ignore", category = FutureWarning)
from queue import Queue
import pandas as pd
import threading
import numpy as np
import time
from multiprocessing import Pool, Lock, cpu_count, Manager
from multiprocessing.managers import BaseManager
# import clickhouse_driver
import os
import sys;
sys.path.append(r"D:\蓝天LT_Research")
sys.path.append(r"D:\蓝天LT_Research\FactorResearch")
from apitool import *;warnings.filterwarnings("ignore")

from AlphasWYF_ import *
from AlphasZCL_ import *
from alphaZS_101_Class import *
from alphaZS_FH_Class import *
from alphaZS_GS127_Class import *
from alphaZS_PDF_Class import *
from alphaZS_TAall_Class import *
from alphaZS_TALib_Class import *


class MyManager(BaseManager):
    pass
MyManager.register('AlphaWYF_', AlphaWYF_)
MyManager.register('AlphasZCL_', AlphasZCL_)
MyManager.register('AlphasZS_YOY', AlphasZS_YOY)
MyManager.register('AlphasZS_FH', AlphasZS_FH)
MyManager.register('AlphasZS_GS127', AlphasZS_GS127)
MyManager.register('AlphasZS_PDF', AlphasZS_PDF)
MyManager.register('AlphasZS_TAall', AlphasZS_TAall)
MyManager.register('AlphasZS_tal', AlphasZS_tal)
#%%--多参数生成

# filepath = r'/home/heshuangji/Data/DATA_DAY_WEIGHT'
factorvaluepath =r'D:\蓝天LT_Research\FactorResearch\Temp\FactorValue\{0}'


# 是否是第一次生成历史因子值
FisrtHistoryCreratFactor = True



def ParaFormat(data):

    x = (data.split('@'))
    x[0] = data

    for i in range(1, len(x)):
        try:
            temp = eval(x[i])
            if temp > 1:
                temp = int(temp)
            x[i] = temp
        except:
            x[i] = None

    if FisrtHistoryCreratFactor:
        x[-1] = None
    else:
       pass

    return tuple(x)


def CreatFactor(*args):


    global factorvaluepath
    factorclass, factorfun, func, paralist, log = args
    # 因子计算
    for para in paralist:


        para = ParaFormat(para)
        fun = getattr(factorclass, factorfun)
        name, value = fun(*para)

        if log:
            name = 'log' + name
        else:
            name = name

        value.insert(0, 'BeginOfBar', value.index)
        value.insert(0, 'name', [name] * len(value))
        path = factorvaluepath.format(func)
        pd.DataFrame.to_csv(value, '{0}/{1}.csv'.format(path, name))

# def GetParaGroup(para, lenrange=[0.5,1,7,50], threshrange=[0.1, 0.2, 0.4, 0.6, 0.8, 1]):
def GetParaGroup(para, lenrange=[0.5, 1, 3, 10], threshrange=[0.1, 0.2, 0.4, 0.6, 0.8, 1]):

    paragroup = []

    try:

        colname = []
        colname.append('name')
        result = []

        if len(para) > 2:

            for i in range(1, len(para) - 1):

                temp = para[i]
                # 小数参数
                if temp > 0 and temp < 1:
                    df = pd.DataFrame(threshrange, columns=[str(len(colname))])
                    df['name'] = para[0]
                    colname.append(str(len(colname)))
                    result.append(df)
                else:
                    # 整数参数
                    df = pd.DataFrame([max(1, int(temp * x)) for x in lenrange], columns=[str(len(colname))])
                    df['name'] = para[0]
                    colname.append(str(len(colname)))
                    result.append(df)

            df = result[0]
            for i in range(1, len(result)):
                df = pd.merge(df, result[i], how='left', on='name')


            df = df[colname]
            df = df.drop_duplicates()


            df[str(len(df.T))] = para[-1]
            if para[-1]!= None:
                orign = pd.DataFrame(para).T
                orign.columns = df.columns
                df = pd.concat([df, orign])

                factor = df.iloc[:, 1:-1].div(df.tail(1).iloc[:, 1:-1].iloc[0]).max(axis=1)
                df[str(len(df.T) - 1)] = (factor * para[-1]).apply(lambda x: int(x) + 1)
                #df[str(len(df.T) - 1)] = df[str(len(df.T) - 1)].apply(lambda x: int(x) + 1)

                df = df.iloc[:-1, :]
            else:
                pass
            df = df.applymap(lambda x: str(x))
            df['name'] = df.apply(lambda x: "@".join(list(x)), axis=1)
            # df = df.set_index('name').astype(float)
            df = df.set_index('name')

            paragroup = list(df.index)

        else:
            result = (para[0]) + "@" + str(para[-1])
            paragroup = [result]
            #     paragroup = [result]
            # if not para[-1]:
            #     paragroup = [para[-1]]
            # else:
            #     result = (para[0]) + "@" + str(para[-1])
            #     paragroup = [result]

    except Exception as e:
        print(str(e))

    return paragroup




if __name__ == '__main__':
    
    # open_ = pd.read_csv(filepath+'/Open.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
    # high_ = pd.read_csv(filepath+'/High.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
    # low_ = pd.read_csv(filepath+'/Low.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
    # close_ = pd.read_csv(filepath+'/Close.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
    # vol_ = pd.read_csv(filepath+'/Vol.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
    # opt_ = pd.read_csv(filepath+'/OpenInterest.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
    # amount_ = pd.read_csv(filepath+'/Amount.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
    data1=get_mydata(mode='FQWEIGHT')
    data2=get_mydata(mode='ORIGIN')
    open_ = data1['open']
    high_ =data1['high']
    low_ = data1['low']
    close_ = data1['close']
    vol_ = data2['vol']
    opt_ = data2['opt']
    amount_ = data2['amt']
    vwap_ = amount_/vol_

    with MyManager() as manager:

        for func in ['AlphaWYF_', 'AlphasZCL_', 'AlphasZS_YOY', 'AlphasZS_FH', 
                     'AlphasZS_GS127', 'AlphasZS_PDF', 'AlphasZS_TAall', 'AlphasZS_tal']:
        # for func in ['AlphasZS_FH']:


            # 创建因子目录
            MkDir(factorvaluepath.format(func))

            # 因子对象实例化
            factorobj = eval("manager.%s(open_,high_,low_,close_,vol_,opt_,amount_,vwap_)"%(func))
            # 用于获取默认参数
            factorobjbase = eval("%s(open_,high_,low_,close_,vol_,opt_,amount_,vwap_)"%(func))

            # 生成需要的因子函数list
            alphalist = []
            temp = factorobj.__dir__()

            # 获取因子函数
            for factor in temp:
                if "alpha" in factor and factor != 'empty':
                    alphalist.append(factor)

            # print(alphalist)
            pool = Pool()
            for factor in alphalist:

                print(factor)
                # 获取默认参数
                para = getattr(factorobjbase, factor).__defaults__
                # 生成参数寻优列表
                paralist = GetParaGroup(para)
                pool.apply_async(CreatFactor, args=(factorobj, factor, func, paralist, False))


            pool.close()
            pool.join()


        print('111111111111111111111111111111111111111111')
