# Wallet Credit Scoring

## Overview

This project provides a transparent, reproducible script to compute credit scores (0–1000) for wallets interacting with the Aave V2 protocol on Polygon, based solely on their historical transaction behaviors.

## Features Engineered

The scoring system uses the following features:

- **Deposit Amount (USD):** Total assets deposited into Aave V2.
- **Borrow/Repay Ratio:** Fraction of borrowed assets that have been repaid.
- **Liquidation Ratio:** Fraction of borrow events ending in liquidation.
- **Transaction Frequency:** Average number of transactions per day.
- **Redeem Ratio:** Fraction of deposits that have been redeemed.
- **Bot/Exploit Detection:** Penalizes wallets with excessive transaction frequency or liquidations.

## Scoring Logic

Scores are calculated using a weighted sum of the features above. Higher scores indicate responsible usage (large deposits, high repay ratio, low liquidation ratio, steady activity). The scoring formula is easy to tune and fully transparent. Wallets with suspicious patterns (very high transaction rate, many liquidations) are penalized.

## How to Use

1. **Place your input JSON file** (e.g. `user-wallet-transactions.json`) in the same directory as the script.
2. **Edit the static filenames** in the script if needed:
    - `input_json`: your input JSON filename
    - `output_csv`: output scores CSV filename
    - `output_plot`: output histogram image filename
3. **Run the script:**
    ```
    python aave_credit_scoring.py
    ```
4. **Outputs:**
    - A CSV file with columns: `wallet,credit_score`
    - A histogram plot of the scores (PNG)

## Validation

- The script saves and displays a histogram of the wallet scores for sanity checking.
- Scores are capped between 0–1000.
- Features and scoring logic are transparent for audit and adjustment.

## Future Improvements

- Add time-weighted features to emphasize recent behavior.
- Use clustering or supervised ML if labeled data becomes available.
- Expand features to cross-protocol or multi-chain scoring.

## Extensibility

- The code is organized using classes for easy feature addition or model substitution.
- All core logic is in `wallet_credit_score.py`.