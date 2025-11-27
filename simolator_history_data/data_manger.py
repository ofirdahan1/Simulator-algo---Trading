"""
Historical Data Manager for Backtesting.

This script is a utility for downloading historical intraday stock data from
the Alpha Vantage API. The downloaded data is saved as text files and is used
by the backtesting engine to simulate trading strategies.
"""

import requests
import csv
import os

# --- Configuration: File Path ---
# The root directory where historical stock data will be stored.
# It is recommended to use a relative path for portability.
PATH_STOCKS_DATA = 'stock_data/'


# --- Configuration: Data to Download ---
# Define the list of stock symbols to download data for.
stocks_check = ['AAPL','AMD','TQQQ','VOO','DIS','ITB','TSLA','LLY','MSTR']
stocks_check += ['TSM','NFLX','GOOG','NVDA','AMZN','AVGO','NVO','MA','PG','MRK','HD','AMT','SOXL','MCD']
stocks_check += ['META','MAGS','MSFT','TQQQ']
stocks_check = ['AAPL','QQQ','AMD','DIS','ITB','LLY']

stocks_check = ['AAPL']

# Define the time periods (year-month) for which to download data.
dates = ["2023-01","2023-02","2023-03","2023-04","2023-05","2023-06","2023-07","2023-08","2023-09","2023-10","2023-11","2023-12"]
dates += ["2024-01","2024-02","2024-03","2024-04","2024-05","2024-06","2024-07","2024-08","2024-09","2024-10"]
dates = ["2024-01","2024-02","2024-03","2024-04","2024-05","2024-06","2024-07","2024-08","2024-09","2024-10","2024-11"]
dates = ["2024-11"]


def create_data_file(stocks_list, dates):
    """
    Downloads historical intraday data from Alpha Vantage for a given list of
    stocks and dates.

    Args:
        stocks_list (list): A list of stock symbols.
        dates (list): A list of year-month strings (e.g., "2023-01").
    
    Returns:
        tuple: A status message and the number of API calls made.
    """
    # --- Configuration: API Key ---
    # IMPORTANT: Replace "YOUR_API_KEY" with your actual Alpha Vantage API key.
    # Get a free key from: https://www.alphavantage.co/support/#api-key
    ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY"
    key = ALPHA_VANTAGE_API_KEY
    
    txt = ''
    counter = 0
    for stock in stocks_list:
        for year_month in dates:
            file_name = f"{stock}_{year_month.replace('-', '_')}.txt"
            if os.path.exists(PATH_STOCKS_DATA + f"{stock}/" + file_name):
                continue
            try:
                url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&interval=1min&month={year_month}&extended_hours=true&outputsize=full&apikey={key}&datatype=csv"
                r = requests.get(url)
                txt = r.text
                if "Our standard API rate limit is 25 requests per day." in txt:
                    return f"Exceeded the 25 request limit at stock: {stock}, date: {year_month}\n" + txt, counter
                if "Invalid API call" in txt:
                    print(f"Invalid API call for {stock} on {year_month}. Check symbol or API key.")
                    continue
            except requests.exceptions.RequestException as e:
                print(f"Could not pull data from web for {stock}: {e}")
                continue
                
            if not os.path.exists(PATH_STOCKS_DATA):
                os.mkdir(PATH_STOCKS_DATA)
            if not os.path.exists(PATH_STOCKS_DATA + f"{stock}"):
                os.mkdir(PATH_STOCKS_DATA + f"{stock}")
                
            with open(PATH_STOCKS_DATA + f"{stock}/" + file_name, 'w+') as output:
                output.write(txt)
            counter += 1
            print(f"Successfully downloaded data for {stock} for {year_month}")
            
    return "success!", counter

def convert_csv_to_txt_file(dir_path):
    """
    Converts all .csv files in a directory to .txt files and deletes the originals.
    
    Args:
        dir_path (str): The path to the directory to process.
    """
    import glob
    csv_file_paths = glob.glob(dir_path + "*/*.csv")
    for csv_file_path in csv_file_paths:
        with open(csv_file_path, 'r') as f_input:
            txt = f_input.read()
            txt_path = csv_file_path.replace('csv', 'txt')
            with open(txt_path, 'w+') as f_output:
                f_output.write(txt)
        os.remove(csv_file_path)

if __name__ == "__main__":
    # This part of the script will run when executed directly.
    # It first converts any existing CSV files to TXT format.
    convert_csv_to_txt_file(PATH_STOCKS_DATA)
    
    # Then, it proceeds to download the historical data.
    status, used = create_data_file(stocks_check, dates)
    print(f"\nAPI pulls used: {used}")
    print(f"Download status: {status}")
