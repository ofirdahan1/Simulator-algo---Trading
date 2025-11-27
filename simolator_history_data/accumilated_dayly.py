avg_dayly_prof = 0.3
days = 0
mounts = 0
years = 10
init_money = 100000
current_money = init_money

total_days = int(days+(21.4*mounts)+years*260.7)

for day in range(total_days):
    current_money *= (1+avg_dayly_prof/100)

txt = f"P&L: {round(100*(current_money-init_money)/init_money,2)}%  current_money:{current_money}"
print(txt)