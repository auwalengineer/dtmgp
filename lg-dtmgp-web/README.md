# LG-DTMGP Web

Vue 3 application shell for the Benue State Local Government Digital Transformation, Management and Governance Platform.

## Commands

```bash
npm install
npm run dev
npm run typecheck
npm test
npm run build
npm run build:staging
```

## Environments

| Mode | File | API behavior | Runtime configuration |
| --- | --- | --- | --- |
| Development | `.env.development` | Vite proxies `/api` and `/assets` to `http://blga.local:8000` | Build-time values |
| Staging | `.env.staging` | Same-origin | Fetches `/runtime-config.json` without caching |
| Production | `.env.production` | Same-origin | Fetches `/runtime-config.json` without caching |

Deployments may replace `runtime-config.json` without rebuilding hashed application assets. It must not contain secrets and should be served with `Cache-Control: no-cache`.
