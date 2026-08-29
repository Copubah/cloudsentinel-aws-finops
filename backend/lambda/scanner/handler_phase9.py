import boto3
from botocore.exceptions import ClientError


def safe_call(function, default=None):
    """Execute an AWS API call without crashing the entire scan."""
    try:
        return function()
    except ClientError as e:
        print(f"AWS API error: {e}")
        return default if default is not None else []


def get_ec2_instances():
    ec2 = boto3.client("ec2")
    response = safe_call(lambda: ec2.describe_instances(), {"Reservations": []})

    resources = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            name = None

            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]

            resources.append({
                "resource_id": instance["InstanceId"],
                "resource_type": "EC2",
                "name": name,
                "region": ec2.meta.region_name,
                "status": instance["State"]["Name"],
                "instance_type": instance["InstanceType"],
                "launch_time": str(instance["LaunchTime"]),
            })

    return resources


def get_ebs_volumes():
    ec2 = boto3.client("ec2")

    response = safe_call(
        lambda: ec2.describe_volumes(),
        {"Volumes": []}
    )

    resources = []

    for volume in response["Volumes"]:
        resources.append({
            "resource_id": volume["VolumeId"],
            "resource_type": "EBS",
            "region": ec2.meta.region_name,
            "status": volume["State"],
            "size_gb": volume["Size"],
            "volume_type": volume["VolumeType"],
            "attached_instance": (
                volume["Attachments"][0]["InstanceId"]
                if volume["Attachments"]
                else None
            ),
            "created": str(volume["CreateTime"]),
        })

    return resources


def get_elastic_ips():
    ec2 = boto3.client("ec2")

    response = safe_call(
        lambda: ec2.describe_addresses(),
        {"Addresses": []}
    )

    resources = []

    for address in response["Addresses"]:
        resources.append({
            "resource_id": address.get("AllocationId"),
            "resource_type": "Elastic IP",
            "region": ec2.meta.region_name,
            "status": "associated" if address.get("InstanceId") or address.get(
                "NetworkInterfaceId"
            ) else "unassociated",
            "public_ip": address.get("PublicIp"),
        })

    return resources


def get_nat_gateways():
    ec2 = boto3.client("ec2")

    response = safe_call(
        lambda: ec2.describe_nat_gateways(
            Filter=[
                {
                    "Name": "state",
                    "Values": ["available", "pending", "failed"]
                }
            ]
        ),
        {"NatGateways": []}
    )

    resources = []

    for gateway in response["NatGateways"]:
        resources.append({
            "resource_id": gateway["NatGatewayId"],
            "resource_type": "NAT Gateway",
            "region": ec2.meta.region_name,
            "status": gateway["State"],
            "vpc_id": gateway.get("VpcId"),
            "subnet_id": gateway.get("SubnetId"),
            "created": str(gateway.get("CreateTime")),
        })

    return resources


def get_rds_instances():
    rds = boto3.client("rds")

    response = safe_call(
        lambda: rds.describe_db_instances(),
        {"DBInstances": []}
    )

    resources = []

    for db in response["DBInstances"]:
        resources.append({
            "resource_id": db["DBInstanceIdentifier"],
            "resource_type": "RDS",
            "region": rds.meta.region_name,
            "status": db["DBInstanceStatus"],
            "engine": db["Engine"],
            "instance_class": db["DBInstanceClass"],
            "storage_gb": db.get("AllocatedStorage"),
        })

    return resources


def get_lambda_functions():
    lambda_client = boto3.client("lambda")

    response = safe_call(
        lambda: lambda_client.list_functions(),
        {"Functions": []}
    )

    resources = []

    for function in response["Functions"]:
        resources.append({
            "resource_id": function["FunctionArn"],
            "resource_type": "Lambda",
            "name": function["FunctionName"],
            "region": lambda_client.meta.region_name,
            "runtime": function.get("Runtime"),
            "memory_mb": function.get("MemorySize"),
            "last_modified": function.get("LastModified"),
        })

    return resources


def get_dynamodb_tables():
    dynamodb = boto3.client("dynamodb")

    table_names = safe_call(
        lambda: dynamodb.list_tables(),
        {"TableNames": []}
    )

    resources = []

    for table_name in table_names["TableNames"]:
        details = safe_call(
            lambda name=table_name: dynamodb.describe_table(
                TableName=name
            ),
            {}
        )

        table = details.get("Table")

        if not table:
            continue

        resources.append({
            "resource_id": table["TableArn"],
            "resource_type": "DynamoDB",
            "name": table["TableName"],
            "region": dynamodb.meta.region_name,
            "status": table["TableStatus"],
            "created": str(table.get("CreationDateTime")),
            "item_count": table.get("ItemCount"),
        })

    return resources


def get_s3_buckets():
    s3 = boto3.client("s3")

    response = safe_call(
        lambda: s3.list_buckets(),
        {"Buckets": []}
    )

    resources = []

    for bucket in response["Buckets"]:
        bucket_name = bucket["Name"]

        try:
            location = s3.get_bucket_location(
                Bucket=bucket_name
            )

            region = location.get("LocationConstraint")

            if region is None:
                region = "us-east-1"

        except ClientError as e:
            print(
                f"Could not determine region for S3 bucket "
                f"{bucket_name}: {e}"
            )
            region = "unknown"

        resources.append({
            "resource_id": bucket_name,
            "resource_type": "S3",
            "name": bucket_name,
            "region": region,
            "created": str(bucket["CreationDate"]),
            "status": "active",
        })

    return resources


def get_cloudfront_distributions():
    cloudfront = boto3.client("cloudfront")

    response = safe_call(
        lambda: cloudfront.list_distributions(),
        {}
    )

    distributions = response.get("DistributionList", {})
    items = distributions.get("Items", [])

    resources = []

    for distribution in items:
        resources.append({
            "resource_id": distribution["Id"],
            "resource_type": "CloudFront",
            "region": "global",
            "status": distribution["Status"],
            "domain": distribution.get("DomainName"),
            "enabled": distribution.get("Enabled"),
        })

    return resources


def scan_resources():
    resources = []

    resources.extend(get_ec2_instances())
    resources.extend(get_ebs_volumes())
    resources.extend(get_elastic_ips())
    resources.extend(get_nat_gateways())
    resources.extend(get_rds_instances())
    resources.extend(get_lambda_functions())
    resources.extend(get_dynamodb_tables())
    resources.extend(get_s3_buckets())
    resources.extend(get_cloudfront_distributions())

    return resources


def handler(event=None, context=None):
    resources = scan_resources()

    summary = {}

    for resource in resources:
        resource_type = resource["resource_type"]

        summary[resource_type] = summary.get(
            resource_type,
            0
        ) + 1

    return {
        "statusCode": 200,
        "summary": summary,
        "total_resources": len(resources),
        "resources": resources,
    }


if __name__ == "__main__":
    result = handler()

    print("\n=== CloudSentinel AWS Resource Scan ===\n")
    print(f"Total resources: {result['total_resources']}\n")

    print("Summary:")

    for resource_type, count in result["summary"].items():
        print(f"  {resource_type}: {count}")

    print("\nResources:")

    for resource in result["resources"]:
        print(
            f"  {resource['resource_type']:<15} "
            f"{resource['resource_id']}"
        )
