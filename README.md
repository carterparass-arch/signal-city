# Signal City

A daily map of market signals: AI and chips, biotech, energy, rates and macro, defense and space, crypto, consumer, private markets and metals, plus a **Moonshots** list of small-cap ideas with their risks spelled out.

Each tower is a sector. Open one to see ideas, outcomes, dated catalysts and news, each with a source link and the listed companies it touches. The **Stocks** tab has a snapshot of valuation data for every company in the city.

**Research leads, not financial advice.** The data is gathered by an automated research routine and can lag or contain errors. Check the linked source before acting on anything.

## How it updates

- `index.html` is the whole site (no build step).
- `data/city.json` holds the published signals, stock snapshots and market tape. It is regenerated on each refresh.
- `tools/build_data.py` builds `data/city.json` from the research database export and filters out private material before anything is written.
- Charts are embedded from TradingView.
