$body = @{
  customer_id = "cust_123"
  notes = "urgent delivery please"
  items = @(
    @{ sku="latte"; qty=2; price_cents=550 },
    @{ sku="muffin"; qty=1; price_cents=350 }
  )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/orders" -ContentType "application/json" -Body $body
