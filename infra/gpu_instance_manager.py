import boto3
import argparse
import time
import sys


class GPUInstanceManager:
    def __init__(self, region="us-east-1"):
        self.ec2 = boto3.client("ec2", region_name=region)
        self.region = region
        self.config = self._load_config()

    @staticmethod
    def _load_config():
        return {
            "DEFAULT": {
                "MaxHourlyBudget": "1.0",
                "MaxMonthlyBudget": "100.0",
                "AutoShutdownHours": "4",
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

    def request_spot_instance(self, instance_type="g4dn.xlarge", ami_id=None):
        """Request a spot instance with budget checks and auto-shutdown"""
        if not self.check_budget_compliance(instance_type):
            sys.exit(1)

        if not ami_id:
            ssm = boto3.client("ssm", region_name=self.region)
            ami_id = ssm.get_parameter(
                Name="/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
            )["Parameter"]["Value"]

        try:
            # Create startup script with auto-shutdown
            user_data = f"""#!/bin/bash
            shutdown -h +{int(self.config['DEFAULT']['AutoShutdownHours']) * 60}
            mkfs -t xfs /dev/xvdf
            mkdir -p /opt/ollama
            mount /dev/xvdf /opt/ollama
            chown -R ec2-user:ec2-user /opt/ollama
            echo '/dev/xvdf /opt/ollama xfs defaults 0 0' >> /etc/fstab
            """

            response = self.ec2.request_spot_instances(
                InstanceCount=1,
                Type="persistent",
                LaunchSpecification={
                    "ImageId": ami_id,
                    "InstanceType": instance_type,
                    "UserData": user_data.encode("utf-8").hex(),
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/xvda",
                            "Ebs": {
                                "VolumeSize": 30,
                                "VolumeType": "gp3",
                                "DeleteOnTermination": True,
                            },
                        },
                        {
                            "DeviceName": "/dev/xvdf",
                            "Ebs": {
                                "VolumeSize": 100,
                                "VolumeType": "gp3",
                                "DeleteOnTermination": True,
                            },
                        },
                    ],
                    "TagSpecifications": [
                        {
                            "ResourceType": "instance",
                            "Tags": [
                                {"Key": "Name", "Value": "LLM-Development"},
                                {
                                    "Key": "AutoShutdown",
                                    "Value": self.config["DEFAULT"]["AutoShutdownHours"],
                                },
                                {"Key": "CreatedBy", "Value": "GPUInstanceManager"},
                            ],
                        }
                    ],
                },
            )

            request_id = response["SpotInstanceRequests"][0]["SpotInstanceRequestId"]
            print(f"Spot request created: {request_id}")

            instance_id = self._wait_for_spot_instance(request_id)
            if instance_id:
                print(f"Spot instance created: {instance_id}")
                self._wait_for_state(instance_id, "running")
                response = self.ec2.describe_instances(InstanceIds=[instance_id])
                public_ip = response["Reservations"][0]["Instances"][0].get("PublicIpAddress")

                print("\n=== IMPORTANT INFORMATION ===")
                print(f"Instance ID: {instance_id}")
                print(f"Public IP: {public_ip}")
                print(f"\nConnect using:")
                print(f"ssh -i your-key.pem ec2-user@{public_ip}")
                print(
                    f"\nAuto-shutdown scheduled in {self.config['DEFAULT']['AutoShutdownHours']} hours"
                )
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
        print("Waiting for spot instance...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.ec2.describe_spot_instance_requests(SpotInstanceRequestIds=[request_id])
            status = response["SpotInstanceRequests"][0]["Status"]["Code"]

            if status == "fulfilled":
                return response["SpotInstanceRequests"][0]["InstanceId"]

            print(f"Current status: {status}... waiting", end="\r")
            time.sleep(5)

        print("\nTimeout waiting for spot instance")
        sys.exit(1)

    def _wait_for_state(self, instance_id, target_state, timeout=300):
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            current_state = response["Reservations"][0]["Instances"][0]["State"]["Name"]

            if current_state == target_state:
                print(f"\nInstance {instance_id} is {target_state}")
                return

            print(f"Current state: {current_state}... waiting", end="\r")
            time.sleep(5)

        print(f"\nTimeout waiting for state {target_state}")
        sys.exit(1)

    def start_instance(self, instance_id):
        """Start an existing instance with budget check"""
        instance_type = self.ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0][
            "Instances"
        ][0]["InstanceType"]

        if not self.check_budget_compliance(instance_type):
            sys.exit(1)

        try:
            self.ec2.start_instances(InstanceIds=[instance_id])
            print(f"Starting instance {instance_id}")
            self._wait_for_state(instance_id, "running")

            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            public_ip = response["Reservations"][0]["Instances"][0].get("PublicIpAddress")
            print(f"\nInstance ready! Connect using:\nssh -i your-key.pem ec2-user@{public_ip}")
            print(
                f"\nDon't forget: Instance will auto-shutdown in {self.config['DEFAULT']['AutoShutdownHours']} hours"
            )

        except Exception as e:
            print(f"Error starting instance: {e}")
            sys.exit(1)

    def stop_instance(self, instance_id):
        try:
            self.ec2.stop_instances(InstanceIds=[instance_id])
            print(f"Stopping instance {instance_id}")
            self._wait_for_state(instance_id, "stopped")
            print("\nInstance stopped successfully. Remember to:")
            print("1. Check AWS Console to confirm instance is stopped")
            print("2. Note down instance ID for future starts")
        except Exception as e:
            print(f"Error stopping instance: {e}")
            sys.exit(1)

    def get_spot_price(self, instance_type="g4dn.xlarge"):
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
        EC2 Spot Instance Manager for LLM Development

        Common workflows:
        1. Check price:    gpu_instance_manager.py price
        2. Start new:      gpu_instance_manager.py request
        3. Stop instance:  gpu_instance_manager.py stop --instance-id i-1234xyz
        4. Resume work:    gpu_instance_manager.py start --instance-id i-1234xyz
        """
    )
    parser.add_argument("action", choices=["start", "stop", "price", "request"])
    parser.add_argument("--instance-id", required=False)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--instance-type", default="g4dn.xlarge")
    parser.add_argument("--ami-id", help="Optional AMI ID")
    args = parser.parse_args()

    manager = GPUInstanceManager(args.region)

    if args.action == "request":
        manager.request_spot_instance(args.instance_type, args.ami_id)
    elif args.action == "start":
        if not args.instance_id:
            print("Error: --instance-id required for start action")
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
            print(
                f"Estimated cost for {manager.config['DEFAULT']['AutoShutdownHours']} hours: ${price * float(manager.config['DEFAULT']['AutoShutdownHours']):.2f}"
            )


if __name__ == "__main__":
    main()
