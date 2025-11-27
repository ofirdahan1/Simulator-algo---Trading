"""
Global State and Configuration for the Backtesting Simulator.

This module serves as a centralized store for all global variables, configuration
parameters, and shared data structures used across the backtesting application.
It is imported by various modules to access and modify the application's state.

Warning:
This approach to state management can be fragile in a multi-threaded
environment. Race conditions and other concurrency issues can arise if access
to shared variables is not properly synchronized.
"""
import threading
#50000 23876701.20093375 23826701.20093375 47653.402401867505 %->0.2

# --- General Simulation Flags ---
dbg_on_real_data = False  # If True, uses a specific local path for debugging.
local_path_file = ''  # The specific local path for debug data.
job_by_one_thread = ''  # Holds the name of the stock being processed if running in single-thread mode.
statistic_flag = True  # If True, runs the simulation in statistical analysis mode to test multiple parameters.
statistic_list = []  # A list to store the results of the statistical analysis.


# --- Portfolio and Money Management ---
my_available_money_dollar_start = 50000  # Initial capital for the portfolio.
my_available_money_dollar = my_available_money_dollar_start  # The current available cash in the portfolio.
my_portfolio = {}  # Dictionary to hold the `Real_Stock_Object` instances for the live portfolio.
stock_that_been_used = {}  # Tracks which stocks have been traded.
my_init_demo_available_money_dollar = 2e5  # Initial capital for each demo stock simulation.


# --- Strategy and Commission Parameters ---
ratio_trade_in_volume_minute = 0.1  # The ratio of the volume to trade in a single minute.
limit_presantage = 1  # The percentage for the trailing stop-loss/take-profit limit.
factor = 1  # A factor used in the trading strategy.
diff_p = 0.3  # A parameter for the trading strategy.
real_time_commision = 0.03  # A commission parameter.
avg_commission_per_shear = 0.0075  # The average commission per share.
slop_d_num_neg_flag = -0.002  # A parameter for the slope calculation in the trading strategy.
slop_d_num_pos_flag = 0  # A parameter for the slope calculation in the trading strategy.
slop_num_pos_flag = 0  # A parameter for the slope calculation in the trading strategy.


# --- Simulation State ---
not_first_day = False  # Flag to indicate if it's not the first day of the simulation.
current_date = ''  # The current date of the simulation.
demo_portfolio_treads = {}  # Dictionary to hold the `Demo_Stock_Object` instances for simulation.
day_timestamp = 60 * 60 * 24  # The number of seconds in a day.
flag_first_day = True  # Flag to indicate if it's the first day of the simulation.
counter = 0  # A general-purpose counter.


# --- Logging and Reporting ---
real_logs = list()  # A list to store human-readable log entries.
real_logs_csv = list()  # A list to store log entries formatted for CSV output.


# --- Threading and Synchronization ---
day_barrier = threading.Barrier(0)  # A barrier to synchronize all stock threads at the end of each day.
min_num_of_time_stamp_in_stocks_current_day = 9999  # The minimum number of timestamps in the current day's data.


# --- Data and File Paths ---
PATH_RESULTS = '/Users/ofirdahan/Desktop/interactive_brokers/stock_analyzer/local_data_result'  # Path to save results.
PATH_STOCKS_DATA = '/Users/ofirdahan/Desktop/interactive_brokers/stock_data/'  # Path to historical stock data.
stocks_data = {}  # A dictionary to hold the loaded stock data.
data_request = 'LOCAL'  # The source of the data, always 'LOCAL' for the simulator.
class Real_Stock_actions:
    Buy = 0
    Sell = 1
    Return_Available_cash = 2
    Collect_divide_again = 3
