

# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 09:18:20 2021

@author: zsqh
"""
from copy import deepcopy
import sys
import os
sys.path.append(r"/home/heshuangji")
from apitool import *
import pywt
# -----------
import warnings

warnings.filterwarnings("ignore")
import datetime
#
import os
import numpy as np
import pandas as pd
import re
from multiprocessing import Pool

from SecondCalculate_functions import  *
#
from scipy.stats import mstats, norm
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
#
import matplotlib.pyplot as plt
from mlfinlab.features.fracdiff import frac_diff_ffd



factorvaluepath = r'/home/heshuangji/Data/FactorValue/{0}'
factorvalueresultpath = r'/home/heshuangji/Data/FactorValue2/{0}'
filepath = r'/home/heshuangji/Data/DATA_DAY_WEIGHT'

open_ = pd.read_csv(filepath + '/Open.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
high_ = pd.read_csv(filepath + '/High.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
low_ = pd.read_csv(filepath + '/Low.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
close_ = pd.read_csv(filepath + '/Close.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
vol_ = pd.read_csv(filepath + '/Vol.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
opt_ = pd.read_csv(filepath + '/OpenInterest.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
amount_ = pd.read_csv(filepath + '/Amount.csv', header=0, parse_dates=True, index_col=0).dropna(how='all').fillna(method='ffill').fillna(method='bfill')
vwap_ = amount_ / vol_

data = {}
data['open'] = open_
data['high'] = high_
data['low'] = low_
data['close'] = close_
data['opt'] = opt_
data['vol'] = vol_
data['amount'] = amount_
data['vwap'] = vwap_

# %%-------通用处理-------
ExceptionSYMBOL = ['(',')','{','}',':', '\'', ',', ' ']
pricetype = 'close'
functiondict = {
    "neutralize_": [['vol', 10, {'close_': data[pricetype]}], ['mom', 10, {'close_': data[pricetype]}]],
    "standardize_": [[10, 'expanding'], [10, 'rolling']],
    "quantilize1_": [[11, 200]],
    "quantilize2_": [[11, 200]],
    "autofracdiff_": [[-3.5, 1, 0.001, True], [-3.5, 1, 0.001, False]],
    "wavefilter_":[ [1,{'length': 20}],  [21,{'length': 20,'matype': 0}], [22,{'length': 20,'matype': 6}],
                   [23,{'length': 20,'matype': 7}],[24,{'length': 20,'matype': 8}],
                   [3], [4,{'length':60}], [5] ],
    "rule1_": [[data[pricetype]]],
    "rule2_1_": [[data[pricetype], 'rolling', {'mul': 1.5, 'length': 15}],
                 [data[pricetype], 'expanding', {'mul': 1.5, 'length':15}]],
    "rule2_2_": [[data[pricetype], 2, 'rolling', {'mul': 1.5}], [data[pricetype], 2, 'expanding', {'mul': 1.5}]],
    "rule3_1_": [[data[pricetype], 5, ], [data[pricetype], None]],
    "rule3_2_": [[data[pricetype], 5, ], [data[pricetype], None]],
    "rule4_1_": [[data[pricetype], 1, ], [data[pricetype], 5]],
    "rule4_2_": [[data[pricetype], 1, ], [data[pricetype], 5]],
    "xFxn_": [[data[pricetype], 'raw', ], [data[pricetype], 'ma', ], [data[pricetype], 'h1', ]],
    "macompare_": [[5, 15]],
    "mmacompare_": [[3, 10]],
    "polyfit_": [[15, 'ma'], [15, 'np']],
    "hptp1_1_": [[15]],
    "hptp1_2_": [[15]],
    "hptp1_3_1_": [[15, 'atr']],
    "hptp1_3_2_": [[15, 'pfe']],
    "hptp1_3_3_": [[15, 'hl']],
    "hptp1_3_4_": [[15, 'std']],
    "linep_": [[]],
    "filter_": [[1, {'length': 20, 'overlap': 15}], [2, {'length1':80, 'length2':150}], 
                [3, {'length1':14,'high_': data['high'],'low_': data['low'], 'close_': data[pricetype] }],
                [4, {'close_': data[pricetype],'f':0.2,'lenf':60}]],
    "nonst_mdd": [[]],
    "st_mdd": [[]],


}
factortype = {

    "all": ["wavefilter_",'neutralize_', 'standardize_', 'quantilize1_','quantilize2_', 'xFxn_', 'macompare_', 'mmacompare_', 'polyfit_', 'linep_', 'filter_', 'keypointprice_'],
    "st": ['st_mdd','hptp1_1_', 'hptp1_2_', 'hptp1_3_1_', 'hptp1_3_2_', 'hptp1_3_3_', 'hptp1_3_4_'],
    "nonst": ['nonst_mdd','autofracdiff_', 'rule1_', 'rule2_1_', 'rule2_2_', 'rule3_1_', 'rule3_2_', 'rule4_1_', 'rule4_2_']

}

factorvalue = pd.read_csv('/home/heshuangji/Data/Factortest_1.csv', header=0, parse_dates=True, index_col=0,engine='python').dropna()
factorvaluelist = list(factorvalue['name'])
factorvaluelist = [i.split('/')[-1][:-4] for i in factorvaluelist]
factorvalue['name'] = factorvaluelist
factorvalue = pd.DataFrame([factorvalue['name'], factorvalue['adf']]).T
pattern = re.compile(r'\D+')




def MkDir(path):

    # 去除首位空格
    path = path.strip()
    # 去除尾部 \ 符号
    path = path.rstrip("/")
    isExists = os.path.exists(path)
    # 判断结果
    if not isExists:
        os.makedirs(path)
        print(path + ' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        print(path + ' 目录已存在')
        return False

def fileformat(name, tempname, df):

    newname = name + '_' + tempname
    df.insert(0, 'BeginOfBar', df.index)
    df.insert(0, 'name', [newname] * len(df))
    return newname, df

def checkfactor(name,funname):

    try:
        index = list(factorvalue['name']).index(name)
        adf = factorvalue.iloc[index]['adf']
        if not ((funname in factortype['all']) or (funname in factortype['st'] and adf == 1) or (
                funname in factortype['nonst'] and adf == 0)):
            return 0
        else:
            return 1
    except:
        return 0

def finalfun(para):

    try:

        fun = eval(para[0])
        path = para[1]
        factor = para[2][:-4]

        # 生成文件名
        if len(para) > 4:

            index = 0
            for i in range(3, len(para)):
                if not isinstance(para[i], pd.DataFrame):
                    index = i
                    break
            if isinstance(para[-1], dict):
                filename = factor + '_' + para[0] + '_' + str(para[index:-1])
            else:
                filename = factor + '_' + para[0] + '_' + str(para[index:])
        else:
            filename = factor + '_' + para[0]
        # 替换异常字符
        for i in ExceptionSYMBOL:
            if i == ',':
                filename = filename.replace(i, '_')
            else:
                filename = filename.replace(i, '')
        filepath = factorvalueresultpath.format(path)

        if isinstance(para[-1], dict):
            result = fun(*para[3:-1], **para[-1])
        else:
            result = fun(*para[3:])

        pd.DataFrame.to_csv(result, '{0}/{1}.csv'.format(filepath, filename))

    except Exception as e:
        with open(r'wrong.txt', 'a') as f:
            f.write(para[0] + str(e) + '\n')

if __name__ == '__main__':


    # 因子字典
    factor = {}
    for factorcls in ['AlphaWYF_', 'AlphasZCL_', 'AlphasZS_YOY', 'AlphasZS_FH', 'AlphasZS_GS127', 'AlphasZS_PDF','AlphasZS_TAall', 'AlphasZS_tal']:
    #for factorcls in ['AlphaWYF_']:
        filelist = os.listdir(factorvaluepath.format(factorcls))
        subfactor = {}
        for file in filelist:
            df = pd.read_csv(factorvaluepath.format(factorcls) + '/{0}'.format(file), header=0, parse_dates=True,index_col=0).dropna(how='all').fillna(method='ffill')
            df = df.iloc[:, 2:]
            subfactor[file] = df
        factor[factorcls] = subfactor

    # 二次算符
    sencondfunlist = list(functiondict.keys())

    # sencondfunlist=['quantilize1_']   
    # sencondfunlist=['quantilize2_']   
    # sencondfunlist=["hptp1_3_1_"]   
    # sencondfunlist=["hptp1_3_2_"]   
    # sencondfunlist=["hptp1_3_3_"]   
    # sencondfunlist=["hptp1_3_4_"]   
    # sencondfunlist=['neutralize_','standardize_','autofracdiff_','rule1_', 
    #                 'rule2_1_', 'rule2_2_','rule3_1_', 'rule3_2_','rule4_1_', 
    #                 'rule4_2_''hptp1_1_', 'hptp1_2_','polyfit_','xFxn_', 'macompare_',
    #                 'mmacompare_','linep_',"filter_", 'nonst_mdd', 'st_mdd']
    sencondfunlist=["wavefilter_"]
    for fun in sencondfunlist:

        print(fun)
        # 原始因子路径
        # for factorcls in ['AlphaWYF_']:
        for factorcls in ['AlphaWYF_', 'AlphasZCL_', 'AlphasZS_YOY', 'AlphasZS_FH', 'AlphasZS_GS127', 'AlphasZS_PDF','AlphasZS_TAall', 'AlphasZS_tal']:

                MkDir(factorvalueresultpath.format(factorcls))
                pool = Pool()
                # 原始因子值
                factorlist = list(factor[factorcls].keys())
                print(factorlist)
                for name in factorlist:

                    df = factor[factorcls][name]
                    # 因子平稳性检验
                    result = checkfactor(name[:-4], fun)
                    if not result:
                        continue

                    # 二次算符参数列表，深copy
                    functiondict1 = deepcopy(functiondict)
                    funparalist = functiondict1[fun]
                    for para in funparalist:

                        para.insert(0, df)
                        para.insert(0, name)
                        para.insert(0, factorcls)
                        para.insert(0, fun)
                        para = tuple(para)
                        pool.apply_async(finalfun, args=(para,))
                        
                        # finalfun(para)
                pool.close()
                pool.join()
