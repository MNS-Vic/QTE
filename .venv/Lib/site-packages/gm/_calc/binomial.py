'''
通过 Binomial options pricing model 进行对 美式期货期权 进行定价、计算隐含波动率与希腊值
https://en.wanweibaike.com/wiki-Binomial%20options%20model#Method

__author__ = 'Charkong'
——date__ = '2021-06-29'
'''
import numpy as np

def check_value(cp: float = 1, v: float = 0.1) -> None:

    if cp not in [1., 1, -1., -1]:
        raise ValueError('cp 错误！请检查是否为±1 ')

    if v <= 0:
        raise ValueError('v 错误！ 请检查是否为>0 ')


def calculate_price(f: float, k: float, r: float, v: float, t: float, cp: float = 1., n: float = 15, return_tree=False):
    # 二叉树理论价格
    check_value(cp)

    # 计算二叉树相关参数
    time = float(t)/n  # dt
    discount = np.exp(- r * time)  # 贴现幅度
    u = np.exp(v*time**0.5)  # 上升幅度
    d = np.exp(-v*time**0.5)  # 下降幅度
    a = np.exp(r*time)
    p = (a-d)/(u-d)

    # 计算相关概率值
    p_up = p/a
    p_down = (1-p)/a

    # 生成标的物价格tree
    underlying_price_tree = np.zeros((n+1, n+1))
    underlying_price_tree[0, 0] = f  # init value
    for i in range(1, n + 1):
        underlying_price_tree[0, i] = underlying_price_tree[0, i - 1] * u
        for j in range(1, n + 1):
            underlying_price_tree[j,
                                  i] = underlying_price_tree[j - 1, i - 1] * d

    # 根据 标的物价格tree 的期望反推 期权价格tree
    option_price_tree = np.zeros((n+1, n+1))
    for j in range(n + 1):
        option_price_tree[j, n] = max(
            0, cp * (underlying_price_tree[j, n] - k))

    for i in range(n - 1, -1, -1):
        for j in range(i + 1):
            option_price_tree[j, i] = max(
                (p_up * option_price_tree[j, i + 1] + p_down *
                 option_price_tree[j + 1, i + 1]) * discount,
                cp * (underlying_price_tree[j, i] - k),
                0
            )

    # 返回tree
    if return_tree:
        return option_price_tree, underlying_price_tree
    else:
        return option_price_tree[0][0]


def calculate_delta(f: float = 0, k: float = 0, r: float = 0, v: float = 0, t: float = 0, cp: float = 1., cash: bool = False, n: int = 15, option_price_tree: np.array = None, underlying_price_tree: np.array = None,) -> float:
    # 计算delta

    check_value(cp, v)
    if not issubsctype(option_price_tree, type(np.array)):
        option_price_tree, underlying_price_tree = calculate_price(
            f, k, r, v, t, cp, n, True)

    d_o_p = option_price_tree[0, 1] - option_price_tree[1, 1]
    d_u_p = underlying_price_tree[0, 1] - underlying_price_tree[1, 1]

    delta = d_o_p/d_u_p
    delta = delta * f * 0.01 if cash else delta
    return delta


def calculate_vega(f: float = 0, k: float = 0, r: float = 0, v: float = 0, t: float = 0, cp: float = 1., cash: bool = False, n: int = 15, theoretical_price: float = None) -> float:
    # 计算 vage
    if v <= 0:
        return 0

    if not theoretical_price:
        theoretical_price = calculate_price(f, k, r, v,  t, cp, n)
    theoretical_price_dv = calculate_price(f, k, r,  v * 1.001, t, cp, n)

    vega = (theoretical_price_dv - theoretical_price) / (v*0.001)
    vega = vega * 0.01 if cash else vega

    return vega


def calculate_theta(f: float = 0, k: float = 0, r: float = 0, v: float = 0, t: float = 0, cp: float = 1., cash: bool = False, n: int = 15, option_price_tree: np.array = None) -> float:
    # 计算 theta
    check_value(cp, v=v)

    if not issubsctype(option_price_tree, type(np.array)):
        option_price_tree, underlying_price_tree = calculate_price(
            f, k, r, v, t, cp, n, True)

    time = t/n
    theta = (option_price_tree[1, 2] - option_price_tree[0, 0]) / (2 * time)
    theta = theta / 252 if cash else theta

    return theta


def calculate_rho(f: float = 0, k: float = 0, r: float = 0, v: float = 0, t: float = 0, cp: float = 1., cash: bool = False, n: int = 15, theoretical_price: float = None) -> float:
    # 计算 rho
    check_value(cp, v=v)

    if not theoretical_price:
        theoretical_price = calculate_price(f, k, r, v,  t, cp, n)
    theoretical_price_dv = calculate_price(f, k, r * 1.001,  v, t, cp, n)

    rho = (theoretical_price_dv - theoretical_price) / (r*0.001)
    rho = rho * 0.01 if cash else rho

    return rho


def calculate_gamma(f: float, k: float, r: float, v: float, t: float, cp: float = 1.,  cash: bool = False, n: int = 15, option_price_tree: np.array = None, underlying_price_tree: np.array = None,) -> float:
    # 计算 gamma
    check_value(v=v)

    if not issubsctype(option_price_tree, type(np.array)):
        option_price_tree, underlying_price_tree = calculate_price(
            f, k, r, v, t, cp, n, True)

    gamma_d1 = (option_price_tree[0, 2] - option_price_tree[1, 2]) / \
        (underlying_price_tree[0, 2] - underlying_price_tree[1, 2])
    gamma_d2 = (option_price_tree[1, 2] - option_price_tree[2, 2]) / \
        (underlying_price_tree[1, 2] - underlying_price_tree[2, 2])
    gamma = (gamma_d1 - gamma_d2) / \
        (0.5 * (underlying_price_tree[0, 2] - underlying_price_tree[2, 2]))
    gamma = gamma * pow(f, 2) * 0.0001 if cash else gamma

    return gamma


def calculate_greeks(f: float, k: float, r: float, v: float, t: float, cp: float = 1., cash: bool = False, n: int = 15) -> float:
    # 计算 greeks
    check_value(v=v)

    option_price_tree, underlying_price_tree = calculate_price(
        f, k, r, v, t, cp, n, True)
    price = option_price_tree[0][0]
    delta = calculate_delta(f, k, r, v, t, cp, cash, n,
                            option_price_tree, underlying_price_tree)
    vega = calculate_vega(f, k, r, v, t, cash, n, price)
    theta = calculate_theta(f, k, r, v, t, cp, cash, n, option_price_tree)
    rho = calculate_rho(f, k, r, v, t, cp, cash, n, price)
    gamma = calculate_gamma(f, k, r, v, t, cash, n,
                            option_price_tree, underlying_price_tree)

    return price, delta, vega, theta, rho, gamma


def calculate_iv(p: float, f: float, k: float, r: float, t: float, cp: float = 1., n: int = 15,) -> float:
    # 通过 Newton-Raphson-Method 计算 iv
    check_value(cp)

    # 根据无套利定价原理，期权价格不能小于其内在价值
    if cp == 1 and p <= (f - k) * np.exp(- r * t):
        return 0
    elif cp == -1 and p <= (k - f) * np.exp(-r*t):
        return 0

    # 初始值
    iv = 0.15

    for i in range(50):

        # 计算最新iv的理论价格与vega
        price = calculate_price(f, k, r, iv, t, cp, n)
        vega = calculate_vega(f, k, r, iv, t, cash=False,
                              n=n, theoretical_price=price)
        if not vega:
            break

        # 计算误差限
        dx = (p - price)/vega
        if abs(dx) < 0.00001:
            break

        iv += dx

    if iv <= 0:
        return 0

    return iv
