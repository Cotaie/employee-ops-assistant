from pydantic import BaseModel


class MetricsResponse(BaseModel):
  total_requests: int
  total_errors: int
  error_rate: str
  avg_latency_ms: str
  cache_hit_rate: str
  total_input_tokens: int
  total_output_tokens: int

