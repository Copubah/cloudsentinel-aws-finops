# CloudSentinel

CloudSentinel is a read-only AWS resource inventory, utilization, and account-cost scanner. It discovers resources across enabled AWS Regions, identifies a small set of potentially idle resources, retrieves account-level AWS costs, and prints a concise summary for review.

It is intended as a foundation for an AWS FinOps workflow: first discover what exists, then measure usage, and finally decide what—if anything—should be changed. CloudSentinel never modifies AWS resources.

## What it scans

Regional services are scanned in every enabled or opt-in-not-required AWS Region:

| Service | Collected details |
| --- | --- |
| Amazon EC2 | instance ID, name, state, type, and launch time |
| Amazon EBS | volume ID, state, size, type, attachment, and creation time |
| Elastic IP | allocation ID, public IP, and association status |
| NAT Gateway | gateway ID, state, VPC, and subnet |
| Amazon RDS | instance ID, status, engine, instance class, and allocated storage |
| AWS Lambda | ARN, runtime, memory, last-modified time, and 30-day invocation count |
| Amazon DynamoDB | table ARN, name, status, and item count |

Global services are scanned once:

| Service | Collected details |
| --- | --- |
| Amazon S3 | bucket name, creation time, and bucket Region |
| Amazon CloudFront | distribution ID, status, enabled state, and domain |

## Current detection rules

CloudSentinel classifies each discovered resource as `ACTIVE`, `LOW ACTIVITY`, or `IDLE` using the following rules.

| Resource | Classification rule |
| --- | --- |
| EBS volume | `IDLE` when it has no attached instance |
| Elastic IP | `IDLE` when it is unassociated |
| EC2 instance | `IDLE` when its state is `stopped` |
| RDS instance | `IDLE` when its status is `stopped` |
| NAT Gateway | `IDLE` when its state is `failed` |
| Lambda function | `IDLE` with zero invocations in the previous 30 days; `LOW ACTIVITY` with fewer than 10 |
| All other discovered resources | `ACTIVE` unless a rule above applies |

These are review signals, not deletion decisions. A stopped instance or an infrequently invoked function can still be intentional and valuable.

## Cost Explorer

When Cost Explorer is enabled and the caller has access, CloudSentinel retrieves month-to-date `NetUnblendedCost`, grouped by AWS service and usage type, plus a daily cost trend. It also requests a best-effort daily forecast for the remainder of the current month; unavailable forecast data is reported separately and does not hide cost results. Current-period values can be marked as estimated by AWS; credits, refunds, and zero or negative values are preserved rather than treated as waste.

Cost data is account-level only. CloudSentinel does not attribute a service cost to a specific resource or calculate savings estimates at this stage.

Each scan makes at least five Cost Explorer API requests (month-to-date total, service and usage-type groups, daily trend, and forecast); pagination can add requests. AWS currently charges $0.01 per Cost Explorer API request against a primary billing view, so the baseline Cost Explorer query cost is approximately $0.05 per scan before pagination. Schedule scans deliberately and add caching before serving this data through a dashboard.

## Architecture

```text
AWS account
  └─ enabled Regions
       └─ resource discovery ──┐
  └─ S3 and CloudFront ────────┤
                                ├─ idle / activity analysis ──> summary and resource list
CloudWatch Lambda invocations ──┘
```

## Requirements

- Python 3.9 or later
- An AWS account and credentials available to the AWS SDK for Python (Boto3)
- Permission to list the relevant resources and read Lambda CloudWatch metrics

CloudSentinel uses the standard AWS credential provider chain. This includes a configured AWS CLI profile, environment variables, IAM roles, or other Boto3-supported credential sources.

## Install

```bash
git clone https://github.com/Copubah/cloudsentinel-aws-finops.git
cd cloudsentinel-aws-finops

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

Configure credentials if you are developing locally:

```bash
aws configure
aws sts get-caller-identity
```

Do not commit credentials, access keys, or local AWS configuration files to the repository.

## Run locally

```bash
python3 backend/lambda/scanner/handler.py
```

The scan can take time in accounts with many enabled Regions or Lambda functions because the scanner queries each supported regional service and reads a CloudWatch metric for every Lambda function. AWS API errors are printed and the scanner continues with the remaining checks where possible.

Example output:

```text
Enabled regions found: 2

Scanning region: us-east-1
  EC2
  EBS
  Elastic IP
  NAT Gateway
  RDS
  Lambda
  DynamoDB

Scanning global services
  S3
  CloudFront

================================================================================
                  CloudSentinel
          AWS Resource & FinOps Scanner
================================================================================

Total resources: 5

Resource Summary:
  Lambda                        1
  S3                            2
  CloudFront                    1
  idle_resources                0
  low_activity_resources        1
  active_resources              4
```

## Run as an AWS Lambda function

The scanner exposes a standard Python Lambda handler:

```text
handler.handler
```

It returns a JSON-serializable object with `statusCode`, `total_resources`, `summary`, and `resources`. Package `boto3` with the function only when your target Lambda runtime does not already provide a compatible version.

## IAM permissions

Use a dedicated least-privilege IAM role. The scanner needs read access equivalent to these actions:

```text
ec2:DescribeRegions
ec2:DescribeInstances
ec2:DescribeVolumes
ec2:DescribeAddresses
ec2:DescribeNatGateways
rds:DescribeDBInstances
lambda:ListFunctions
dynamodb:ListTables
dynamodb:DescribeTable
s3:ListAllMyBuckets
s3:GetBucketLocation
cloudfront:ListDistributions
cloudwatch:GetMetricStatistics
ce:GetCostAndUsage
ce:GetCostForecast
```

Some actions may need `Resource: "*"` because the corresponding AWS APIs do not support resource-level permissions. Scope access further where AWS supports it, and validate the policy against the services and Regions you intend to scan.

## Security and operational notes

- The scanner only calls read/list/describe APIs and CloudWatch metric reads. It does not delete, stop, terminate, release, or reconfigure resources.
- Review every `IDLE` or `LOW ACTIVITY` result before remediation. The tool has no cost calculation or automated remediation capability.
- The scanner discovers enabled AWS Regions from EC2. If that call is denied, regional discovery returns no Regions, though global S3 and CloudFront checks still run.
- S3 and CloudFront are treated as global discovery operations; S3 bucket locations are reported individually.

## Repository layout

```text
cloudsentinel/
├── backend/
│   ├── requirements.txt
│   └── lambda/
│       └── scanner/
│           └── handler.py       # scanner and Lambda entry point
├── infrastructure/              # reserved for infrastructure code
├── scripts/                     # reserved for helper scripts
├── tests/                       # reserved for tests
└── README.md
```

## Roadmap

- Cost Explorer integration and cost-to-resource mapping
- Savings estimates and prioritized recommendations
- Additional utilization analysis for EC2, RDS, DynamoDB, S3, CloudFront, and NAT Gateways
- Scheduled scans, persistence, alerts, and a web dashboard

## License

This project is licensed under the [MIT License](LICENSE).
