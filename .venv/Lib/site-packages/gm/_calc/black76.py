"""
通过 black 76 定价模型进行对 欧式期货期权 进行定价、计算隐含波动率与希腊值
https://en.wanweibaike.com/wiki-The%20Greeks%20(finance)#Greeks_for_multi-asset_options

__author__ = 'Charkong'
——date__ = '2021-06-29'
"""

import numpy as np

from gm._calc import load_norm


def calculate_d1(f, k, r, v, t):
    # type: (float, float, float, float, float) -> float
    """计算d1"""
    if t < 0:
        raise ValueError("剩余时间不能为负, t={}".format(t))
    if t < 0.01:
        t = 0.01
    return (np.log(f / k) + (v ** 2 * 0.5) * t) / (v * np.sqrt(t))


def calculate_d2(d1, v, t):
    # type: (float, float, float) -> float
    """计算d2"""
    return d1 - v * np.sqrt(t)


def check_value(cp=1, v=0.1):
    # type: (float, float) -> None

    if cp not in [1.0, 1, -1.0, -1]:
        raise ValueError("cp 错误！请检查是否为±1 ")

    if v <= 0:
        raise ValueError("v 错误！ 请检查是否为>0 ")


def calculate_price(f, k, r, v, t, cp=1.0, d1=None):
    # type: (float, float, float, float, float, float, float|None) -> float
    """b76理论价格"""
    norm = load_norm()

    check_value(cp)
    if v <= 0:
        return max(0, cp * (f - k))

    if not d1:
        d1 = calculate_d1(f, k, r, v, t)
    d2 = calculate_d2(d1, v, t)

    return (f * norm.cdf(d1 * cp) - k * norm.cdf(d2 * cp)) * cp * np.exp(-r * t)


def calculate_delta(f, k, r, v, t, cp=1.0, cash=False, d1=None):
    # type: (float, float, float, float, float, float, bool, float|None) -> float
    """计算delta"""

    norm = load_norm()

    check_value(cp, v)
    if not d1:
        d1 = calculate_d1(f, k, r, v, t)

    delta = norm.cdf(cp * d1) * cp * np.exp(-r * t)
    delta = delta * f * 0.01 if cash else delta
    return delta


def calculate_vega(f, k, r, v, t, cash=False, d1=None):
    # type: (float, float, float, float, float, bool, float|None) -> float
    """计算 vage"""
    norm = load_norm()
    if v <= 0:
        return 0

    if not d1:
        d1 = calculate_d1(f, k, r, v, t)

    vega = f * np.exp(-r * t) * norm.pdf(d1) * np.sqrt(t)
    vega = vega * 0.01 if cash else vega

    return vega


def calculate_theta(f, k, r, v, t, cp=1.0, cash=False, d1=None):
    # type: (float, float, float, float, float, float, bool, float|None) -> float
    """计算 theta"""
    norm = load_norm()

    check_value(cp, v=v)

    if not d1:
        d1 = calculate_d1(f, k, r, v, t)
    d2 = calculate_d2(d1, v, t)

    theta = (
        -f * np.exp(-r * t) * norm.pdf(d1) * v / (2 * np.sqrt(t))
        - cp * r * k * np.exp(-r * t) * norm.cdf(d2 * cp)
        + cp * r * f * np.exp(-r * t) * norm.cdf(d1 * cp)
    )
    theta = theta / 252 if cash else theta

    return theta


def calculate_rho(f, k, r, v, t, cp=1.0, cash=False, d1=None):
    # type: (float, float, float, float, float, float, bool, float|None) -> float
    """计算 rho"""

    norm = load_norm()

    check_value(cp, v=v)

    if not d1:
        d1 = calculate_d1(f, k, r, v, t)
    d2 = calculate_d2(d1, v, t)
    rho = -t * np.exp(-r * t) * cp * \
        (f * norm.cdf(d1 * cp) - k * norm.cdf(cp * d2))
    rho = rho * 0.01 if cash else rho

    return rho


def calculate_gamma(f, k, r, v, t, cash=False, d1=None):
    # type: (float, float, float, float, float, bool, float|None) -> float
    """计算 gamma"""

    norm = load_norm()

    check_value(v=v)

    if not d1:
        d1 = calculate_d1(f, k, r, v, t)

    gamma = norm.pdf(d1) * np.exp(-r * t) / (f * v * np.sqrt(t))
    gamma = gamma * pow(f, 2) * 0.0001 if cash else gamma

    return gamma


def calculate_greeks(f, k, r, v, t, cp=1.0, cash=False, d1=None):
    # type: (float, float, float, float, float, float, bool, float|None) ->  tuple[float, float, float, float, float, float]
    """计算 greeks"""
    check_value(v=v)

    if not d1:
        d1 = calculate_d1(f, k, r, v, t)

    price = calculate_price(f, k, r, v, t, cp, d1)
    delta = calculate_delta(f, k, r, v, t, cp, cash, d1)
    vega = calculate_vega(f, k, r, v, t, cash, d1)
    theta = calculate_theta(f, k, r, v, t, cp, cash, d1)
    rho = calculate_rho(f, k, r, v, t, cp, cash, d1)
    gamma = calculate_gamma(f, k, r, v, t, cash, d1)

    return price, delta, vega, theta, rho, gamma


def calculate_iv(p, f, k, r, t, cp=1.0):
    # type: (float, float, float, float, float, float) -> float
    """通过 Newton-Raphson-Method 计算 iv"""
    check_value(cp)

    # 根据无套利定价原理，期权价格不能小于其内在价值
    if cp == 1 and p <= (f - k) * np.exp(-r * t):
        return 0
    elif cp == -1 and p <= (k - f) * np.exp(-r * t):
        return 0

    # 初始值
    iv = 0.22

    for i in range(50):

        # 计算最新iv的理论价格与vega
        d1 = calculate_d1(f, k, r, iv, t)
        price = calculate_price(f, k, r, iv, t, cp, d1)
        vega = calculate_vega(f, k, r, iv, t, cash=False, d1=d1)

        if not vega:
            break

        # 计算误差限
        dx = (p - price) / vega
        if abs(dx) < 0.00001:
            break

        iv += dx

    if iv <= 0:
        return 0

    return iv
