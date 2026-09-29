import pandas as pd
import os

# Load the transaction data
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_path, "data", "flash_loan_transactions.csv")

df = pd.read_csv(data_path)

# Path to the analysis folder
analysis_path = os.path.dirname(os.path.abspath(__file__))

# Basic information
print("===== FLASH LOAN RISK ANALYSIS =====")

print("\nTotal Transactions:", len(df))

print("Total Loan Amount:", df["loan_amount"].sum())

print("Average Loan Amount:", df["loan_amount"].mean())

print("\nRisk Level Counts:")
print(df["risk_level"].value_counts())

print("\nAverage Risk Score:", df["risk_score"].mean())

# Average risk score by protocol
print("\nAverage Risk Score by Protocol:")

protocol_risk = df.groupby("protocol")["risk_score"].mean()

print(protocol_risk)

# Average risk score by blockchain
print("\nAverage Risk Score by Blockchain:")

chain_risk = df.groupby("chain")["risk_score"].mean()

print(chain_risk)
# Relationship between loan amount and risk score
print("\nCorrelation between Loan Amount and Risk Score:")

correlation = df["loan_amount"].corr(df["risk_score"])

print(correlation)

# Average risk score by transaction type
print("\nAverage Risk Score by Transaction Type:")

transaction_type_risk = df.groupby("transaction_type")["risk_score"].mean()

print(transaction_type_risk)

# Top 5 highest-risk transactions
print("\nTop 5 Highest-Risk Transactions:")

top_risk = df.sort_values("risk_score", ascending=False)[
    [
        "transaction_id",
        "loan_amount",
        "protocol",
        "chain",
        "transaction_type",
        "risk_score",
        "risk_level"
    ]
].head(5)

print(top_risk)

# Check for missing values
print("\nMissing Values:")

print(df.isnull().sum())

# Check for duplicate transactions
print("\nDuplicate Rows:")

print(df.duplicated().sum())

# risk level distributiom 
import matplotlib.pyplot as plt

# Risk level distribution
risk_counts = df["risk_level"].value_counts()

plt.figure(figsize=(7, 5))

risk_counts.plot(kind="bar")

plt.title("Risk Level Distribution")
plt.xlabel("Risk Level")
plt.ylabel("Number of Transactions")

plt.tight_layout()
plt.savefig(os.path.join(analysis_path, "risk_level_distribution.png"))

# Average risk score by transaction type

transaction_type_risk = df.groupby("transaction_type")["risk_score"].mean()

plt.figure(figsize=(7, 5))

transaction_type_risk.plot(kind="bar")

plt.title("Average Risk Score by Transaction Type")
plt.xlabel("Transaction Type")
plt.ylabel("Average Risk Score")

plt.tight_layout()

plt.savefig(os.path.join(analysis_path, "risk_by_transaction_type.png"))