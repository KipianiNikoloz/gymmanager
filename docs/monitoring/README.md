# Monitoring

- Metrics endpoint: `/metrics` (Prometheus text format).
- Prometheus scrape config example: `docs/monitoring/prometheus.yml` (target `localhost:8000` or your deployed host).
- Suggested dashboard: create a Grafana dashboard with panels for:
  - `http_requests_total` (method/path/status)
  - `http_request_duration_seconds` (histogram/summary)
  - Error rate (status >=500)

Assets:
- Grafana dashboard JSON: `docs/monitoring/grafana-dashboard.json` (import into Grafana; set datasource to Prometheus).
Add screenshots to this folder when available.
