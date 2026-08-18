# Banking77 demo episode

End-to-end walkthrough on public data (what the paper measured; you should
see FREEZE recommended against Qwen3-8B, because Banking77 is a
low-coupling task whose reference barely moves across generations).

```bash
python prepare_data.py
upgrade-advisor measure episode.yaml --target Qwen/Qwen3-8B
upgrade-advisor recommend episode.yaml --target Qwen/Qwen3-8B --reference-estimate 0.9321
```
