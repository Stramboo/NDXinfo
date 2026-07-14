"""Demo A2: 仿真规则生效 + T+1 拦截 + 拒绝原因码"""
import sys
sys.path.insert(0, r'e:\Projects\NDXinfo')

from trading.broker import SimulationBroker, OrderSide, OrderType, REJECT_T_PLUS_ONE, REJECT_INSUFFICIENT_CASH
from trading.sim_rules import SimExecutionRules

print('=== Demo A2: 启用滑点 + 佣金 + T+1 ===')

# A2-1: 滑点 + 佣金
print('\n[A2-1] slippage=5bps + 每笔佣金 $0.01，最低 $1')
b = SimulationBroker(initial_cash=100000.0,
                     rules=SimExecutionRules(slippage_bps=5,
                                             commission_per_share=0.01,
                                             min_commission=1.0))
b.set_price('NVDA', 500.0)
buy = b.place_order('NVDA', 100, OrderSide.BUY, OrderType.MARKET)
print('BUY  fill=$' + format(buy.avg_fill_price, '.4f') + ' (理论=' + format(500.0 * 1.0005, '.4f') + ')')
print('     fee=$' + format(buy.commission, '.2f') + ' (理论=max(100*0.01, 1.0)=$1.00)')

# A2-2: T+1
print('\n[A2-2] t_plus_one=True: 卖出后立刻买入应被拦截')
b2 = SimulationBroker(initial_cash=100000.0,
                      rules=SimExecutionRules(t_plus_one=True))
b2.set_price('AAPL', 100.0)
first = b2.place_order('AAPL', 800, OrderSide.BUY, OrderType.MARKET)   # 用掉 8 万
print('first BUY -> status=' + first.status.value + ' settled=$' + format(b2.get_account().settled_cash, ',.2f'))
b2.set_price('MSFT', 100.0)
second = b2.place_order('MSFT', 300, OrderSide.BUY, OrderType.MARKET)  # 应被拦截
print('second BUY -> status=' + second.status.value)
print('           rejection_code=' + str(second.rejection_code) + ' (期望 REJECT_T_PLUS_ONE=' + str(REJECT_T_PLUS_ONE) + ')')
print('           note="' + second.note + '"')

# A2-3: 资金不足的拒绝原因码
print('\n[A2-3] 资金不足 -> REJECT_INSUFFICIENT_CASH')
b3 = SimulationBroker(initial_cash=1000.0)
b3.set_price('XYZ', 100.0)
r = b3.place_order('XYZ', 100, OrderSide.BUY, OrderType.MARKET)
print('rejected -> code=' + str(r.rejection_code) + ' (期望=' + str(REJECT_INSUFFICIENT_CASH) + ') note="' + r.note + '"')
