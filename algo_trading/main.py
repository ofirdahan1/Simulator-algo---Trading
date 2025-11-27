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
stocks_check = ['AAPL','AMD','TQQQ','VOO','DIS','MCD','ITB','TSLA','LLY','MSTR']
stocks_check += ['TSM','NFLX','GOOG','NVDA','AMZN','AVGO','NVO','MA','PG','MRK','HD','AMT','SOXL']
stocks_check += ['META','MAGS','MSFT']
stocks_check = ['JNJ','V','MA','CVX']

# stocks_check = ['AAPL','NFLX','AMD','MSTR','VOO','TQQQ']
stocks_check = ['NVDA','AAPL','SEDG','NKE','SOXL','CAR']
stocks_check = ['SOXL']
stocks_check = ['TQQQ','TSLA','GOOG','NVDA','AAPL','MSTR']

# trade_and_update_portfolio(stocks_check,end="2022-04-28",wanted_num_days = 7,interval="1m")
glb.my_available_money_dollar_start = 200000
glb.my_available_money_dollar = glb.my_available_money_dollar_start
glb.include_pre_post_mkt = False
glb.dbg_local = False
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
