import boto3
import argparse
import time
import sys
import os
import base64


class GPUInstanceManager:
    def __init__(self, region, key_name):
        self.ec2 = boto3.client("ec2", region_name=region)
        self.region = region
        self.config = self._load_config()
        self.key_name = key_name

    @staticmethod
    def _load_config():
        return {
            "DEFAULT": {
                "MaxHourlyBudget": "1.0",
                "MaxMonthlyBudget": "100.0",
                "AlertEmail": "",
            }
        }

    def check_budget_compliance(self, instance_type):
        """Check if launching instance stays within budget"""
        spot_price = self.get_spot_price(instance_type)
        if not spot_price:
            return False

        max_hourly = float(self.config["DEFAULT"]["MaxHourlyBudget"])
        if spot_price > max_hourly:
            print(f"WARNING: Spot price ${spot_price}/hour exceeds budget ${max_hourly}/hour")
            response = input("Continue anyway? (y/N): ")
            return response.lower() == "y"
        return True

    def request_spot_instance(
        self, instance_type="g4dn.xlarge", ami_id=None, security_group_ids=None, subnet_id=None
    ):
        """Request a new persistent spot instance"""
        if not self.check_budget_compliance(instance_type):
            sys.exit(1)

        if not ami_id:
            ssm = boto3.client("ssm", region_name=self.region)
            ami_id = ssm.get_parameter(
                Name="/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
            )["Parameter"]["Value"]

        if not security_group_ids:
            print("Warning: No security groups specified. This may limit access to your instance.")
            security_group_ids = []

        if not subnet_id:
            print("Warning: No subnet specified. Using default subnet in the VPC.")

        try:
            user_data = """#!/bin/bash
exec 1> >(logger -s -t $(basename $0)) 2>&1

echo "Starting volume mount script"

# List all block devices for debugging
echo "Available block devices:"
lsblk --json
ls -l /dev/nvme*

# Find the NVMe device for data storage
echo "Searching for NVMe device..."
DATA_DEVICE=$(lsblk --json | python3 -c '
import json, sys
devices = json.load(sys.stdin)["blockdevices"]
for dev in devices:
    print(f"Checking device: {dev}", file=sys.stderr)
    if (dev["type"] == "disk" and 
        dev["name"].startswith("nvme") and 
        not dev.get("children") and
        dev["name"] != "nvme0n1"):  # Skip the root device
        print(f"/dev/{dev[\"name\"]}")  # Fixed quotes in f-string
        break
')

echo "Found device: $DATA_DEVICE"

if [ -z "$DATA_DEVICE" ]; then
    echo "Error: Could not find appropriate NVMe device"
    exit 1
fi

echo "Creating XFS filesystem on $DATA_DEVICE"
mkfs -t xfs $DATA_DEVICE

echo "Creating mount point /opt/ollama"
mkdir -p /opt/ollama

echo "Mounting device"
mount $DATA_DEVICE /opt/ollama

echo "Setting permissions"
chown -R ubuntu:ubuntu /opt/ollama

echo "Adding to fstab"
echo "$DATA_DEVICE /opt/ollama xfs defaults 0 0" >> /etc/fstab

echo "Mount complete - current mounts:"
df -h
"""

            user_data_encoded = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")
            tags = [
                {"Key": "Name", "Value": "LLM-Development"},
                {"Key": "CreatedBy", "Value": "GPUInstanceManager"},
            ]

            launch_specification = {
                "ImageId": ami_id,
                "InstanceType": instance_type,
                "KeyName": self.key_name,
                "UserData": user_data_encoded,
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/sda1",
                        "Ebs": {
                            "VolumeSize": 100,
                            "VolumeType": "gp3",
                            "DeleteOnTermination": True,
                        },
                    },
                    {
                        "DeviceName": "/dev/sdf",
                        "Ebs": {
                            "VolumeSize": 100,
                            "VolumeType": "gp3",
                            "DeleteOnTermination": True,
                        },
                    },
                ],
            }

            if security_group_ids:
                launch_specification["SecurityGroupIds"] = security_group_ids

            if subnet_id:
                launch_specification["SubnetId"] = subnet_id

            # Request a persistent spot instance
            response = self.ec2.request_spot_instances(
                InstanceCount=1,
                Type="persistent",  # Changed to persistent
                TagSpecifications=[{"ResourceType": "spot-instances-request", "Tags": tags}],
                LaunchSpecification=launch_specification,
            )

            request_id = response["SpotInstanceRequests"][0]["SpotInstanceRequestId"]
            print(f"Persistent spot request created: {request_id}")

            instance_id = self._wait_for_spot_instance(request_id)
            if instance_id:
                print(f"Spot instance created: {instance_id}")
                self._wait_for_state(instance_id, "running")

                # Tag the instance itself
                self.ec2.create_tags(Resources=[instance_id], Tags=tags)

                response = self.ec2.describe_instances(InstanceIds=[instance_id])
                public_ip = response["Reservations"][0]["Instances"][0].get("PublicIpAddress")

                print("\n=== IMPORTANT INFORMATION ===")
                print(f"Instance ID: {instance_id}")
                print(f"Public IP: {public_ip}")
                print(f"\nConnect using:")
                print(f"ssh -i {self.key_name}.pem ubuntu@{public_ip}")
                print(f"Current spot price: ${self.get_spot_price(instance_type)}/hour")
                print("\nTo start working with Ollama:")
                print("1. cd /opt/ollama")
                print("2. curl https://ollama.ai/install.sh | sh")
                print("3. ollama run mistral   # or any other model")
                print("\n=== COST MANAGEMENT ===")
                print("• Always stop instance when not in use")
                print("• Check spot prices before starting")
                print("• Monitor usage in AWS Console")
                print("===========================")

                return instance_id

        except Exception as e:
            print(f"Error requesting spot instance: {e}")
            sys.exit(1)

    def _wait_for_spot_instance(self, request_id, timeout=300):
        """Wait for spot instance request to be fulfilled"""
        print("Waiting for spot instance...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.ec2.describe_spot_instance_requests(
                    SpotInstanceRequestIds=[request_id]
                )
                status = response["SpotInstanceRequests"][0]["Status"]["Code"]

                if status == "fulfilled":
                    return response["SpotInstanceRequests"][0]["InstanceId"]

                if status in ["schedule-expired", "canceled-before-fulfillment", "bad-parameters"]:
                    print(f"\nSpot request failed with status: {status}")
                    return None

                print(f"Current status: {status}... waiting", end="\r")
                time.sleep(5)

            except self.ec2.exceptions.ClientError as e:
                print(f"\nError checking spot request status: {e}")
                return None

        print("\nTimeout waiting for spot instance")
        return None

    def _wait_for_state(self, instance_id, target_state, timeout=300):
        """Wait for instance to reach desired state"""
        print(f"Waiting for instance to become {target_state}...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.ec2.describe_instances(InstanceIds=[instance_id])
                current_state = response["Reservations"][0]["Instances"][0]["State"]["Name"]

                if current_state == target_state:
                    print(f"\nInstance {instance_id} is {target_state}")
                    return True

                print(f"Current state: {current_state}... waiting", end="\r")
                time.sleep(5)

            except self.ec2.exceptions.ClientError as e:
                print(f"\nError checking instance state: {e}")
                return False

        print(f"\nTimeout waiting for state {target_state}")
        return False

    def start_instance(self, instance_id):
        """Start an existing stopped instance"""
        try:
            # Check if instance exists and get its configuration
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]

            if instance["State"]["Name"] == "running":
                print(f"Instance {instance_id} is already running")
                return

            # Check budget before starting
            if not self.check_budget_compliance(instance["InstanceType"]):
                sys.exit(1)

            # Start the instance
            self.ec2.start_instances(InstanceIds=[instance_id])
            print(f"Starting instance {instance_id}")

            if self._wait_for_state(instance_id, "running"):
                response = self.ec2.describe_instances(InstanceIds=[instance_id])
                public_ip = response["Reservations"][0]["Instances"][0].get("PublicIpAddress")
                print(f"\nInstance ready! Connect using:")
                print(f"ssh -i {self.key_name}.pem ubuntu@{public_ip}")

        except self.ec2.exceptions.ClientError as e:
            if "InvalidInstanceID.NotFound" in str(e):
                print(f"Instance {instance_id} not found")
            else:
                print(f"Error starting instance: {e}")
            sys.exit(1)

    def stop_instance(self, instance_id):
        """Stop instance without canceling the persistent spot request"""
        try:
            print(f"Stopping instance {instance_id}")
            self.ec2.stop_instances(InstanceIds=[instance_id])
            self._wait_for_state(instance_id, "stopped")

            print("\nInstance stopped successfully")
            print(
                f"To restart it later, use: python gpu_manager.py start --instance-id {instance_id}"
            )

        except Exception as e:
            print(f"Error stopping instance: {e}")
            sys.exit(1)

    def get_spot_price(self, instance_type="g4dn.xlarge"):
        """Get current spot price for instance type"""
        try:
            response = self.ec2.describe_spot_price_history(
                InstanceTypes=[instance_type], ProductDescriptions=["Linux/UNIX"], MaxResults=1
            )
            if response["SpotPriceHistory"]:
                return float(response["SpotPriceHistory"][0]["SpotPrice"])
            return None
        except Exception as e:
            print(f"Error getting spot price: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description="""
        EC2 GPU Spot Instance Manager

        Common workflows:
        1. Check price:    gpu_instance_manager.py price
        2. Start new:      gpu_instance_manager.py request --key-name my-key --security-group-ids sg-xxx --subnet-id subnet-xxx
        3. Stop instance:  gpu_instance_manager.py stop --instance-id i-1234xyz
        4. Resume work:    gpu_instance_manager.py start --instance-id i-1234xyz --key-name my-key
        """
    )
    parser.add_argument("action", choices=["start", "stop", "price", "request"])
    parser.add_argument("--instance-id", required=False)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--instance-type", default="g4dn.xlarge")
    parser.add_argument("--ami-id", help="Optional AMI ID")
    parser.add_argument("--key-name", help="Name of your AWS key pair (without .pem extension)")
    parser.add_argument("--security-group-ids", help="Comma-separated list of security group IDs")
    parser.add_argument("--subnet-id", help="Subnet ID for the instance")
    args = parser.parse_args()

    manager = GPUInstanceManager(args.region, args.key_name)

    if args.action == "request":
        if not args.key_name:
            print("Error: --key-name required for request action")
            sys.exit(1)

        security_group_ids = args.security_group_ids.split(",") if args.security_group_ids else None
        manager.request_spot_instance(
            args.instance_type, args.ami_id, security_group_ids, args.subnet_id
        )
    elif args.action == "start":
        if not args.instance_id:
            print("Error: --instance-id required for start action")
            sys.exit(1)
        if not args.key_name:
            print("Error: --key-name required for start action")
            sys.exit(1)
        manager.start_instance(args.instance_id)
    elif args.action == "stop":
        if not args.instance_id:
            print("Error: --instance-id required for stop action")
            sys.exit(1)
        manager.stop_instance(args.instance_id)
    elif args.action == "price":
        price = manager.get_spot_price(args.instance_type)
        if price:
            print(f"Current spot price: ${price}/hour")


if __name__ == "__main__":
    main()
