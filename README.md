# Algorithmic Trading Project

## Overview

This project contains a comprehensive algorithmic trading system written in Python. It is divided into two main components: a live/paper trading bot and a backtesting simulator. The system is designed to trade stocks using a momentum-based strategy, with capabilities for both real-world execution and historical performance analysis.

This project was developed over several months in 2024 as a personal endeavor to explore algorithmic trading. While the strategies implemented here have not been proven to be consistently profitable, the codebase serves as a practical example of a trading bot architecture. The core logic was manually coded, with AI assistance used solely for generating documentation in the end of 2025 to improve readability for other developers.

## Project Components

This repository is organized into two primary directories:

### 1. `algo_trading`

This directory contains the core application for live and paper trading. It connects to the Interactive Brokers (IBKR) platform to execute trades in real-time based on the implemented trading strategy.

For a detailed explanation of its architecture, setup, and usage, please refer to the [`algo_trading/README.md`](./algo_trading/README.md) file.

### 2. `simolator_history_data`

This directory houses the backtesting engine. It allows you to test the trading algorithm against historical market data to evaluate its performance before deploying it in a live environment. This folder also contains the historical data and the results from simulation runs.

For a detailed breakdown of the backtesting simulator, please see the [`simolator_history_data/README.md`](./simolator_history_data/README.md) file.
