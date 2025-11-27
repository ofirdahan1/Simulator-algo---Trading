"""
Main entry point for the backtesting simulator.

This script initializes the simulation environment, sets key configuration
parameters for the backtest, and starts the simulation process. It includes
functionality for running single backtests as well as statistical analysis
to optimize strategy parameters.
"""
import enum

from protfolio_mangment_fun_v2 import *
import globals_v2 as glb

import time
#367.92% NFLX
#113.849% AAPL
#306.96% AMD
# 65.06% VOO
# 407.68% MSTR
# 960.7851% TQQQ

# --- Configuration: Stock Portfolio ---
# Define the list of stocks to be backtested.
# The list is overwritten multiple times; the last definition is the one that will be used.
stocks_check = ['AAPL','AMD','TQQQ','VOO','DIS','MCD','ITB','TSLA','LLY','MSTR']
stocks_check += ['TSM','NFLX','GOOG','NVDA','AMZN','AVGO','NVO','MA','PG','MRK','HD','AMT','SOXL']
stocks_check += ['META','MAGS','MSFT']
stocks_check = ['JNJ','V','MA','CVX']

stocks_check = ['AAPL','QQQ','AMD','DIS','ITB','LLY']
stocks_check += ['NVDA','SEDG','NKE','SOXL','CAR']
stocks_check += ['TQQQ','TSLA','MSTR','VOO']
stocks_check = ['TQQQ']

# --- Configuration: Debug and Local Mode ---
# `dbg_local` is used to switch between different modes of operation.
# It appears to be intended for debugging with a specific local data path.
dbg_local = False
if dbg_local:
    stocks_check = ['TQQQ','TSLA','GOOG','NVDA','AAPL','MSTR']

glb.dbg_on_real_data = dbg_local
# This sets a specific path for local data, which is used when `dbg_local` is True.
glb.local_path_file = f"/Users/ofirdahan/Desktop/interactive_brokers/stock_analyzer/paper_trading_data_result/Program_runs/28_10M_2024->29_10M_2024/day_trade/"


# --- Configuration: Strategy Parameters ---
# These parameters control the behavior of the trading algorithm.
glb.limit_presantage = 3.6  # The percentage for the trailing stop-loss/take-profit limit.
glb.diff_p = 0.8  # A parameter for the trading strategy.
glb.factor = 1  # A factor used in the trading strategy.


# --- Configuration: Simulation Mode ---
# `statistic_flag` controls whether to run a single backtest or a statistical analysis.
# - If True, the script will loop through different strategy parameters to find the optimal combination.
# - If False, it will run a single backtest with the predefined parameters.
glb.statistic_flag = False


# --- Execution ---
if dbg_local:
    # If in debug mode, extract the start and end dates from the local file path.
    start, end = glb.local_path_file.split('/')[-3].replace('M','').replace('_','-').split('->')
    trade_and_update_portfolio_local_data(stocks_check, start=start, end=end)
else:
    if glb.statistic_flag:
        # If statistic_flag is True, run a loop to test different parameters.
        for glb.limit_presantage in np.arange(0.5, 5, 0.1):
            for glb.diff_p in np.arange(0.1, 1, 0.05):
                # for glb.factor in np.arange(0.5,4,0.5):
                trade_and_update_portfolio_local_data(stocks_check, start="2024-01-03", end="2024-07-30")
                
                # Reset global state for the next iteration.
                glb.job_by_one_thread = ''
                glb.my_available_money_dollar_start = 50000
                glb.my_available_money_dollar = glb.my_available_money_dollar_start
                glb.not_first_day = False
                glb.current_date = ''
                glb.demo_portfolio_treads = {}
                glb.my_portfolio = {}
                glb.stock_that_been_used = {}
                glb.my_init_demo_available_money_dollar = 2e5
                glb.flag_first_day = True
                glb.counter = 0
                glb.real_logs = list()
                glb.real_logs_csv = list()
                glb.day_barrier = threading.Barrier(0)
                glb.min_num_of_time_stamp_in_stocks_current_day = 9999
                glb.stocks_data = {}
        
        # Print the sorted results of the statistical analysis.
        new_list = sorted(glb.statistic_list, key=lambda x: x[0], reverse=True)
        for i in new_list:
            print(i)
    else:
        # If not running statistical analysis, run a single backtest with the specified dates.
        trade_and_update_portfolio_local_data(stocks_check, start="2023-05-03", end="2023-12-30")
    # trade_and_update_portfolio_local_data(stocks_check,start="2023-01-03" ,end="2024-07-31")
# trade_and_update_portfolio_local_data(stocks_check,start="2024-09-26" ,end="2024-09-27")
# trade_and_update_portfolio_local_data(stocks_check,start="2022-01-03" ,end="2022-09-30")

# for stock in stocks_check:
#     try:
#         trade_and_update_portfolio_local_data([stock],start="2022-01-03" ,end="2022-09-30")
#     except:
#         x=1
#     glb.job_by_one_thread = ''
#     glb.my_available_money_dollar_start = 2e5
#     glb.my_available_money_dollar = glb.my_available_money_dollar_start
#     glb.not_first_day = False
#     glb.current_date = ''
#     glb.demo_portfolio_treads = {}
#     glb.demo_portfolio_treads_Limit = {}
#     glb.my_portfolio = {}
#     glb.my_init_demo_available_money_dollar = 2e5
#     glb.day_timestamp = 60 * 60 * 24
#     glb.flag_first_day = True
#     glb.counter = 0
#     glb.real_logs = list()
#     glb.real_logs_csv = list()
#     glb.day_barrier = threading.Barrier(0)
#     glb.min_num_of_time_stamp_in_stocks_current_day = 9999
#     glb.slop_d_num_neg_flag = -0.002
#     glb.slop_d_num_pos_flag = 0
#     glb.slop_num_pos_flag = 0
#     glb.PATH_RESULTS = '/Users/ofirdahan/Desktop/interactive_brokers/stock_analyzer/local_data_result'
#     glb.PATH_STOCKS_DATA = '/Users/ofirdahan/Desktop/interactive_brokers/stock_data/'
#     glb.stocks_data = {}
#     glb.data_request = 'LOCAL'
#
# # # trade_and_update_portfolio_local_data(stocks_check,start="2022-04-01" ,end="2022-05-27")
# #
# #
# #
