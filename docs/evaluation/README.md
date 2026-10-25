# M9 — Public order data evaluation (Olist)

**Status:** A reproducible local evaluator and synthetic-only CI. **No live Olist dataset measurements have been performed or published by this repository.**

## Original public dataset and permitted use

The [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), provided by Olist, comprises roughly 100,000 historical marketplace orders from 2016–2018. The orders file is `olist_orders_dataset.csv`. Source attribution: *Olist and Sionek (2018), Brazilian E-Commerce Public Dataset by Olist, Kaggle.*

**License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0).** This means the dataset is **not automatically cleared for commercial or employer use**. Before using it for company projects, external presentations, customer work or formal KRA deployment, obtain legal/employer approval or choose an appropriately licensed dataset. Follow the dataset license, source citation and any applicable data terms. The toolkit **does not redistribute, upload, cache in GitHub Actions, or download Olist records**. Obtain the original file separately in a permitted environment if your intended use allows it.

Other order-status CSV files with the same schema can be evaluated, subject to their own terms.

## One-command local evaluation (Windows PowerShell / PyCharm)

Install the three AET packages as described in [the M7 demo](../demo/README.md):

```powershell
python -m pip install -e ".[demo]"
python -m pip install -e "./packages/agent-quality-kit"
python -m pip install -e "./packages/agent-provider-contract"
```

Once you have permission for the dataset, download it from the official Kaggle page and extract `olist_orders_dataset.csv` into a **local non-versioned** directory. From the private AET repository root:

```powershell
python scripts/evaluate_olist.py --input "C:\Data\olist_orders_dataset.csv" --sample 300 --queries 100 --seed 19 --json-out "C:\Data\olist-eval-aggregate.json"
```

The script uses a seeded reservoir sample over **all** order records, discards customer IDs and other columns, generates a fresh temporary mock agent, temporarily configures its deterministic routing to accept Olist's 32-hex-character order IDs, then sends in-process POST /invoke requests through FastAPI + LangGraph. Tool events are asserted using the standalone Agent Quality Kit.

It verifies exact stored status lookup, one tool call per valid request, case-insensitive order IDs, an unknown valid order, and malformed input falling back without invoking the tool. The script measures per-request local TestClient latency (median, p95, max). It **does not use a real language model or a remote service**. Raw Olist IDs remain inside temporary local files that are automatically deleted; no identifier, customer ID, contact, location or raw dataset row is written to the aggregate report.

## CI test without any external data

This repository contains only `tests/fixtures/olist_orders_synthetic.csv`: eight **fabricated** rows exercising each known Olist status category. To reproduce our CI evaluation:

```powershell
python scripts/evaluate_olist.py --input tests/fixtures/olist_orders_synthetic.csv --sample 8 --queries 8 --seed 19 --dataset-kind synthetic
```

The output records `dataset_kind: synthetic` and must **never** be described as a measured result on the original Olist dataset. CI never downloads or copies any external data.

## Evidence interpretation and limitations

- **Correctness:** Exact-match status accuracy, including unknown-order and malformed-input handling, not fuzzy semantic retrieval.
- **Latency:** In-process FastAPI TestClient + LangGraph + local dictionary lookup. Excludes network, database, concurrency, deployment, model inference and data download time.
- **Sampling:** Seeded reservoir of bounded size. Historical Olist data is highly imbalanced (many delivered orders); small samples may omit rare statuses. The fabricated CI fixture is purposely balanced and is not representative of the real dataset.
- **Security:** This exercise intentionally patches only the *temporary generated test project*. It does not alter or ship the synthetic production reference tool.
- **Human impact:** No claim about saved development hours, cross-team adoption, semantic LLM quality or provider-cloud parity can be inferred.

For actual promotion evidence, retain only properly licensed aggregate summaries and distinguish dataset evaluations from the M8 controlled human pilot. When reporting external-data statistics, record the exact downloaded source/version, timestamp, sampling configuration and the source's licensing clearance.
