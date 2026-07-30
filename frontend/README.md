# Front-end Docs

- <https://nextjs.org/docs/app/getting-started>
- <https://mui.com/toolpad/core/introduction/>
- <https://mui.com/material-ui/all-components/>
- <https://mui.com/x/react-data-grid/>

Always-visible filter fields (e.g. Min Price / Max Price) would improve usability over multi-click column filters alone.

## Installation

From the repo root:

```bash
./bin/setup-frontend.sh
./bin/start-frontend-live.sh
```

`npm run dev` (from `frontend/`) also works; the app listens on port **3030**.

Open [http://localhost:3030](http://localhost:3030). The UI talks to the back-end URL from
`NEXT_PUBLIC_BACKEND_URL` in the repo-root [`.env`](../.env.template) (default `http://localhost:8000`). For a full
local stack, see the root [README](../README.md).

### API Client

1. The back-end OpenAPI docs are generated via FastAPI's built-in tools.
2. The front-end API client is generated via @hey-api/openapi-ts.
3. The front-end API client is imported into the front-end app, and the endpoints and models/types are able to be used.

This process can be completed by running the `../bin/install-frontend-api-client.sh` script.
