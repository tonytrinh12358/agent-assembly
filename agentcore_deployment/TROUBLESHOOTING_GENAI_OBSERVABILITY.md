# 🔍 Troubleshooting GenAI Observability Dashboard

## Issue: Not Seeing Data in Bedrock AgentCore Observability

You have Transaction Search enabled (✅ confirmed) and agents deployed with OpenTelemetry (✅ confirmed), but not seeing data in the GenAI Observability dashboard.

## 🕐 **Most Likely Cause: Timing**

**GenAI Observability data can take 5-15 minutes to appear after agent invocations.**

### ⏰ Wait Time Checklist:
- ✅ Transaction Search enabled
- ✅ Agents deployed with observability  
- ✅ Agents invoked successfully
- ⏳ **Wait 10-15 minutes after invocations**

## 📍 **Dashboard Location Issues**

The GenAI Observability dashboard might be in different locations:

### 🔗 Try These URLs:

1. **Primary GenAI Observability**:
   ```
   https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#genai-observability:home
   ```

2. **CloudWatch Insights**:
   ```
   https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#insights:home
   ```

3. **Application Signals** (Alternative):
   ```
   https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#application-signals:home
   ```

4. **X-Ray Service Map**:
   ```
   https://us-west-2.console.aws.amazon.com/xray/home?region=us-west-2#service-map
   ```

## 🔧 **Manual Dashboard Search**

In CloudWatch Console:

1. Go to **CloudWatch** → **Insights**
2. Look for **"GenAI"** or **"Generative AI"** section
3. Search for your agent names:
   - `orchestrator_agent-wO9MODGRe9`
   - `langgraph_agent-bH2lUr45Jq`
   - `crewai_agent-J93te7CbkT`

## 📊 **Alternative: Check X-Ray Directly**

If GenAI Observability isn't showing, check X-Ray:

1. **Service Map**: Look for `bedrock-agentcore` services
2. **Traces**: Filter by service name containing `orchestrator`, `langgraph`, or `crewai`
3. **Timeline**: Check traces from the last hour

## 🔍 **Verification Steps**

### Step 1: Check CloudWatch Metrics
```bash
aws cloudwatch list-metrics \
  --namespace "AWS/BedrockAgentCore" \
  --region us-west-2
```

### Step 2: Look for Application Signals
In CloudWatch Console → Application Signals → Services
- Look for services named after your agents

### Step 3: Search in CloudWatch Logs Insights
```sql
fields @timestamp, @message
| filter @message like /orchestrator/
| sort @timestamp desc
| limit 20
```

## 🚨 **Common Issues & Solutions**

### Issue 1: Feature Not Enabled
**Solution**: GenAI Observability might need explicit enablement:
```bash
aws logs put-account-policy \
  --policy-name "GenAIObservability" \
  --policy-type "DATA_PROTECTION_POLICY" \
  --policy-document file://cloudwatch-transaction-search-policy.json
```

### Issue 2: Wrong Region
**Solution**: Ensure you're looking in `us-west-2` region where agents are deployed.

### Issue 3: Insufficient Data
**Solution**: Generate more agent invocations:
```bash
# Run more tests to generate data
for i in {1..5}; do
  python test_orchestrator.py
  sleep 30
done
```

### Issue 4: Dashboard Under Different Name
**Solution**: Look for:
- "Application Insights"
- "Service Lens"  
- "Container Insights"
- "Lambda Insights"

## 🎯 **Immediate Actions**

### 1. Wait & Check Again (Most Important)
- Wait 15 minutes after last agent invocation
- Refresh CloudWatch console
- Check multiple dashboard locations

### 2. Generate More Data
```bash
cd /Users/totrinh/Library/CloudStorage/OneDrive-amazon.com/workspace/agent-assemble/TechSummit_2025/agentcore_deployment

# Run orchestrator multiple times
for i in {1..3}; do 
  echo "Test $i..."
  python test_orchestrator.py > /dev/null
  sleep 60
done
```

### 3. Check Alternative Observability Views
- X-Ray Service Map
- CloudWatch Application Signals  
- CloudWatch Container Insights

## 📋 **Expected Dashboard Content**

When working, you should see:

### Metrics:
- **Invocations**: Request count per agent
- **Duration**: Response time distributions  
- **Errors**: Failed request rates
- **Token Usage**: Model consumption

### Traces:
- Request flow: Client → Orchestrator → Sub-agents
- Span details: Tool usage, model calls
- Error context: Stack traces, debugging info

## 🔄 **Next Steps If Still Not Working**

1. **Contact AWS Support**: GenAI Observability might need account-level enablement
2. **Check Feature Availability**: Verify GenAI Observability is available in us-west-2
3. **Use Alternative Tools**: CloudWatch Logs Insights, X-Ray, custom dashboards

## ✅ **Success Indicators**

You'll know it's working when you see:
- Agent names in GenAI Observability dropdown
- Request metrics showing invocation counts
- Trace data with span details
- Service map showing agent relationships

---

**Most likely solution**: Wait 10-15 minutes and check the specific GenAI Observability URLs above. The data propagation delay is common for newly deployed services.
