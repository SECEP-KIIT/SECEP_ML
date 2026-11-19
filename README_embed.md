# Embeddings (Phase C2): Kaggle GPU run

Encoder `sentence-transformers/all-mpnet-base-v2`: frozen, 384-token truncation, L2-normalised, float32, 768 dims.
`input_text` is embedded exactly as given (no re-cleaning). gold_test: only `email_uid` + `input_text` are read, so no labels leave your machine.

## 1. Local: build the upload (from `ML_Training`)
```
python scripts\prepare_embed_inputs.py
```
→ `Data\emb_inputs\` with `pool.csv`, `gold_dev.csv`, `gold_calib.csv`, `gold_test.csv` (columns `uid,input_text`), `embed.py`, `inputs_manifest.json`.
If it prints a **text_version WARNING**, stop and check: the pool and gold text must come from the same `common/text.py` recipe.

## 2. Kaggle: upload the dataset
kaggle.com → **Datasets → New Dataset** → drag in **all 6 files** from `Data\emb_inputs\` → title `secep-emb-inputs` → **Private** → Create.

## 3. Kaggle: run the notebook
1. **Create → New Notebook → File → Import Notebook** → `notebooks\embed_kaggle.ipynb`.
2. Right panel: **Add Input** → *Your Work / Datasets* → `secep-emb-inputs`.
3. **Settings**: Accelerator **GPU T4 x2** (not P100: recent Kaggle PyTorch builds drop it). **Internet On** (needs a phone-verified account) so the encoder can download.
4. **Run All**. Expect ~3–6 min for the 10k pool. Cell 3 prints rows, truncated count and seconds per file.
5. Output panel (right) → `/kaggle/working/emb.zip` → ⋮ → **Download**. (~35 MB)

If you re-run after changing a CSV, upload a **new dataset version**; `embed.py` skips files whose input hash hasn't changed only within the same output folder.

## 4. Local: unpack and verify
Extract `emb.zip` so the files land directly in `Data\emb\` (`Data\emb\pool_emb.npy`, not `Data\emb\emb\…`), then:
```
python -m pip install sentence-transformers
python scripts\check_embeddings.py --parity 20
```
Every file must PASS (same input hash, uid order, shape, unit norm), and **CPU parity** must show min cosine ≥ 0.999:
the live system embeds on CPU, so the GPU training vectors have to match what CPU inference produces. The first run downloads the model (~420 MB) and takes a minute.
Output: `runs\<date>-embed-check\embed_check.json`.

## Log in decision_log.md
- C2 embedded on Kaggle (no local GPU); CPU parity checked on 20 gold-dev emails (result: …).
- Truncated at 384 tokens: pool …%, gold_dev …% (from the `*_emb.json` files).
- Pool uid column is `pool_uid` (I2 says `email_uid`); embedding uid lists use it as-is.
