```mermaid

flowchart LR

&nbsp; Client -->|POST /orders| API\[FastAPI API]

&nbsp; API -->|enqueue job| Redis\[(Redis)]

&nbsp; Worker\[RQ Worker] -->|dequeue| Redis

&nbsp; Worker -->|update status + risk\_score| DB\[(Postgres)]

&nbsp; Client -->|GET /orders/{id}| API



