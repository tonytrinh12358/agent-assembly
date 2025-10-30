# GenAI Observability Implementation Guide

## Overview

This guide explains the GenAI observability implementation for the AgentCore deployed agents in this directory. All agents are instrumented with AWS OpenTelemetry for comprehensive monitoring through Amazon CloudWatch.

## 🚀 Implementation Status

### ✅ Fully Implemented Features

All three agents (`crewai_agent`, `langgraph_agent`, `orchestrator_agent`) include:

1. **AgentCore Runtime Integration**
   - Using `BedrockAgentCoreApp()` for runtime management
   - Proper `@app.entrypoint` decorators for entry points
   - Standardized payload handling and error management

2. **OpenTelemetry Instrumentation**
   - `aws-opentelemetry-distro>=0.10.1` installed in all containers
   - `opentelemetry-instrument` command in all Dockerfiles
   - Automatic trace and metric collection

3. **CloudWatch Integration**
   - Automatic metrics export to CloudWatch
   - Distributed tracing with AWS X-Ray
   - Custom span attributes for agent-specific data

## 🔧 Technical Implementation

### Agent Structure

Each agent follows the observability pattern:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def agent_function(payload):
    """Agent entrypoint with automatic instrumentation"""
    # Agent logic here
    return response

if __name__ == "__main__":
    app.run()
```

### Docker Configuration

All Dockerfiles include:

```dockerfile
# Install OpenTelemetry
RUN uv pip install aws-opentelemetry-distro>=0.10.1

# Instrumented execution
CMD ["opentelemetry-instrument", "python", "-m", "agent_module"]
```

### Requirements Configuration

All `requirements.txt` files include:

```txt
# Observability
aws-opentelemetry-distro>=0.10.1
```

## 📊 Observability Features

### Automatic Metrics Collection

The following metrics are automatically collected:

1. **Request Metrics**
   - Request count and rate
   - Response times (latency distribution)
   - Error rates and types
   - Concurrent request handling

2. **Agent-Specific Metrics**
   - **CrewAI Agent**: Task execution times, crew workflow stages
   - **LangGraph Agent**: Graph node execution, tool usage
   - **Orchestrator**: Inter-agent communication, workflow coordination

3. **Resource Metrics**
   - Memory usage
   - CPU utilization
   - Container health

### Distributed Tracing

Each request generates traces containing:

- **Root Span**: Full request lifecycle
- **Child Spans**: Individual agent operations
- **Custom Attributes**: Agent type, model used, tools invoked
- **Error Context**: Stack traces and error details

## 📈 CloudWatch Dashboard Access

### Prerequisites

1. **Enable Transaction Search**
   ```bash
   # Enable in CloudWatch console or via CLI
   aws logs put-account-policy \
     --policy-name TransactionSearch \
     --policy-type DATA_PROTECTION_POLICY \
     --policy-document file://transaction-search-policy.json
   ```

2. **IAM Permissions**
   Ensure your execution role has:
   - `cloudwatch:PutMetricData`
   - `xray:PutTraceSegments`
   - `logs:CreateLogGroup`
   - `logs:CreateLogStream`
   - `logs:PutLogEvents`

### Dashboard Navigation

1. **GenAI Observability Dashboard**
   - Go to CloudWatch Console
   - Navigate to "Insights" → "GenAI Observability"
   - Filter by time range and agent name

2. **Key Views**
   - **Overview**: All agents runtime metrics
   - **Agent-Specific**: Individual agent performance
   - **Sessions**: Request session analysis
   - **Traces**: Detailed execution traces

## 🔍 Monitoring Best Practices

### Key Metrics to Monitor

1. **Performance Metrics**
   - Average response time < 30 seconds
   - 95th percentile latency
   - Error rate < 1%

2. **Cost Metrics**
   - Model token usage
   - Request frequency
   - Resource utilization

3. **Business Metrics**
   - Successful renovations analyzed
   - Cost estimates generated
   - User satisfaction (custom metrics)

### Alerting Setup

Example CloudWatch alarms:

```json
{
  "AlarmName": "AgentCore-HighErrorRate",
  "ComparisonOperator": "GreaterThanThreshold",
  "EvaluationPeriods": 2,
  "MetricName": "Errors",
  "Namespace": "AWS/BedrockAgentCore",
  "Period": 300,
  "Statistic": "Sum",
  "Threshold": 5.0,
  "ActionsEnabled": true,
  "AlarmActions": ["arn:aws:sns:us-west-2:123456789012:agent-alerts"],
  "AlarmDescription": "Alert when agent error rate exceeds threshold"
}
```

## 🚦 Health Check Monitoring

### Built-in Health Checks

Each agent includes:

- `/ping` endpoint for container health
- `/invocations` endpoint for functional testing
- Automatic retry logic and circuit breakers

### Manual Health Verification

```bash
# Test agent health
curl -X GET https://your-agent-endpoint/ping

# Test agent function
curl -X POST https://your-agent-endpoint/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test kitchen analysis"}'
```

## 📋 Troubleshooting Guide

### Common Issues

1. **Missing Traces**
   - Verify `aws-opentelemetry-distro` is installed
   - Check IAM permissions for X-Ray
   - Confirm Transaction Search is enabled

2. **High Latency**
   - Review model selection (smaller models for faster response)
   - Check external service dependencies
   - Monitor resource constraints

3. **Error Rates**
   - Check CloudWatch Logs for detailed error messages
   - Verify agent dependencies and model availability
   - Review payload validation

### Debug Commands

```bash
# Check agent logs
aws logs describe-log-groups --log-group-name-prefix "/aws/bedrock-agentcore"

# View recent traces
aws xray get-trace-summaries --time-range-type TimeRangeByStartTime \
  --start-time 2024-01-01T00:00:00 --end-time 2024-01-01T23:59:59

# Monitor metrics
aws cloudwatch get-metric-statistics --namespace AWS/BedrockAgentCore \
  --metric-name Invocations --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z --period 3600 --statistics Sum
```

## 🔄 Deployment Considerations

### Environment Variables

Set in your deployment:

```bash
export AWS_REGION=us-west-2
export OTEL_EXPORTER_OTLP_ENDPOINT=https://cloudwatch-fips.us-west-2.amazonaws.com
export OTEL_AWS_APPLICATION_SIGNALS_ENABLED=true
```

### Security

- All traces exclude sensitive payload data
- Custom span attributes are sanitized
- Logs are encrypted at rest in CloudWatch

## 📚 Additional Resources

- [AWS OpenTelemetry Documentation](https://docs.aws.amazon.com/xray/latest/devguide/aws-otel.html)
- [CloudWatch GenAI Observability](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-GenAI-observability.html)
- [AgentCore Runtime Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-runtime.html)

## 🎯 Next Steps

1. Deploy agents with observability enabled
2. Configure CloudWatch dashboards
3. Set up alerting thresholds
4. Review metrics and optimize performance
5. Implement custom business metrics as needed

---

*This implementation provides comprehensive observability for production GenAI agents with minimal performance overhead and maximum insight into system behavior.*
