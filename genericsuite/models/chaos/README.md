# Chaos Experiments

This module provides chaos engineering capabilities for the GenericSuite backend framework. Chaos engineering is the practice of intentionally introducing failures into a system to test its resilience and identify weaknesses.

## Available Experiments

### 1. Latency Injection
Introduces artificial delays to response times to test how your application handles slow dependencies.

**Parameters:**
- `delay_seconds` (float): Amount of delay to introduce (default: 2.0)
- `duration_seconds` (float): How long to run the experiment (default: 30.0)

### 2. Error Injection
Randomly injects errors into responses based on a configurable error rate.

**Parameters:**
- `error_rate` (float): Percentage of requests that should fail (0.0-1.0, default: 0.1)
- `duration_seconds` (float): How long to run the experiment (default: 30.0)

### 3. Resource Exhaustion
Consumes system resources (memory) to test application behavior under resource constraints.

**Parameters:**
- `memory_mb` (int): Amount of memory to consume in MB (default: 100)
- `duration_seconds` (float): How long to run the experiment (default: 30.0)

## API Endpoints

All endpoints are available under the `/chaos_experiments` prefix.

### List Available Experiments
```http
GET /chaos_experiments/list
```

Returns a list of available experiments and currently active ones.

### Start an Experiment
```http
POST /chaos_experiments/start
Content-Type: application/json

{
    "experiment_name": "latency_injection",
    "delay_seconds": 3.0,
    "duration_seconds": 60.0
}
```

### Stop an Experiment
```http
POST /chaos_experiments/stop
Content-Type: application/json

{
    "experiment_name": "latency_injection"
}
```

### Get Experiment Status
```http
GET /chaos_experiments/status?experiment_name=latency_injection
```

### Test Endpoint
```http
GET /chaos_experiments/test
```

This endpoint applies any active chaos experiments and can be used to test the effects.

## Example Usage

### Starting a Latency Injection Experiment

```bash
curl -X POST http://localhost:8000/chaos_experiments/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "experiment_name": "latency_injection",
    "delay_seconds": 2.0,
    "duration_seconds": 30.0
  }'
```

### Testing the Effect

```bash
# This request will be delayed by 2 seconds if the latency experiment is active
curl http://localhost:8000/chaos_experiments/test
```

### Stopping the Experiment

```bash
curl -X POST http://localhost:8000/chaos_experiments/stop \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "experiment_name": "latency_injection"
  }'
```

## Safety Considerations

1. **Use in Non-Production**: Only run chaos experiments in development, testing, or staging environments.

2. **Start Small**: Begin with low impact experiments (short durations, low error rates).

3. **Monitor Effects**: Always monitor your application's behavior during experiments.

4. **Have Rollback Plans**: Know how to quickly stop experiments if needed.

5. **Resource Limits**: Be careful with resource exhaustion experiments to avoid system crashes.

## Framework Support

This chaos engineering module is fully supported across all GenericSuite frameworks:

- **Chalice**: AWS Lambda-based applications
- **Flask**: Traditional web applications
- **FastAPI**: Modern async API applications

The API and functionality remain consistent across all frameworks.