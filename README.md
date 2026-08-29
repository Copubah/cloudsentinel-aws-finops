# CloudSentinel AWS FinOps
CloudSentinel is an AWS FinOps platform that discovers cloud resources, analyzes their utilization and costs, identifies idle or low-activity resources, and provides actionable cost-optimization recommendations.

The project is designed around a real-world cloud operations workflow:

AWS Account
     │
     ▼
Resource Discovery
     │
     ├── EC2
     ├── EBS
     ├── Elastic IP
     ├── NAT Gateway
     ├── RDS
     ├── Lambda
     ├── DynamoDB
     ├── S3
     └── CloudFront
          │
          ▼
   CloudWatch Metrics
          │
          ▼
    AWS Cost Explorer
          │
          ▼
    FinOps Analysis
          │
     ┌────┴────┐
     ▼         ▼
   Idle     Low Activity
 Resources   Resources
     │         │
     └────┬────┘
          ▼
 Cost Optimization
 Recommendations
          │
          ▼
    FinOps Agent
          │
          ▼
     Web Dashboard


## Project Goals

CloudSentinel aims to answer four important questions:

1. What AWS resources are running?**
2. Which resources are idle or underutilized?
3. What is actually costing money?
4. What can be optimized to reduce AWS spending?

Unlike a basic AWS inventory script, CloudSentinel combines resource discovery, utilization data, and billing information to provide FinOps recommendations.

---

# Features

## AWS Resource Discovery

CloudSentinel scans enabled AWS regions and identifies resources including:

* EC2
* EBS
* Elastic IPs
* NAT Gateways
* RDS
* Lambda
* DynamoDB
* S3
* CloudFront

Example:
Total resources: 5

Resource Summary:
  Lambda                        1
  DynamoDB                      1
  S3                            2
  CloudFront                    1
  idle_resources                0
  low_activity_resources        1
  active_resources              4

## Multi-Region Scanning
The scanner automatically discovers enabled AWS regions rather than requiring regions to be manually configured.

Example:
Scanning region: ap-northeast-1
Scanning region: ap-south-1
Scanning region: eu-central-1
Scanning region: eu-west-1
Scanning region: us-east-1
Scanning region: us-west-2
```

Global services such as S3 and CloudFront are scanned separately.

---

# Utilization Analysis

CloudSentinel uses Amazon CloudWatch metrics to determine whether resources are being used.

For Lambda, the platform currently analyzes invocation activity over the previous 30 days.

Example:
Lambda
Invocations (30d): 6.0
Classification: LOW ACTIVITY


Resources can be classified as:

ACTIVE
LOW ACTIVITY
IDLE

---

# Idle Resource Detection

CloudSentinel identifies resources that may be generating unnecessary costs.

Examples include:

### EBS

EBS volume
      ↓
No attached EC2 instance
      ↓
IDLE


### Elastic IP

Elastic IP
      ↓
Not associated
      ↓
IDLE


### EC2

EC2 instance
      ↓
Stopped
      ↓
IDLE


### Lambda

Lambda
      ↓
0 invocations / 30 days
      ↓
IDLE


Low-activity resources are also flagged for review.

---

# AWS Cost Explorer

CloudSentinel integrates with AWS Cost Explorer to retrieve:

* Current monthly AWS cost
* Cost by AWS service
* Usage-type costs
* Cost drivers

Example:

FINOPS COST

Current month:
$0.08 USD

COST BY SERVICE:

AWS Lambda
Amazon S3
Amazon DynamoDB
Amazon CloudFront
AmazonCloudWatch
AWS Key Management Service


This allows CloudSentinel to combine:

Resource
   +
Utilization
   +
Cost


instead of looking at each independently.

---

# FinOps Recommendation Engine

The next stage of the project converts raw AWS data into recommendations.

Example:
Lambda Function
6 invocations / 30 days
        │
        ▼
LOW ACTIVITY
        │
        ▼
Review function necessity
        │
        ▼
Potential cost optimization


Future recommendations will include:

* Delete unused EBS volumes
* Release unassociated Elastic IPs
* Review stopped EC2 instances
* Review inactive Lambda functions
* Review idle RDS databases
* Review unnecessary NAT Gateways
* Identify S3 storage optimization opportunities
* Identify CloudFront optimization opportunities
* Identify DynamoDB capacity inefficiencies

---

# AWS FinOps Agent

CloudSentinel will integrate an AWS FinOps Agent to provide higher-level analysis of the collected cloud data.

The agent will be able to reason about:
Resource inventory
       +
CloudWatch metrics
       +
Cost Explorer
       +
Resource metadata
       ↓
FinOps Agent
       ↓
Prioritized recommendations


Example:

Recommendation

Resource:
s3-storage-optimizer-dev-scanner

Activity:
6 Lambda invocations in 30 days

Finding:
Low activity

Priority:
Medium

Action:
Review whether this function is still required.

Estimated savings:
Calculated using AWS cost data.

---

# Architecture

                  ┌──────────────────────┐
                  │      AWS Account     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Resource Discovery   │
                  └──────────┬───────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
       EC2/EBS          Lambda/RDS        S3/CloudFront
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                  ┌──────────────────────┐
                  │    CloudWatch        │
                  │    Utilization       │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Cost Explorer      │
                  │   Billing Analysis   │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   FinOps Engine      │
                  └──────────┬───────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        Idle Detection            Cost Analysis
                │                         │
                └────────────┬────────────┘
                             ▼
                  ┌──────────────────────┐
                  │ FinOps Agent         │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Web Dashboard        │
                  └──────────────────────┘

---

# Project Phases

| Phase | Component                          | Status      |
| ----- | ---------------------------------- | ----------- |
| 1     | Project setup                      | Complete    |
| 2     | AWS authentication                 | Complete    |
| 3     | Resource discovery                 | Complete    |
| 4     | S3 optimization analysis           | Complete    |
| 5     | DynamoDB persistence               | Complete    |
| 6     | Lambda scanner                     | Complete    |
| 7     | CloudFront integration             | Complete    |
| 8     | Multi-region scanning              | Complete    |
| 9     | Resource inventory                 | Complete    |
| 10    | Basic idle detection               | Complete    |
| 11    | CloudWatch utilization             | Complete    |
| 12    | Cost Explorer integration          | In progress |
| 13    | FinOps recommendation engine       | Planned     |
| 14    | AWS FinOps Agent                   | Planned     |
| 15    | Web dashboard, alerts & deployment | Planned     |

---

# Technology Stack

### Cloud

* AWS
* AWS Lambda
* Amazon S3
* Amazon DynamoDB
* Amazon CloudFront
* Amazon CloudWatch
* AWS Cost Explorer
* AWS IAM

### Development

* Python
* Bash
* AWS CLI
* Boto3
* Git
* GitHub

### Planned

* FinOps Agent
* React dashboard
* API layer
* Automated alerts
* Scheduled scanning
* Cost forecasting

---

# Repository Structure

```text
cloudsentinel/
│
├── backend/
│   └── lambda/
│       └── scanner/
│           └── handler.py
│
├── frontend/
│
├── infrastructure/
│
├── tests/
│
├── scripts/
│
├── docs/
│
├── .gitignore
├── README.md
└── requirements.txt


---

# Installation

## Clone the repository

git clone https://github.com/YOUR_USERNAME/cloudsentinel-aws-finops.git

cd cloudsentinel-aws-finops


## Install dependencies
pip install -r requirements.txt


## Configure AWS CLI

aws configure

Verify authentication:


aws sts get-caller-identity


Example:

```json
{
    "Account": "YOUR_AWS_ACCOUNT_ID",
    "Arn": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:user/YOUR_USER"
}
```

---

# Run the Scanner

python3 backend/lambda/scanner/handler.py

CloudSentinel will:

1. Discover enabled AWS regions.
2. Scan regional resources.
3. Scan global resources.
4. Query CloudWatch utilization metrics.
5. Classify resources.
6. Query AWS Cost Explorer.
7. Generate a FinOps summary.

---

# Example Output

================================================================================
                  CloudSentinel
          AWS Resource & FinOps Scanner
================================================================================

Total resources: 5

Resource Summary:
  Lambda                        1
  DynamoDB                      1
  S3                            2
  CloudFront                    1
  idle_resources                0
  low_activity_resources        1
  active_resources              4

Resources:

  Lambda
      Region: us-east-1
      Invocations (30d): 6
      Classification: LOW ACTIVITY

  DynamoDB
      Region: us-east-1
      Classification: ACTIVE

  S3
      Region: us-east-1
      Classification: ACTIVE

  S3
      Region: us-east-1
      Classification: ACTIVE

  CloudFront
      Region: global
      Classification: ACTIVE


---

# Security

CloudSentinel is designed to operate in **read-only mode** during scanning.

The scanner does not automatically:

* Delete resources
* Stop EC2 instances
* Delete databases
* Release Elastic IPs
* Modify S3 buckets
* Modify IAM permissions

Recommendations are generated for human review before any remediation action is performed.

AWS credentials should never be committed to the repository.

Add sensitive files to `.gitignore`:

.env
*.pem
*.key
.aws/
credentials
```

---

# IAM Permissions

The scanner requires permissions to inspect AWS resources and retrieve monitoring and billing information.

Required permissions will vary depending on the services enabled in the AWS account.

Core permissions include read-only access to:

EC2
EBS
RDS
Lambda
DynamoDB
S3
CloudFront
CloudWatch
Cost Explorer
```

For production deployments, use a dedicated IAM role with the minimum permissions required.

---

# FinOps Philosophy

CloudSentinel follows a simple principle:

> **Don't optimize what you haven't measured.**

The platform therefore follows:

```text
Discover
   ↓
Measure
   ↓
Analyze
   ↓
Prioritize
   ↓
Recommend
   ↓
Remediate
   ↓
Measure Again
```

This makes the project useful not only as an AWS monitoring tool, but as a practical demonstration of FinOps and Cloud Operations.

---

# Roadmap

### Current

* [x] AWS resource discovery
* [x] Multi-region scanning
* [x] Lambda utilization analysis
* [x] Idle resource detection
* [x] Cost Explorer access

### Next

* [ ] Cost-to-resource mapping
* [ ] Savings estimation
* [ ] FinOps recommendation engine
* [ ] S3 cost optimization
* [ ] DynamoDB utilization analysis
* [ ] CloudFront analysis
* [ ] RDS utilization analysis
* [ ] EC2 utilization analysis

### Future

* [ ] AWS FinOps Agent integration
* [ ] Natural-language FinOps queries
* [ ] React dashboard
* [ ] Cost trend visualization
* [ ] Automated scheduled scans
* [ ] Email/Slack alerts
* [ ] Automated remediation with approval
* [ ] Monthly FinOps reports

---

# Why CloudSentinel?

CloudSentinel is designed as a practical cloud engineering project rather than a simple AWS inventory script.

It demonstrates:

* AWS architecture
* Cloud Operations
* FinOps
* Infrastructure monitoring
* Python/Boto3
* CloudWatch
* Cost Explorer
* Serverless architecture
* Multi-region AWS operations
* Cloud security
* Automation
* Data analysis
* AI-assisted cloud optimization

The long-term goal is to turn CloudSentinel into a lightweight **AWS FinOps and Cloud Operations platform** capable of continuously identifying waste and explaining where optimization opportunities exist.

---

# License

This project is licensed under the MIT License.
