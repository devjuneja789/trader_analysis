from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "analysis_outputs"
OUT.mkdir(exist_ok=True)

SENTIMENT_ORDER = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]


def pct(series):
    return series.mean() * 100


def load_data():
    trades = pd.read_csv(DATA / "historical_trader_data.csv")
    sentiment = pd.read_csv(DATA / "fear_greed_index.csv")

    trades["datetime_ist"] = pd.to_datetime(
        trades["Timestamp IST"], format="%d-%m-%Y %H:%M", errors="coerce"
    )
    trades["date"] = trades["datetime_ist"].dt.normalize()
    sentiment["date"] = pd.to_datetime(sentiment["date"], errors="coerce")

    merged = trades.merge(
        sentiment[["date", "value", "classification"]],
        on="date",
        how="left",
    )
    merged = merged.rename(
        columns={
            "value": "fear_greed_value",
            "classification": "sentiment",
        }
    )
    merged["net_pnl"] = merged["Closed PnL"] - merged["Fee"]
    merged["is_closed"] = merged["Closed PnL"].ne(0)
    merged["is_win"] = merged["Closed PnL"].gt(0)
    merged["abs_start_position"] = merged["Start Position"].abs()
    merged["position_after_trade"] = merged["Start Position"] + merged["Size Tokens"].where(
        merged["Side"].eq("BUY"), -merged["Size Tokens"]
    )
    merged["reduces_position"] = (
        merged["Start Position"].ne(0)
        & merged["position_after_trade"].abs().lt(merged["abs_start_position"])
    )

    merged["sentiment"] = pd.Categorical(
        merged["sentiment"], categories=SENTIMENT_ORDER, ordered=True
    )
    return merged


def summarize_group(df, group_cols):
    grouped = df.groupby(group_cols, observed=True)
    summary = grouped.agg(
        fills=("Trade ID", "count"),
        accounts=("Account", "nunique"),
        symbols=("Coin", "nunique"),
        notional_usd=("Size USD", "sum"),
        avg_notional_usd=("Size USD", "mean"),
        gross_closed_pnl=("Closed PnL", "sum"),
        total_fees=("Fee", "sum"),
        net_pnl=("net_pnl", "sum"),
        closed_fills=("is_closed", "sum"),
        reducing_position_rate=("reduces_position", pct),
    ).reset_index()
    closed_stats = (
        df[df["is_closed"]]
        .groupby(group_cols, observed=True)
        .agg(
            closed_win_rate=("is_win", lambda s: s.mean() * 100),
            avg_closed_pnl=("Closed PnL", "mean"),
            median_closed_pnl=("Closed PnL", "median"),
        )
        .reset_index()
    )
    summary = summary.merge(closed_stats, on=group_cols, how="left")
    summary["net_pnl_per_1k_notional"] = summary["net_pnl"] / summary["notional_usd"] * 1000
    return summary


def write_bar_svg(labels, values, title, ylabel, path, colors=None):
    colors = colors or ["#4c78a8"] * len(labels)
    width, height = 920, 520
    left, right, top, bottom = 90, 30, 60, 110
    plot_w, plot_h = width - left - right, height - top - bottom
    max_v = max(values + [0])
    min_v = min(values + [0])
    span = max(max_v - min_v, 1)

    def y(v):
        return top + (max_v - v) / span * plot_h

    zero_y = y(0)
    bar_w = plot_w / len(labels) * 0.62
    gap = plot_w / len(labels)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">{title}</text>',
        f'<text x="20" y="{height/2}" transform="rotate(-90 20 {height/2})" text-anchor="middle" font-family="Arial" font-size="14">{ylabel}</text>',
        f'<line x1="{left}" y1="{zero_y:.1f}" x2="{width-right}" y2="{zero_y:.1f}" stroke="#222" stroke-width="1"/>',
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        x = left + i * gap + (gap - bar_w) / 2
        bar_y = min(y(value), zero_y)
        bar_h = abs(zero_y - y(value))
        parts.append(f'<rect x="{x:.1f}" y="{bar_y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{colors[i]}"/>')
        parts.append(f'<text x="{x + bar_w/2:.1f}" y="{bar_y - 8 if value >= 0 else bar_y + bar_h + 18:.1f}" text-anchor="middle" font-family="Arial" font-size="12">{value:,.0f}</text>')
        parts.append(f'<text x="{x + bar_w/2:.1f}" y="{height-58}" transform="rotate(-25 {x + bar_w/2:.1f} {height-58})" text-anchor="end" font-family="Arial" font-size="13">{label}</text>')
    for t in range(5):
        value = min_v + span * t / 4
        yy = y(value)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" stroke="#e9ecef" stroke-width="1"/>')
        parts.append(f'<text x="{left-8}" y="{yy+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{value:,.0f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_line_svg(series_df, title, ylabel, path):
    width, height = 1040, 560
    left, right, top, bottom = 90, 170, 60, 70
    plot_w, plot_h = width - left - right, height - top - bottom
    colors = ["#b94a48", "#d9822b", "#6c757d", "#2f9e44", "#087f5b"]
    values = series_df.to_numpy().ravel()
    max_v, min_v = max(values.max(), 0), min(values.min(), 0)
    span = max(max_v - min_v, 1)

    def x(i):
        return left + i / max(len(series_df) - 1, 1) * plot_w

    def y(v):
        return top + (max_v - v) / span * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">{title}</text>',
        f'<text x="20" y="{height/2}" transform="rotate(-90 20 {height/2})" text-anchor="middle" font-family="Arial" font-size="14">{ylabel}</text>',
        f'<line x1="{left}" y1="{y(0):.1f}" x2="{width-right}" y2="{y(0):.1f}" stroke="#222" stroke-width="1"/>',
    ]
    for idx, col in enumerate(series_df.columns):
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(series_df[col].values))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{colors[idx]}" stroke-width="2.2"/>')
        parts.append(f'<rect x="{width-right+25}" y="{top+idx*26}" width="14" height="14" fill="{colors[idx]}"/>')
        parts.append(f'<text x="{width-right+45}" y="{top+12+idx*26}" font-family="Arial" font-size="13">{col}</text>')
    for t in range(5):
        value = min_v + span * t / 4
        yy = y(value)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" stroke="#e9ecef" stroke-width="1"/>')
        parts.append(f'<text x="{left-8}" y="{yy+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{value:,.0f}</text>')
    parts.append(f'<text x="{left}" y="{height-25}" font-family="Arial" font-size="12">{series_df.index.min().date()}</text>')
    parts.append(f'<text x="{width-right}" y="{height-25}" text-anchor="end" font-family="Arial" font-size="12">{series_df.index.max().date()}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main():
    merged = load_data()
    merged.to_csv(OUT / "merged_trader_sentiment.csv", index=False)

    sentiment_summary = summarize_group(merged, ["sentiment"])
    sentiment_summary.to_csv(OUT / "sentiment_summary.csv", index=False)

    daily = summarize_group(merged, ["date", "sentiment"])
    daily.to_csv(OUT / "daily_summary.csv", index=False)

    account_sentiment = summarize_group(merged, ["Account", "sentiment"])
    account_sentiment.to_csv(OUT / "account_sentiment_summary.csv", index=False)

    symbol_sentiment = summarize_group(merged, ["Coin", "sentiment"])
    symbol_sentiment.to_csv(OUT / "symbol_sentiment_summary.csv", index=False)

    side_sentiment = summarize_group(merged, ["Side", "sentiment"])
    side_sentiment.to_csv(OUT / "side_sentiment_summary.csv", index=False)

    closed = merged[merged["is_closed"]].copy()
    account_best = (
        closed.groupby(["Account", "sentiment"], observed=True)
        .agg(closed_fills=("Trade ID", "count"), net_pnl=("net_pnl", "sum"), closed_win_rate=("is_win", pct))
        .query("closed_fills >= 50")
        .sort_values("net_pnl", ascending=False)
        .head(20)
        .reset_index()
    )
    account_best.to_csv(OUT / "top_account_sentiment_edges.csv", index=False)

    plot_df = sentiment_summary.set_index("sentiment").reindex(SENTIMENT_ORDER)
    sentiment_colors = ["#b94a48", "#d9822b", "#6c757d", "#2f9e44", "#087f5b"]
    write_bar_svg(
        [str(x) for x in plot_df.index],
        plot_df["net_pnl"].fillna(0).tolist(),
        "Net PnL by Bitcoin Market Sentiment",
        "Net PnL (USD)",
        OUT / "net_pnl_by_sentiment.svg",
        sentiment_colors,
    )
    write_bar_svg(
        [str(x) for x in plot_df.index],
        plot_df["closed_win_rate"].fillna(0).tolist(),
        "Closed-Fill Win Rate by Sentiment",
        "Win Rate (%)",
        OUT / "win_rate_by_sentiment.svg",
        sentiment_colors,
    )

    daily_pnl = (
        merged.groupby(["date", "sentiment"], observed=True)["net_pnl"]
        .sum()
        .unstack("sentiment")
        .reindex(columns=SENTIMENT_ORDER)
        .fillna(0)
        .cumsum()
    )
    write_line_svg(
        daily_pnl,
        "Cumulative Net PnL Contribution by Sentiment",
        "Cumulative Net PnL (USD)",
        OUT / "cumulative_pnl_by_sentiment.svg",
    )

    print("rows", len(merged))
    print("date_range", merged["date"].min().date(), merged["date"].max().date())
    print(sentiment_summary.to_string(index=False))
    print("\\nTop account/sentiment edges")
    print(account_best.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
