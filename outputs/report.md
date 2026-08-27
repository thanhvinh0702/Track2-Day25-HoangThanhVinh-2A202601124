# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Inference unit cost:** $6.488 → $1.126 / 1M-token

**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1
- Cache economics: 1.32 estimated reads; cache enabled: True
- Reasoning traffic: 8.4% of requests; $1.40 optimized cost (16.5% of optimized inference)
- Reasoning energy multiplier: 15.8x vs non-reasoning traffic
- 10% reasoning cap estimate: save $0.00/day and 0.0 Wh/day

## Recommended actions

1. Ưu tiên cascade + prompt caching + batch vì đây là đòn bẩy inference lớn nhất theo $/1M-token.
2. Tắt GPU idle và right-size các GPU có GPU-Util cao nhưng MFU thấp; GPU-Util chỉ phản ánh thời gian bận.
3. Dùng spot cho workload interruptible có checkpoint và reserved cho duty cycle cao; theo dõi tag coverage trước chargeback.
4. Giới hạn reasoning ở 10% traffic khi chất lượng cho phép; chuyển job gián đoạn sang vùng có carbon thấp.

_Figures are June-2026 as-of snapshots; re-baseline before acting._