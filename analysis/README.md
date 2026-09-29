# Flash Loan Risk Analysis

## Overview

This folder contains the Data Science analysis developed for the De-Flash project.

The analysis examines flash loan transaction data and identifies patterns related to transaction risk using Python and Pandas.

## Dataset

The analysis uses a sample dataset containing flash loan transaction information.

The dataset includes:

- Loan amount
- Protocol
- Blockchain
- Transaction type
- Gas price
- Token volatility
- Transaction frequency
- Risk score
- Risk level

> **Note:** The current dataset is synthetic sample data created for development and analysis purposes. It does not represent real blockchain transaction records.

## Analysis Performed

The analysis includes:

1. Total number of transactions
2. Total and average loan amount
3. Risk level distribution
4. Average risk score
5. Average risk score by protocol
6. Average risk score by blockchain
7. Average risk score by transaction type
8. Correlation between loan amount and risk score
9. Identification of the top 5 highest-risk transactions
10. Missing-value analysis
11. Duplicate transaction analysis

## Visualizations

### Risk Level Distribution

![Risk Level Distribution](risk_level_distribution.png)

This visualization shows the distribution of transactions across LOW, MEDIUM, and HIGH risk levels.

### Risk by Transaction Type

![Risk by Transaction Type](risk_by_transaction_type.png)

This visualization compares the average risk score across different transaction types.

## Key Findings

Based on the current synthetic dataset:

- The dataset contains 20 transactions.
- The total loan amount is 7,575,000.
- The average loan amount is 378,750.
- The average risk score is 47.25.
- There are 7 LOW-risk, 6 MEDIUM-risk, and 7 HIGH-risk transactions.
- Liquidation transactions have the highest average risk score in this sample.
- The correlation between loan amount and risk score is approximately 0.968.
- No missing values were found.
- No duplicate rows were found.

## Tools Used

- Python
- Pandas
- Matplotlib

## Files

```text
analysis/
├── README.md
├── risk_analysis.py
├── risk_level_distribution.png
└── risk_by_transaction_type.png