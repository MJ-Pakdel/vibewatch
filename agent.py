from strands import Agent
import os

def main():
    try:
        # Create an agent with default Bedrock model
        # Note: This requires AWS credentials and Bedrock access
        agent = Agent()
        
        # Ask the agent a question
        response = agent("Tell me about agentic AI")
        print("Agent Response:")
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use strands-agents, you need:")
        print("1. AWS credentials configured")
        print("2. Access to AWS Bedrock service")
        print("3. Proper IAM permissions for Bedrock")
        print("\nTo set up AWS credentials:")
        print("aws configure")
        print("# Enter your AWS Access Key ID, Secret Access Key, and region")
        print("\nOr set environment variables:")
        print("export AWS_ACCESS_KEY_ID='your-access-key'")
        print("export AWS_SECRET_ACCESS_KEY='your-secret-key'")
        print("export AWS_DEFAULT_REGION='us-east-1'")

if __name__ == "__main__":
    main()
