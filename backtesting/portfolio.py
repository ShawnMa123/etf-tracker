import pandas as pd

class Account:
    """
    代表一个投资账户，用于跟踪持股、投入和市值。
    """
    def __init__(self, name: str, tickers: list = None):
        """
        初始化一个账户。
        
        :param name: 账户名称 (e.g., "My Portfolio", "SPY")
        :param tickers: 此账户将持有的所有可能的股票代码
        """
        self.name = name
        self.shares = {ticker: 0.0 for ticker in tickers} if tickers else {}
        self.total_invested = 0.0
        
    def add_investment(self, amount: float):
        """
        记录一笔新的投资，增加总投入本金。
        
        :param amount: 投入的金额
        """
        self.total_invested += amount

    def buy(self, ticker: str, num_shares: float):
        """
        向账户中增加指定数量的股票。
        
        :param ticker: 股票代码
        :param num_shares: 购买的股数
        """
        if ticker not in self.shares:
            self.shares[ticker] = 0.0
        self.shares[ticker] += num_shares

    def get_market_value(self, current_prices: pd.Series) -> float:
        """
        根据当前价格计算账户的总市值。
        
        :param current_prices: 一个包含当日所有相关股票价格的 pandas Series
        :return: 账户的总市值
        """
        value = 0.0
        for ticker, num_shares in self.shares.items():
            if num_shares > 0 and ticker in current_prices:
                value += num_shares * current_prices[ticker]
        return value