from aat.exchange import SyntheticExchange

s = SyntheticExchange()

# seed
s._seed()

# double orders
s._seedOrders()
print(s)

# test some orders
s._testOrders()
print(s)