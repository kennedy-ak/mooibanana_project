# AWS CloudWatch Logging Setup Guide

## 📋 Overview
Your application now supports **dual logging**:
- **Local files** (logs/ directory) - Always active
- **AWS CloudWatch** - Optional, for production monitoring

## 🚀 Quick Setup (3 Steps)

### Step 1: Get AWS Credentials

You need an AWS account with CloudWatch access. Two options:

#### Option A: Create IAM User (Recommended)
1. Go to AWS Console → IAM → Users → Create User
2. User name: `mooibanana-logger`
3. Attach policy: `CloudWatchLogsFullAccess` (or create custom policy below)
4. Create access key → Save the credentials

**Custom Policy (Least Privilege)**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:mooibanana-app:*"
        }
    ]
}
```

#### Option B: Use EC2 Instance Role (if deployed on EC2)
- Attach IAM role with CloudWatch permissions to your EC2 instance
- No credentials needed in .env file

### Step 2: Configure Environment Variables

Add these to your `.env` file:

```bash
# AWS CloudWatch Configuration
AWS_CLOUDWATCH_ENABLED=True
AWS_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
CLOUDWATCH_LOG_GROUP=mooibanana-app
```

**Available Regions**: `us-east-1`, `us-west-2`, `eu-west-1`, `eu-central-1`, etc.

### Step 3: Restart Your Application

```bash
# The log group will be created automatically on first log
python manage.py runserver
```

## 📊 CloudWatch Log Structure

Your logs will be organized in CloudWatch as:

```
Log Group: mooibanana-app
├── general-2025-11-11 (INFO logs from all apps)
├── payments-2025-11-11 (DEBUG logs from payment operations)
├── errors-2025-11-11 (ERROR logs from all apps)
└── security-2025-11-11 (WARNING+ security events)
```

**Log streams rotate daily automatically** - each day gets a new stream.

## 🔍 Viewing Logs in AWS Console

1. Go to **AWS Console** → **CloudWatch** → **Logs** → **Log groups**
2. Click on `mooibanana-app`
3. Select a log stream (e.g., `payments-2025-11-11`)
4. Use the search bar to filter logs

### Useful CloudWatch Queries

**Find all payment errors today**:
```
fields @timestamp, @message
| filter @message like /ERROR/
| filter @logStream like /payments/
| sort @timestamp desc
```

**Track specific user activity**:
```
fields @timestamp, @message
| filter @message like /User: 123/
| sort @timestamp desc
```

**Monitor failed login attempts**:
```
fields @timestamp, @message
| filter @message like /Failed login/
| stats count() by bin(5m)
```

## 🔔 Setting Up CloudWatch Alarms

### Example 1: Alert on Payment Failures

1. CloudWatch → Alarms → Create Alarm
2. Select Metric → Logs → Log Group Metrics
3. **Metric filter**:
   ```
   [time, level=ERROR*, logger=payments*, ...]
   ```
4. **Condition**: >= 5 errors in 5 minutes
5. **Action**: Send SNS notification to your email

### Example 2: Alert on High Error Rate

```
Metric Filter Pattern: [level=ERROR]
Statistic: Sum
Period: 5 minutes
Threshold: >= 10 errors
```

## 💰 Cost Estimation

CloudWatch Logs pricing (as of 2024):
- **Ingestion**: $0.50 per GB
- **Storage**: $0.03 per GB/month
- **Free tier**: 5 GB ingestion + 5 GB storage

**Estimated costs for your app**:
- Small (1000 users): ~$5-10/month
- Medium (10k users): ~$20-40/month
- Large (100k users): ~$100-200/month

**Cost optimization tips**:
1. Set log retention to 7-30 days instead of infinite
2. Use log levels wisely (DEBUG only for critical apps)
3. Aggregate logs before querying

## 🛠 Advanced Configuration

### Different Regions for Different Environments

```python
# .env.production
AWS_REGION_NAME=us-east-1
CLOUDWATCH_LOG_GROUP=mooibanana-production

# .env.staging
AWS_REGION_NAME=us-west-2
CLOUDWATCH_LOG_GROUP=mooibanana-staging
```

### Log Retention Policy

Set in AWS Console:
1. CloudWatch → Log groups → `mooibanana-app`
2. Actions → Edit retention setting
3. Choose: 7 days, 30 days, 1 year, etc.

### Custom Log Streams

Add more specific log streams in `settings.py`:

```python
LOGGING['handlers']['cloudwatch_likes'] = {
    **cloudwatch_handler_config,
    'log_stream_name': 'likes-{strftime:%Y-%m-%d}',
}

LOGGING['loggers']['likes']['handlers'].append('cloudwatch_likes')
```

## 🧪 Testing CloudWatch Integration

```bash
# Start Django shell
python manage.py shell

# Test logging
import logging
logger = logging.getLogger('payments')
logger.info("Test CloudWatch integration")
logger.error("Test error logging")

# Check AWS Console → CloudWatch → Log groups → mooibanana-app
# You should see your test messages within 1-2 seconds
```

## 🐛 Troubleshooting

### Issue: "CloudWatch enabled but watchtower/boto3 not installed"
**Solution**: Run `pip install watchtower boto3`

### Issue: "CloudWatch enabled but AWS credentials not configured"
**Solution**: Check your `.env` file has all required variables

### Issue: "Unable to locate credentials"
**Solution**:
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are correct
- Ensure no extra spaces in .env file
- Try setting environment variables directly:
  ```bash
  export AWS_ACCESS_KEY_ID=your_key
  export AWS_SECRET_ACCESS_KEY=your_secret
  ```

### Issue: "Access Denied" when creating log group
**Solution**: Your IAM user/role needs `logs:CreateLogGroup` permission

### Issue: Logs not appearing in CloudWatch
**Checklist**:
1. ✓ `AWS_CLOUDWATCH_ENABLED=True` in .env
2. ✓ Credentials are correct
3. ✓ Application restarted after config changes
4. ✓ IAM permissions include `logs:PutLogEvents`
5. ✓ Check CloudWatch region matches `AWS_REGION_NAME`

### Issue: Too many log streams
**Solution**: This is normal - each day creates new streams. Set retention policy to clean up old logs.

## 📈 CloudWatch Dashboard Example

Create a dashboard to visualize your logs:

1. CloudWatch → Dashboards → Create dashboard
2. Add widgets:
   - **Line chart**: Payment transaction count over time
   - **Number**: Total errors in last hour
   - **Log insights**: Recent critical errors

## 🔒 Security Best Practices

1. ✅ **Never commit AWS credentials to git**
2. ✅ Use IAM roles instead of access keys when possible
3. ✅ Rotate access keys every 90 days
4. ✅ Use separate AWS accounts for prod/staging
5. ✅ Enable CloudTrail to audit CloudWatch access
6. ✅ Encrypt sensitive log data at rest (CloudWatch KMS)

## 🎯 When to Use CloudWatch vs Local Files

**Use Local Files**:
- Development environment
- Quick debugging
- Cost-conscious projects
- Testing

**Use CloudWatch**:
- Production environment
- Multiple servers/containers
- Long-term log retention
- Real-time monitoring and alerts
- Integration with other AWS services

## 📚 Additional Resources

- [AWS CloudWatch Logs Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)
- [Watchtower Python Library](https://github.com/kislyuk/watchtower)
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [AWS Free Tier Details](https://aws.amazon.com/free/)

## ✨ Summary

You now have:
- ✅ CloudWatch logging configured
- ✅ Automatic log stream organization
- ✅ Dual logging (local + cloud)
- ✅ Production-ready monitoring setup
- ✅ Cost-effective configuration

**Next steps**: Set up CloudWatch alarms for critical errors and payment failures!
