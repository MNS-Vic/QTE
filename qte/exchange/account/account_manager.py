#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
账户管理器 - 负责用户账户、资金和持仓的管理
"""
import logging
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
from decimal import Decimal

logger = logging.getLogger("AccountManager")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 使用Decimal确保精确计算
D = lambda x: Decimal(str(x))

@dataclass
class AssetBalance:
    """资产余额类"""
    asset: str                       # 资产名称
    free: Decimal = D(0)             # 可用余额
    locked: Decimal = D(0)           # 锁定余额
    
    @property
    def total(self) -> Decimal:
        """总余额 = 可用 + 锁定"""
        return self.free + self.locked
    
    def __str__(self) -> str:
        return f"{self.asset}: 可用={self.free}, 锁定={self.locked}, 总计={self.total}"

@dataclass
class Position:
    """持仓类"""
    symbol: str                      # 交易对
    amount: Decimal = D(0)           # 持仓数量
    avg_price: Decimal = D(0)        # 平均成本
    unrealized_pnl: Decimal = D(0)   # 未实现盈亏
    
    @property
    def position_value(self) -> Decimal:
        """持仓价值 = 数量 * 平均成本"""
        return self.amount * self.avg_price
    
    def __str__(self) -> str:
        return f"{self.symbol}: 数量={self.amount}, 成本={self.avg_price}, 未实现盈亏={self.unrealized_pnl}"

@dataclass
class TransactionRecord:
    """交易记录类"""
    transaction_id: str              # 交易ID
    user_id: str                     # 用户ID
    transaction_type: str            # 交易类型
    asset: str                       # 资产
    amount: Decimal                  # 数量
    timestamp: datetime = field(default_factory=datetime.now)  # 交易时间
    details: Dict[str, Any] = field(default_factory=dict)  # 详细信息
    
    def __str__(self) -> str:
        return f"{self.transaction_type} {self.amount} {self.asset} at {self.timestamp}"

class UserAccount:
    """用户账户类"""
    
    def __init__(self, user_id: str, name: Optional[str] = None):
        """
        初始化用户账户
        
        Parameters
        ----------
        user_id : str
            用户ID
        name : Optional[str], optional
            用户名称, by default None
        """
        self.user_id = user_id
        self.name = name or user_id
        self.balances: Dict[str, AssetBalance] = {}  # 资产余额
        self.positions: Dict[str, Position] = {}  # 持仓
        self.transactions: List[TransactionRecord] = []  # 交易记录
        
        logger.info(f"用户账户已创建: {user_id}")
    
    def get_balance(self, asset: str) -> AssetBalance:
        """
        获取指定资产的余额
        
        Parameters
        ----------
        asset : str
            资产名称
            
        Returns
        -------
        AssetBalance
            资产余额对象
        """
        if asset not in self.balances:
            self.balances[asset] = AssetBalance(asset)
        return self.balances[asset]
    
    def get_position(self, symbol: str) -> Position:
        """
        获取指定交易对的持仓
        
        Parameters
        ----------
        symbol : str
            交易对
            
        Returns
        -------
        Position
            持仓对象
        """
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)
        return self.positions[symbol]
    
    def deposit(self, asset: str, amount: Decimal) -> bool:
        """
        充值资产
        
        Parameters
        ----------
        asset : str
            资产名称
        amount : Decimal
            充值数量
            
        Returns
        -------
        bool
            是否成功
        """
        if amount <= D(0):
            logger.warning(f"充值金额必须大于0: {amount}")
            return False
            
        balance = self.get_balance(asset)
        balance.free += amount
        
        # 记录交易
        self._add_transaction("DEPOSIT", asset, amount)
        
        logger.info(f"用户 {self.user_id} 充值 {amount} {asset}, 当前余额: {balance.free}")
        return True
    
    def withdraw(self, asset: str, amount: Decimal) -> bool:
        """
        提现资产
        
        Parameters
        ----------
        asset : str
            资产名称
        amount : Decimal
            提现数量
            
        Returns
        -------
        bool
            是否成功
        """
        if amount <= D(0):
            logger.warning(f"提现金额必须大于0: {amount}")
            return False
            
        balance = self.get_balance(asset)
        
        if balance.free < amount:
            logger.warning(f"用户 {self.user_id} 提现 {amount} {asset} 失败: 可用余额不足 {balance.free}")
            return False
            
        balance.free -= amount
        
        # 记录交易
        self._add_transaction("WITHDRAW", asset, -amount)
        
        logger.info(f"用户 {self.user_id} 提现 {amount} {asset}, 当前余额: {balance.free}")
        return True
    
    def lock_asset(self, asset: str, amount: Decimal) -> bool:
        """
        锁定资产（下单冻结）
        
        Parameters
        ----------
        asset : str
            资产名称
        amount : Decimal
            锁定数量
            
        Returns
        -------
        bool
            是否成功
        """
        if amount <= D(0):
            logger.warning(f"锁定金额必须大于0: {amount}")
            return False
            
        balance = self.get_balance(asset)
        
        if balance.free < amount:
            logger.warning(f"用户 {self.user_id} 锁定 {amount} {asset} 失败: 可用余额不足 {balance.free}")
            return False
            
        balance.free -= amount
        balance.locked += amount
        
        # 记录交易
        self._add_transaction("LOCK", asset, amount, {"locked": True})
        
        logger.info(f"用户 {self.user_id} 锁定 {amount} {asset}, 可用: {balance.free}, 锁定: {balance.locked}")
        return True
    
    def unlock_asset(self, asset: str, amount: Decimal) -> bool:
        """
        解锁资产（取消订单）
        
        Parameters
        ----------
        asset : str
            资产名称
        amount : Decimal
            解锁数量
            
        Returns
        -------
        bool
            是否成功
        """
        if amount <= D(0):
            logger.warning(f"解锁金额必须大于0: {amount}")
            return False
            
        balance = self.get_balance(asset)
        
        if balance.locked < amount:
            logger.warning(f"用户 {self.user_id} 解锁 {amount} {asset} 失败: 锁定余额不足 {balance.locked}")
            return False
            
        balance.locked -= amount
        balance.free += amount
        
        # 记录交易
        self._add_transaction("UNLOCK", asset, amount, {"unlocked": True})
        
        logger.info(f"用户 {self.user_id} 解锁 {amount} {asset}, 可用: {balance.free}, 锁定: {balance.locked}")
        return True
    
    def update_position(self, symbol: str, trade_amount: Decimal, trade_price: Decimal, is_buy: bool) -> Position:
        """
        更新持仓信息
        
        Parameters
        ----------
        symbol : str
            交易对
        trade_amount : Decimal
            交易数量
        trade_price : Decimal
            交易价格
        is_buy : bool
            是否为买入
            
        Returns
        -------
        Position
            更新后的持仓
        """
        position = self.get_position(symbol)
        
        # 买入: 增加持仓，重新计算平均成本
        if is_buy:
            # 计算新的平均成本
            old_value = position.amount * position.avg_price
            new_value = trade_amount * trade_price
            new_amount = position.amount + trade_amount
            
            if new_amount > D(0):
                new_avg_price = (old_value + new_value) / new_amount
            else:
                new_avg_price = D(0)
                
            position.amount = new_amount
            position.avg_price = new_avg_price
            
        # 卖出: 减少持仓
        else:
            # 计算已实现盈亏
            realized_pnl = trade_amount * (trade_price - position.avg_price)
            
            # 更新持仓
            position.amount -= trade_amount
            
            # 如果持仓为0，重置平均成本
            if position.amount <= D(0):
                position.amount = D(0)
                position.avg_price = D(0)
                
        self._add_transaction("POSITION_UPDATE", symbol, trade_amount if is_buy else -trade_amount, 
                            {"price": trade_price, "is_buy": is_buy})
                
        logger.info(f"用户 {self.user_id} 更新持仓: {symbol}, 数量={position.amount}, 成本={position.avg_price}")
        return position
    
    def settle_trade(self, symbol: str, base_asset: str, quote_asset: str, 
                    amount: Decimal, price: Decimal, is_buy: bool, fee: Decimal = D(0), 
                    fee_asset: Optional[str] = None) -> bool:
        """
        结算交易
        
        Parameters
        ----------
        symbol : str
            交易对
        base_asset : str
            基础资产（交易对左边）
        quote_asset : str
            计价资产（交易对右边）
        amount : Decimal
            交易数量
        price : Decimal
            交易价格
        is_buy : bool
            是否为买入
        fee : Decimal, optional
            手续费, by default D(0)
        fee_asset : Optional[str], optional
            手续费资产, by default None
            
        Returns
        -------
        bool
            是否成功
        """
        if amount <= D(0) or price <= D(0):
            logger.warning(f"交易数量和价格必须大于0: 数量={amount}, 价格={price}")
            return False
            
        # 计算交易金额
        trade_value = amount * price
        
        # 买入: 扣除计价资产，增加基础资产
        if is_buy:
            # 检查余额
            quote_balance = self.get_balance(quote_asset)
            if quote_balance.locked < trade_value:
                logger.warning(f"用户 {self.user_id} 买入结算失败: 锁定的 {quote_asset} 不足, 需要 {trade_value}, 实际锁定 {quote_balance.locked}")
                return False
                
            # 扣除计价资产
            quote_balance.locked -= trade_value
            
            # 增加基础资产
            base_balance = self.get_balance(base_asset)
            base_balance.free += amount
            
            # 更新持仓
            self.update_position(symbol, amount, price, True)
            
        # 卖出: 扣除基础资产，增加计价资产
        else:
            # 检查持仓
            base_balance = self.get_balance(base_asset)
            if base_balance.locked < amount:
                logger.warning(f"用户 {self.user_id} 卖出结算失败: 锁定的 {base_asset} 不足, 需要 {amount}, 实际锁定 {base_balance.locked}")
                return False
                
            # 扣除基础资产
            base_balance.locked -= amount
            
            # 增加计价资产
            quote_balance = self.get_balance(quote_asset)
            quote_balance.free += trade_value
            
            # 更新持仓
            self.update_position(symbol, amount, price, False)
            
        # 扣除手续费
        if fee > D(0):
            fee_asset_name = fee_asset or (base_asset if is_buy else quote_asset)
            fee_balance = self.get_balance(fee_asset_name)
            
            if fee_balance.free < fee:
                logger.warning(f"用户 {self.user_id} 手续费扣除失败: {fee_asset_name} 余额不足, 需要 {fee}, 实际可用 {fee_balance.free}")
                # 继续执行，不因手续费不足而失败交易
            else:
                fee_balance.free -= fee
                logger.info(f"用户 {self.user_id} 扣除手续费 {fee} {fee_asset_name}")
                
        # 记录交易
        trade_type = "BUY" if is_buy else "SELL"
        self._add_transaction(trade_type, symbol, amount if is_buy else -amount, 
                            {"price": price, "value": trade_value, "fee": fee, "fee_asset": fee_asset})
                
        logger.info(f"用户 {self.user_id} 结算 {trade_type} 交易: {amount} {symbol} @ {price}, 总额: {trade_value}")
        return True
    
    def _add_transaction(self, txn_type: str, asset: str, amount: Decimal, details: Dict[str, Any] = None) -> None:
        """
        添加交易记录
        
        Parameters
        ----------
        txn_type : str
            交易类型
        asset : str
            资产
        amount : Decimal
            数量
        details : Dict[str, Any], optional
            详细信息, by default None
        """
        transaction = TransactionRecord(
            transaction_id=str(uuid.uuid4()),
            user_id=self.user_id,
            transaction_type=txn_type,
            asset=asset,
            amount=amount,
            details=details or {}
        )
        
        self.transactions.append(transaction)
        
    def get_account_snapshot(self) -> Dict[str, Any]:
        """
        获取账户快照
        
        Returns
        -------
        Dict[str, Any]
            账户快照，包含余额和持仓信息
        """
        return {
            "user_id": self.user_id,
            "name": self.name,
            "balances": {asset: {"free": float(balance.free), "locked": float(balance.locked), "total": float(balance.total)} 
                        for asset, balance in self.balances.items()},
            "positions": {symbol: {"amount": float(position.amount), "avg_price": float(position.avg_price)} 
                        for symbol, position in self.positions.items() if position.amount > 0}
        }


class AccountManager:
    """账户管理器，管理所有用户账户"""
    
    def __init__(self):
        """初始化账户管理器"""
        self.accounts: Dict[str, UserAccount] = {}  # 用户ID -> 账户对象
        self.account_listeners = []  # 账户更新监听器
        self.active_symbols: Set[str] = set()  # 活跃交易对
        
        logger.info("账户管理器已初始化")
    
    def create_account(self, user_id: str, name: Optional[str] = None) -> UserAccount:
        """
        创建用户账户
        
        Parameters
        ----------
        user_id : str
            用户ID
        name : Optional[str], optional
            用户名称, by default None
            
        Returns
        -------
        UserAccount
            创建的账户对象
        """
        if user_id in self.accounts:
            logger.warning(f"用户账户 {user_id} 已存在")
            return self.accounts[user_id]
            
        account = UserAccount(user_id, name)
        self.accounts[user_id] = account
        
        logger.info(f"创建用户账户: {user_id}")
        return account
    
    def get_account(self, user_id: str) -> Optional[UserAccount]:
        """
        获取用户账户
        
        Parameters
        ----------
        user_id : str
            用户ID
            
        Returns
        -------
        Optional[UserAccount]
            用户账户对象，如不存在则返回None
        """
        account = self.accounts.get(user_id)
        if not account:
            logger.warning(f"用户账户 {user_id} 不存在")
        return account
    
    def add_active_symbol(self, symbol: str) -> None:
        """
        添加活跃交易对
        
        Parameters
        ----------
        symbol : str
            交易对
        """
        self.active_symbols.add(symbol)
        logger.info(f"添加活跃交易对: {symbol}")
    
    def lock_funds_for_order(self, user_id: str, symbol: str, 
                          side: str, amount: Decimal, price: Optional[Decimal] = None,
                          base_asset: Optional[str] = None, quote_asset: Optional[str] = None) -> bool:
        """
        为订单锁定资金
        
        Parameters
        ----------
        user_id : str
            用户ID
        symbol : str
            交易对
        side : str
            买卖方向 ("BUY" 或 "SELL")
        amount : Decimal
            数量
        price : Optional[Decimal], optional
            价格, by default None (市价单)
        base_asset : Optional[str], optional
            基础资产, by default None (从交易对解析)
        quote_asset : Optional[str], optional
            计价资产, by default None (从交易对解析)
            
        Returns
        -------
        bool
            是否成功
        """
        account = self.get_account(user_id)
        if not account:
            return False
            
        # 解析资产
        if not base_asset or not quote_asset:
            # 实际项目中应该有更复杂的逻辑解析交易对
            base_asset = base_asset or symbol.split('/')[0] if '/' in symbol else symbol[:3]
            quote_asset = quote_asset or symbol.split('/')[1] if '/' in symbol else symbol[3:]
            
        # 买单: 锁定计价资产
        if side.upper() == "BUY":
            if not price:
                logger.warning(f"买单必须指定价格")
                return False
                
            total_value = amount * price
            return account.lock_asset(quote_asset, total_value)
            
        # 卖单: 锁定基础资产
        elif side.upper() == "SELL":
            return account.lock_asset(base_asset, amount)
            
        else:
            logger.warning(f"未知的订单方向: {side}")
            return False
    
    def unlock_funds_for_order(self, user_id: str, symbol: str, 
                            side: str, amount: Decimal, price: Optional[Decimal] = None,
                            base_asset: Optional[str] = None, quote_asset: Optional[str] = None) -> bool:
        """
        解锁订单资金（取消订单）
        
        Parameters
        ----------
        user_id : str
            用户ID
        symbol : str
            交易对
        side : str
            买卖方向 ("BUY" 或 "SELL")
        amount : Decimal
            数量
        price : Optional[Decimal], optional
            价格, by default None
        base_asset : Optional[str], optional
            基础资产, by default None (从交易对解析)
        quote_asset : Optional[str], optional
            计价资产, by default None (从交易对解析)
            
        Returns
        -------
        bool
            是否成功
        """
        account = self.get_account(user_id)
        if not account:
            return False
            
        # 解析资产
        if not base_asset or not quote_asset:
            # 实际项目中应该有更复杂的逻辑解析交易对
            base_asset = base_asset or symbol.split('/')[0] if '/' in symbol else symbol[:3]
            quote_asset = quote_asset or symbol.split('/')[1] if '/' in symbol else symbol[3:]
            
        # 买单: 解锁计价资产
        if side.upper() == "BUY":
            if not price:
                logger.warning(f"买单必须指定价格")
                return False
                
            total_value = amount * price
            return account.unlock_asset(quote_asset, total_value)
            
        # 卖单: 解锁基础资产
        elif side.upper() == "SELL":
            return account.unlock_asset(base_asset, amount)
            
        else:
            logger.warning(f"未知的订单方向: {side}")
            return False
    
    def settle_trade(self, user_id: str, symbol: str, 
                    side: str, amount: Decimal, price: Decimal,
                    fee: Decimal = D(0), fee_asset: Optional[str] = None,
                    base_asset: Optional[str] = None, quote_asset: Optional[str] = None) -> bool:
        """
        结算交易
        
        Parameters
        ----------
        user_id : str
            用户ID
        symbol : str
            交易对
        side : str
            买卖方向 ("BUY" 或 "SELL")
        amount : Decimal
            数量
        price : Decimal
            价格
        fee : Decimal, optional
            手续费, by default D(0)
        fee_asset : Optional[str], optional
            手续费资产, by default None
        base_asset : Optional[str], optional
            基础资产, by default None (从交易对解析)
        quote_asset : Optional[str], optional
            计价资产, by default None (从交易对解析)
            
        Returns
        -------
        bool
            是否成功
        """
        account = self.get_account(user_id)
        if not account:
            return False
            
        # 解析资产
        if not base_asset or not quote_asset:
            # 实际项目中应该有更复杂的逻辑解析交易对
            base_asset = base_asset or symbol.split('/')[0] if '/' in symbol else symbol[:3]
            quote_asset = quote_asset or symbol.split('/')[1] if '/' in symbol else symbol[3:]
            
        is_buy = side.upper() == "BUY"
        
        return account.settle_trade(
            symbol=symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            amount=amount,
            price=price,
            is_buy=is_buy,
            fee=fee,
            fee_asset=fee_asset
        )
    
    def add_account_listener(self, listener):
        """
        添加账户更新监听器
        
        Parameters
        ----------
        listener : callable
            监听器函数，接收用户ID和账户快照作为参数
        """
        self.account_listeners.append(listener)
        
    def remove_account_listener(self, listener):
        """
        移除账户更新监听器
        
        Parameters
        ----------
        listener : callable
            要移除的监听器函数
        """
        if listener in self.account_listeners:
            self.account_listeners.remove(listener)
    
    def get_all_accounts(self) -> Dict[str, UserAccount]:
        """
        获取所有用户账户
        
        Returns
        -------
        Dict[str, UserAccount]
            用户账户字典
        """
        return self.accounts
        
    def _notify_account_listeners(self, user_id: str) -> None:
        """
        通知账户监听器
        
        Parameters
        ----------
        user_id : str
            用户ID
        """
        account = self.get_account(user_id)
        if not account:
            return
            
        snapshot = account.get_account_snapshot()
        
        for listener in self.account_listeners:
            try:
                listener(user_id, snapshot)
            except Exception as e:
                logger.error(f"通知账户监听器失败: {e}")