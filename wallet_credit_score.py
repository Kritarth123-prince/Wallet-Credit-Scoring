import json
import pandas as pd
from collections import defaultdict
from typing import Dict, Any
import matplotlib.pyplot as plt

class WalletFeatures:
    def __init__(self, wallet: str):
        self.wallet = wallet
        self.deposit_count = 0
        self.borrow_count = 0
        self.repay_count = 0
        self.redeem_count = 0
        self.liquidation_count = 0
        self.deposit_usd = 0.0
        self.borrow_usd = 0.0
        self.repay_usd = 0.0
        self.liquidation_usd = 0.0
        self.tx_count = 0
        self.first_ts = None
        self.last_ts = None

    def update(self, tx: Dict[str, Any]):
        action = str(tx.get('action', '')).lower()
        ts = tx.get('timestamp')
        ad = tx.get('actionData', {})
        amt = float(ad.get('amount', '0'))
        price = float(ad.get('assetPriceUSD', '1'))
        asset = ad.get('assetSymbol', '').upper()
        decimals = 6 if asset in ['USDC', 'USDT', 'DAI'] else 18 if len(str(amt)) > 10 else 1
        usd = amt * price / (10 ** decimals if decimals > 1 else 1)
        self.tx_count += 1
        self.first_ts = min(self.first_ts, ts) if self.first_ts else ts
        self.last_ts = max(self.last_ts, ts) if self.last_ts else ts

        if action == 'deposit':
            self.deposit_count += 1
            self.deposit_usd += usd
        elif action == 'borrow':
            self.borrow_count += 1
            self.borrow_usd += usd
        elif action == 'repay':
            self.repay_count += 1
            self.repay_usd += usd
        elif action == 'redeemunderlying':
            self.redeem_count += 1
        elif action == 'liquidationcall':
            self.liquidation_count += 1
            self.liquidation_usd += usd

    def get_features(self) -> Dict[str, Any]:
        borrow_repaid_ratio = self.repay_usd / (self.borrow_usd + 1e-6)
        liquidation_borrow_ratio = self.liquidation_count / (self.borrow_count + 1e-6)
        active_days = (self.last_ts - self.first_ts) / 86400 if self.first_ts and self.last_ts else 0
        tx_per_day = self.tx_count / (active_days + 1) if active_days else self.tx_count
        redeem_ratio = self.redeem_count / (self.deposit_count + 1e-6)
        return {
            'deposit_usd': self.deposit_usd,
            'borrow_repaid_ratio': borrow_repaid_ratio,
            'liquidation_borrow_ratio': liquidation_borrow_ratio,
            'tx_per_day': tx_per_day,
            'redeem_ratio': redeem_ratio,
            'liquidation_count': self.liquidation_count
        }

class CreditScorer:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.wallets: Dict[str, WalletFeatures] = {}

    def load_data(self):
        with open(self.json_path, 'r') as f:
            text = f.read()
        last_bracket = text.rfind(']')
        if last_bracket != -1:
            fixed_text = text[:last_bracket + 1]
            self.data = json.loads(fixed_text)
            print(f"Loaded {len(self.data)} transactions after patching.")
        else:
            raise ValueError("No valid closing bracket found in JSON file.")

    def process_transactions(self):
        for tx in self.data:
            w = tx.get('userWallet')
            if not w:
                continue
            if w not in self.wallets:
                self.wallets[w] = WalletFeatures(w)
            self.wallets[w].update(tx)

    def score_wallet(self, features: Dict[str, Any]) -> int:
        score = (
            0.35 * min(features['deposit_usd'] / 10000, 1) * 1000 +
            0.20 * min(features['borrow_repaid_ratio'], 1) * 1000 +
            0.15 * (1 - min(features['liquidation_borrow_ratio'], 1)) * 1000 +
            0.10 * min(features['tx_per_day'] / 10, 1) * 1000 +
            0.20 * min(features['redeem_ratio'], 1) * 1000
        )
        if features['tx_per_day'] > 50 or features['liquidation_count'] > 5:
            score *= 0.7
        score = max(0, min(int(score), 1000))
        return score

    def generate_scores(self) -> pd.DataFrame:
        results = []
        for w, wf in self.wallets.items():
            feats = wf.get_features()
            score = self.score_wallet(feats)
            results.append({'wallet': w, 'credit_score': score})
        df = pd.DataFrame(results)
        return df

    def save_scores(self, out_path: str, df: pd.DataFrame):
        df.to_csv(out_path, index=False)
        print(f"Saved scores to {out_path}")

    def plot_scores(self, df: pd.DataFrame, plot_path: str):
        plt.figure(figsize=(8,5))
        plt.hist(df['credit_score'], bins=20, color="skyblue", edgecolor="black")
        plt.xlabel('Credit Score')
        plt.ylabel('Number of Wallets')
        plt.title('Wallet Credit Score Distribution')
        plt.tight_layout()
        plt.savefig(plot_path)
        print(f"Saved plot to {plot_path}")

if __name__ == "__main__":
    input_json = "user-wallet-transactions.json"
    output_csv = "aave_wallet_scores.csv"
    output_plot = "wallet_score_histogram.png"

    scorer = CreditScorer(input_json)
    scorer.load_data()
    scorer.process_transactions()
    df = scorer.generate_scores()
    scorer.save_scores(output_csv, df)
    scorer.plot_scores(df, output_plot)