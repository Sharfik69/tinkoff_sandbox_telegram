from decimal import Decimal

import tinvest
from tinvest import SandboxRegisterRequest, BrokerAccountType, SandboxSetCurrencyBalanceRequest, SandboxCurrency

import settings


class User:
    def __init__(self):
        self.client = tinvest.SyncClient(settings.__TINKOFF_API__, use_sandbox=True)

        self.client.clear_sandbox_account()

        xx = SandboxRegisterRequest(broker_account_type=BrokerAccountType.tinkoff)
        self.client.register_sandbox_account(xx)

        self.our_currency = {'rub': SandboxCurrency.rub, 'eur': SandboxCurrency.eur, 'usd': SandboxCurrency.usd}

        self.messages_properties = {'usd': 'Долларов', 'rub': 'Рублей', 'eur': 'Евро'}

        print('Создали новый акк')

    def top_up_balance(self, balance, curr):
        current_balance = self.get_balance(beatiful=False)
        already_have = current_balance[curr]
        a = SandboxSetCurrencyBalanceRequest(balance=Decimal(balance) + already_have, currency=self.our_currency.get(curr, SandboxCurrency.rub))
        self.client.set_sandbox_currencies_balance(a)
        print(balance, curr)
        return True

    def get_balance(self, beatiful=True):
        portfolio = self.client.get_portfolio_currencies()
        sum_dict = {self.messages_properties.get(x.currency.name, x.currency.name) if beatiful else x.currency.name: x.balance for x in portfolio.payload.currencies}
        return sum_dict
