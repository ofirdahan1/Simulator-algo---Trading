"""
Main entry point for the algorithmic trading bot.

This script initializes the trading environment, sets key configuration parameters,
and starts the trading process. It is the primary file to run for both
backtesting and live trading sessions.
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
# Define the list of stocks to be traded or backtested.
# The list is overwritten multiple times; the last definition is the one that will be used.
# For example, to trade only TQQQ, TSLA, GOOG, NVDA, AAPL, and MSTR, ensure the final line is:
# stocks_check = ['TQQQ','TSLA','GOOG','NVDA','AAPL','MSTR']
stocks_check = ['AAPL','AMD','TQQQ','VOO','DIS','MCD','ITB','TSLA','LLY','MSTR']
stocks_check += ['TSM','NFLX','GOOG','NVDA','AMZN','AVGO','NVO','MA','PG','MRK','HD','AMT','SOXL']
stocks_check += ['META','MAGS','MSFT']
stocks_check = ['JNJ','V','MA','CVX']

# stocks_check = ['AAPL','NFLX','AMD','MSTR','VOO','TQQQ']
stocks_check = ['NVDA','AAPL','SEDG','NKE','SOXL','CAR']
stocks_check = ['SOXL']
stocks_check = ['TQQQ','TSLA','GOOG','NVDA','AAPL','MSTR']


# --- Configuration: Global Settings ---

# Set the initial starting capital for the portfolio.
glb.my_available_money_dollar_start = 200000
glb.my_available_money_dollar = glb.my_available_money_dollar_start

# Determines whether to include pre-market and post-market data in the simulation.
glb.include_pre_post_mkt = False


# --- Configuration: Trading Mode ---
# Set the trading mode for the application.
# - Set to True for backtesting using local historical data.
# - Set to False for live or paper trading via Interactive Brokers.
glb.dbg_local = False


# --- Execution ---
# Initiates the trading process with the configured stocks and settings.
trade_and_update_portfolio_local_data(stocks_check)
# trade_and_update_portfolio_local_data(stocks_check,start="2024-07-01" ,end="2024-07-31")
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
#     glb.PATH_RESULTS = '/Users/ofirdahan/Desktop/interactive brokers/stock_analyzer/local_data_result'
#     glb.PATH_STOCKS_DATA = '/Users/ofirdahan/Desktop/interactive brokers/stock_data/'
#     glb.stocks_data = {}
#     glb.data_request = 'LOCAL'
#
# # # trade_and_update_portfolio_local_data(stocks_check,start="2022-04-01" ,end="2022-05-27")
# #
# #
# #
