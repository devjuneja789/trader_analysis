# Trader Performance vs Bitcoin Market Sentiment

## Dataset Scope

- Trader fills: 211,224 Hyperliquid records from 2023-05-01 to 2025-05-01.
- Sentiment records: daily Bitcoin Fear & Greed classifications from 2018-02-01 to 2025-05-02.
- Joined key: calendar date derived from `Timestamp IST`.
- Coverage note: 6 trader rows did not match a sentiment day; all other records were matched.
- PnL metric: `net_pnl = Closed PnL - Fee`.
- Win rate metric: calculated only on fills where `Closed PnL != 0`.

## Key Results by Sentiment

| Sentiment | Fills | Notional USD | Net PnL | Closed fills | Closed win rate | Avg closed PnL | Net PnL per $1k notional |
|---|---:|---:|---:|---:|---:|---:|---:|
| Extreme Fear | 21,400 | 114,484,261 | 715,222 | 10,406 | 76.22% | 71.03 | 6.25 |
| Fear | 61,837 | 483,324,790 | 3,264,698 | 29,808 | 87.29% | 112.63 | 6.75 |
| Neutral | 37,686 | 180,242,063 | 1,253,546 | 18,159 | 82.39% | 71.20 | 6.95 |
| Greed | 50,303 | 288,582,495 | 2,087,031 | 25,176 | 76.89% | 85.40 | 7.23 |
| Extreme Greed | 39,992 | 124,465,165 | 2,688,141 | 20,853 | 89.17% | 130.21 | 21.60 |

## Main Insights

1. Extreme Greed was the highest-efficiency regime.
   Although Extreme Greed had much lower notional than Fear and Greed, it produced the best PnL density: $21.60 per $1,000 traded, roughly 3x the other sentiment buckets.

2. Fear had the largest absolute PnL, but not the best efficiency.
   Fear generated the highest total net PnL at about $3.26M, but it also had the largest notional exposure at about $483.3M. Its efficiency was solid, not exceptional.

3. Sell-side trades dominated in Greed and Extreme Greed.
   In Extreme Greed, sell fills produced about $2.51M net PnL versus about $175K for buy fills. Sell-side PnL efficiency reached $39.18 per $1,000 notional in Extreme Greed, suggesting that fading overheated markets was especially profitable in this dataset.

4. Buy-side performance was stronger in Fear than in Greed.
   Buy fills in Fear produced about $1.89M net PnL and $7.66 per $1,000 notional. In Extreme Greed, buy-side efficiency fell to $2.91 per $1,000 notional.

5. Daily sentiment score had weak direct correlation with daily PnL.
   Daily net PnL correlation with the numeric Fear & Greed value was -0.079. Sentiment classification appears more useful as a regime filter than as a linear daily predictor.

6. Performance was concentrated in specific accounts and symbols.
   The best account-sentiment pockets were not evenly distributed. For example, one account generated about $1.10M net PnL in Extreme Greed with a 93.84% closed-fill win rate, while another generated about $1.11M in Fear with an 89.06% closed-fill win rate.

## Symbol Observations

Top symbols by total net PnL among symbols with at least 500 fills:

| Symbol | Fills | Net PnL | Notional USD |
|---|---:|---:|---:|
| @107 | 29,992 | 2,777,960 | 55,760,860 |
| HYPE | 68,005 | 1,923,123 | 141,990,200 |
| SOL | 10,691 | 1,611,600 | 125,074,800 |
| ETH | 11,158 | 1,296,888 | 118,281,000 |
| BTC | 26,064 | 728,821 | 644,232,100 |

BTC had the largest notional exposure but much lower PnL efficiency than several alt symbols. This suggests strategy design should not assume the most liquid symbol is the highest-return opportunity.

## Strategy Implications

- Use sentiment as a regime filter, not a standalone signal.
- In Extreme Greed, prioritize short/fade setups or tighter validation for long entries.
- In Fear, long entries appear more attractive than in Greed/Extreme Greed, especially when paired with account or symbol filters.
- Allocate more capital to account-symbol-sentiment combinations with repeated edge, rather than applying one rule across all traders and coins.
- Monitor PnL per notional alongside total PnL; total PnL alone over-rewards high-volume regimes.
- Include fees in evaluation, especially for high-frequency accounts, because fee drag reduced total gross PnL by about $245.8K across the dataset.

## Generated Files

- `analysis_outputs/merged_trader_sentiment.csv`: row-level joined dataset.
- `analysis_outputs/sentiment_summary.csv`: core regime-level performance table.
- `analysis_outputs/account_sentiment_summary.csv`: account by sentiment performance.
- `analysis_outputs/symbol_sentiment_summary.csv`: symbol by sentiment performance.
- `analysis_outputs/side_sentiment_summary.csv`: buy/sell by sentiment performance.
- `analysis_outputs/top_account_sentiment_edges.csv`: strongest account-sentiment combinations with at least 50 closed fills.
- `analysis_outputs/net_pnl_by_sentiment.svg`: net PnL chart.
- `analysis_outputs/win_rate_by_sentiment.svg`: closed-fill win rate chart.
- `analysis_outputs/cumulative_pnl_by_sentiment.svg`: cumulative PnL contribution chart.
