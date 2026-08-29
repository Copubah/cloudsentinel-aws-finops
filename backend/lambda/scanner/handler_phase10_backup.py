import boto3
from botocore.exceptions import ClientError


# ============================================================
# Configuration
# ============================================================

GLOBAL_SERVICES = {
    "S3",
    "CloudFront",
}


# ============================================================
# Utility
# ============================================================

def safe_call(function, default=None):
    try:
        return function()
    except ClientError as error:
        print(f"AWS API error: {error}")
        return default if default is not None else {}
    except Exception as error:
        print(f"Unexpected error: {error}")
        return default if default is not None else {}


# ============================================================
# Regions
# ============================================================

def get_enabled_regions():

    ec2 = boto3.client("ec2")

    response = safe_call(
        lambda: ec2.describe_regions(
            AllRegions=True
        ),
        {"Regions": []}
    )

    regions = []

    for region in response.get("Regions", []):

        status = region.get("OptInStatus")

        if status in [
            "opt-in-not-required",
            "opted-in"
        ]:
            regions.append(
                region["RegionName"]
            )

    return sorted(regions)


# ============================================================
# EC2
# ============================================================

def get_ec2_instances(region):

    ec2 = boto3.client(
        "ec2",
        region_name=region
    )

    response = safe_call(
        lambda: ec2.describe_instances(),
        {"Reservations": []}
    )

    resources = []

    for reservation in response.get(
        "Reservations",
        []
    ):

        for instance in reservation.get(
            "Instances",
            []
        ):

            name = None

            for tag in instance.get(
                "Tags",
                []
            ):

                if tag.get("Key") == "Name":
                    name = tag.get("Value")

            resources.append({
                "resource_id":
                    instance["InstanceId"],

                "resource_type":
                    "EC2",

                "name":
                    name,

                "region":
                    region,

                "status":
                    instance["State"]["Name"],

                "instance_type":
                    instance.get("InstanceType"),

                "launch_time":
                    str(instance.get("LaunchTime")),
            })

    return resources


# ============================================================
# EBS
# ============================================================

def get_ebs_volumes(region):

    ec2 = boto3.client(
        "ec2",
        region_name=region
    )

    response = safe_call(
        lambda: ec2.describe_volumes(),
        {"Volumes": []}
    )

    resources = []

    for volume in response.get(
        "Volumes",
        []
    ):

        attachments = volume.get(
            "Attachments",
            []
        )

        attached_instance = None

        if attachments:
            attached_instance = attachments[0].get(
                "InstanceId"
            )

        resources.append({
            "resource_id":
                volume["VolumeId"],

            "resource_type":
                "EBS",

            "region":
                region,

            "status":
                volume.get("State"),

            "size_gb":
                volume.get("Size"),

            "volume_type":
                volume.get("VolumeType"),

            "attached_instance":
                attached_instance,

            "created":
                str(volume.get("CreateTime")),
        })

    return resources


# ============================================================
# Elastic IP
# ============================================================

def get_elastic_ips(region):

    ec2 = boto3.client(
        "ec2",
        region_name=region
    )

    response = safe_call(
        lambda: ec2.describe_addresses(),
        {"Addresses": []}
    )

    resources = []

    for address in response.get(
        "Addresses",
        []
    ):

        associated = bool(
            address.get("InstanceId")
            or address.get(
                "NetworkInterfaceId"
            )
        )

        resources.append({
            "resource_id":
                address.get("AllocationId"),

            "resource_type":
                "Elastic IP",

            "region":
                region,

            "status":
                (
                    "associated"
                    if associated
                    else "unassociated"
                ),

            "public_ip":
                address.get("PublicIp"),

            "instance_id":
                address.get("InstanceId"),

            "network_interface":
                address.get(
                    "NetworkInterfaceId"
                ),
        })

    return resources


# ============================================================
# NAT Gateway
# ============================================================

def get_nat_gateways(region):

    ec2 = boto3.client(
        "ec2",
        region_name=region
    )

    response = safe_call(
        lambda: ec2.describe_nat_gateways(
            Filter=[
                {
                    "Name": "state",
                    "Values": [
                        "available",
                        "pending",
                        "failed"
                    ]
                }
            ]
        ),
        {"NatGateways": []}
    )

    resources = []

    for gateway in response.get(
        "NatGateways",
        []
    ):

        resources.append({
            "resource_id":
                gateway["NatGatewayId"],

            "resource_type":
                "NAT Gateway",

            "region":
                region,

            "status":
                gateway.get("State"),

            "vpc_id":
                gateway.get("VpcId"),

            "subnet_id":
                gateway.get("SubnetId"),

            "created":
                str(gateway.get("CreateTime")),
        })

    return resources


# ============================================================
# RDS
# ============================================================

def get_rds_instances(region):

    rds = boto3.client(
        "rds",
        region_name=region
    )

    response = safe_call(
        lambda: rds.describe_db_instances(),
        {"DBInstances": []}
    )

    resources = []

    for database in response.get(
        "DBInstances",
        []
    ):

        resources.append({
            "resource_id":
                database[
                    "DBInstanceIdentifier"
                ],

            "resource_type":
                "RDS",

            "region":
                region,

            "status":
                database.get(
                    "DBInstanceStatus"
                ),

            "engine":
                database.get("Engine"),

            "instance_class":
                database.get(
                    "DBInstanceClass"
                ),

            "storage_gb":
                database.get(
                    "AllocatedStorage"
                ),
        })

    return resources


# ============================================================
# Lambda
# ============================================================

def get_lambda_functions(region):

    lambda_client = boto3.client(
        "lambda",
        region_name=region
    )

    response = safe_call(
        lambda: lambda_client.list_functions(),
        {"Functions": []}
    )

    resources = []

    for function in response.get(
        "Functions",
        []
    ):

        resources.append({
            "resource_id":
                function["FunctionArn"],

            "resource_type":
                "Lambda",

            "name":
                function.get(
                    "FunctionName"
                ),

            "region":
                region,

            "runtime":
                function.get("Runtime"),

            "memory_mb":
                function.get(
                    "MemorySize"
                ),

            "last_modified":
                function.get(
                    "LastModified"
                ),
        })

    return resources


# ============================================================
# DynamoDB
# ============================================================

def get_dynamodb_tables(region):

    dynamodb = boto3.client(
        "dynamodb",
        region_name=region
    )

    response = safe_call(
        lambda: dynamodb.list_tables(),
        {"TableNames": []}
    )

    resources = []

    for table_name in response.get(
        "TableNames",
        []
    ):

        details = safe_call(
            lambda name=table_name:
            dynamodb.describe_table(
                TableName=name
            ),
            {}
        )

        table = details.get(
            "Table"
        )

        if not table:
            continue

        resources.append({
            "resource_id":
                table["TableArn"],

            "resource_type":
                "DynamoDB",

            "name":
                table["TableName"],

            "region":
                region,

            "status":
                table.get(
                    "TableStatus"
                ),

            "created":
                str(
                    table.get(
                        "CreationDateTime"
                    )
                ),

            "item_count":
                table.get(
                    "ItemCount"
                ),
        })

    return resources


# ============================================================
# S3
# ============================================================

def get_s3_buckets():

    s3 = boto3.client("s3")

    response = safe_call(
        lambda: s3.list_buckets(),
        {"Buckets": []}
    )

    resources = []

    for bucket in response.get(
        "Buckets",
        []
    ):

        bucket_name = bucket["Name"]

        try:

            location = s3.get_bucket_location(
                Bucket=bucket_name
            )

            region = location.get(
                "LocationConstraint"
            )

            if not region:
                region = "us-east-1"

        except ClientError as error:

            print(
                f"Could not determine region "
                f"for {bucket_name}: {error}"
            )

            region = "unknown"

        resources.append({
            "resource_id":
                bucket_name,

            "resource_type":
                "S3",

            "name":
                bucket_name,

            "region":
                region,

            "created":
                str(
                    bucket.get(
                        "CreationDate"
                    )
                ),

            "status":
                "active",
        })

    return resources


# ============================================================
# CloudFront
# ============================================================

def get_cloudfront_distributions():

    cloudfront = boto3.client(
        "cloudfront"
    )

    response = safe_call(
        lambda:
        cloudfront.list_distributions(),
        {}
    )

    distribution_list = response.get(
        "DistributionList",
        {}
    )

    resources = []

    for distribution in distribution_list.get(
        "Items",
        []
    ):

        resources.append({
            "resource_id":
                distribution["Id"],

            "resource_type":
                "CloudFront",

            "region":
                "global",

            "status":
                distribution.get(
                    "Status"
                ),

            "domain":
                distribution.get(
                    "DomainName"
                ),

            "enabled":
                distribution.get(
                    "Enabled"
                ),
        })

    return resources


# ============================================================
# Idle Detection
# ============================================================

def detect_idle(resource):

    resource_type = resource.get(
        "resource_type"
    )

    status = resource.get(
        "status"
    )

    # Unattached EBS
    if resource_type == "EBS":

        if not resource.get(
            "attached_instance"
        ):

            return {
                "idle": True,
                "idle_score": 100,
                "idle_reason":
                    "EBS volume is unattached",
                "recommendation":
                    "Review and delete if no longer required"
            }

    # Unassociated Elastic IP
    if resource_type == "Elastic IP":

        if status == "unassociated":

            return {
                "idle": True,
                "idle_score": 100,
                "idle_reason":
                    "Elastic IP is unassociated",
                "recommendation":
                    "Release if no longer required"
            }

    # Stopped EC2
    if resource_type == "EC2":

        if status == "stopped":

            return {
                "idle": True,
                "idle_score": 90,
                "idle_reason":
                    "EC2 instance is stopped",
                "recommendation":
                    "Review whether the instance is still required"
            }

    # Stopped RDS
    if resource_type == "RDS":

        if status == "stopped":

            return {
                "idle": True,
                "idle_score": 90,
                "idle_reason":
                    "RDS instance is stopped",
                "recommendation":
                    "Review whether the database is still required"
            }

    # Failed NAT Gateway
    if resource_type == "NAT Gateway":

        if status == "failed":

            return {
                "idle": True,
                "idle_score": 100,
                "idle_reason":
                    "NAT Gateway has failed",
                "recommendation":
                    "Review and remove if no longer required"
            }

    return {
        "idle": False,
        "idle_score": 0,
        "idle_reason": None,
        "recommendation": None
    }


# ============================================================
# Regional Scan
# ============================================================

def scan_region(region):

    print()
    print(f"Scanning region: {region}")

    resources = []

    print("  EC2")
    resources.extend(
        get_ec2_instances(region)
    )

    print("  EBS")
    resources.extend(
        get_ebs_volumes(region)
    )

    print("  Elastic IP")
    resources.extend(
        get_elastic_ips(region)
    )

    print("  NAT Gateway")
    resources.extend(
        get_nat_gateways(region)
    )

    print("  RDS")
    resources.extend(
        get_rds_instances(region)
    )

    print("  Lambda")
    resources.extend(
        get_lambda_functions(region)
    )

    print("  DynamoDB")
    resources.extend(
        get_dynamodb_tables(region)
    )

    return resources


# ============================================================
# Complete Scan
# ============================================================

def scan_resources():

    resources = []

    regions = get_enabled_regions()

    print()
    print(
        f"Enabled regions found: {len(regions)}"
    )

    for region in regions:

        regional_resources = scan_region(
            region
        )

        resources.extend(
            regional_resources
        )

    # Global services
    print()
    print("Scanning global services")

    print("  S3")
    resources.extend(
        get_s3_buckets()
    )

    print("  CloudFront")
    resources.extend(
        get_cloudfront_distributions()
    )

    # Idle analysis
    for resource in resources:

        resource.update(
            detect_idle(resource)
        )

    return resources


# ============================================================
# Summary
# ============================================================

def create_summary(resources):

    summary = {}

    for resource in resources:

        resource_type = resource[
            "resource_type"
        ]

        summary[resource_type] = (
            summary.get(
                resource_type,
                0
            ) + 1
        )

    idle_count = sum(
        1
        for resource in resources
        if resource.get("idle")
    )

    summary["idle_resources"] = idle_count

    return summary


# ============================================================
# Handler
# ============================================================

def handler(event=None, context=None):

    resources = scan_resources()

    summary = create_summary(
        resources
    )

    return {
        "statusCode": 200,
        "total_resources": len(
            resources
        ),
        "summary": summary,
        "resources": resources,
    }


# ============================================================
# Local Execution
# ============================================================

if __name__ == "__main__":

    result = handler()

    print()
    print("=" * 70)
    print(
        "             CloudSentinel AWS Scan"
    )
    print("=" * 70)

    print()
    print(
        f"Total resources: "
        f"{result['total_resources']}"
    )

    print()
    print("Resource Summary:")

    for resource_type, count in result[
        "summary"
    ].items():

        print(
            f"  {resource_type:<25} {count}"
        )

    print()
    print("Resources:")

    for resource in result[
        "resources"
    ]:

        idle_status = (
            "IDLE"
            if resource.get("idle")
            else "ACTIVE"
        )

        print(
            f"  {resource['resource_type']:<15} "
            f"{resource['region']:<15} "
            f"{resource['resource_id']:<60} "
            f"{idle_status}"
        )

    print()
    print("=" * 70)