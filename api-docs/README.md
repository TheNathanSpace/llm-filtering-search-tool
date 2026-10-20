# External API docs

Vendored OpenAPI specs. Implementation reference only. Not loaded at runtime.

| File | Upstream | Format |
| --- | --- | --- |
| [`openapi-openrouter.json`](openapi-openrouter.json) | https://openrouter.ai/openapi.json | JSON |

No OpenAPI is vendored for [models.dev](https://models.dev) (`https://models.dev/api.json`) or the Hugging Face Hub model API. See `backend/llm_rankings/models_dev.py` and `backend/llm_rankings/hf_enrichment.py`.

## Refresh

From the repo root:

```bash
./bin/update-external-api-docs.sh
```

> [!WARNING]
> Do not edit these files by hand. Re-run the script after upstream API changes.

## Related

- This project's FastAPI OpenAPI export (for the front-end TypeScript client) is `DATA_DIR/openapi.json`, produced by `bin/generate-openapi-docs.sh`.
- API links: [`backend/README.md`](../backend/README.md).
