"""Demo A: SimulationBroker 默认规则（向后兼容）"""
import sys, os
sys.path.insert(0, r'e:\Projects\NDXinfo')

from trading.broker import SimulationBroker, OrderSide, OrderType

print('=== Demo A: SimulationBroker 默认规则（向后兼容） ===')
b = SimulationBroker(initial_cash=100000.0)
b.set_price('AAPL', 180.0)
buy = b.place_order('AAPL', 10, OrderSide.BUY, OrderType.MARKET)
print('BUY  AAPL x10 -> status=' + buy.status.value + ', fill=$' + format(buy.avg_fill_price, '.2f') + ', fee=$' + format(buy.commission, '.2f'))
b.set_price('AAPL', 185.0)
sell = b.place_order('AAPL', 10, OrderSide.SELL, OrderType.MARKET)
print('SELL AAPL x10 -> status=' + sell.status.value + ', fill=$' + format(sell.avg_fill_price, '.2f') + ', fee=$' + format(sell.commission, '.2f'))
acc = b.get_account()
print('账户: cash=$' + format(acc.cash, ',.2f') + ' equity=$' + format(acc.equity, ',.2f') + ' settled=$' + format(acc.settled_cash, ',.2f') + ' 收益=' + format(acc.total_return_pct, '.2f') + '%')
