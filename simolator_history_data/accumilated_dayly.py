"""
Compound Interest Calculator.

This script calculates the future value of an investment based on a fixed
daily profit rate over a specified period (in years, months, and days).
It can be used for financial projections and to understand the power of
compounding.
"""
# --- Configuration ---
# The average daily profit rate as a percentage (e.g., 0.3 for 0.3%).
avg_dayly_prof = 0.3
# The number of additional days for the calculation.
days = 0
# The number of months for the calculation.
mounts = 0
# The number of years for the calculation.
years = 10
# The initial investment amount.
init_money = 100000
current_money = init_money

# --- Calculation ---
# Calculate the total number of trading days.
# Assumes an average of 21.4 trading days per month and 260.7 per year.
total_days = int(days + (21.4 * mounts) + years * 260.7)

# Calculate the compounded future value.
for day in range(total_days):
    current_money *= (1 + avg_dayly_prof / 100)

# --- Output ---
# Print the final results.
txt = f"P&L: {round(100 * (current_money - init_money) / init_money, 2)}%  current_money:{current_money}"
print(txt)