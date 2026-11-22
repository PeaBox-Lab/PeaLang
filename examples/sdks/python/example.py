# Example: Using the PeaLang Python SDK
#
# Generate the SDK:
#   pea sdk generate python ./sdk
#
# Run:
#   python example.py

from sdk.pealang.client import PeaClient


def main():
    client = PeaClient("http://localhost:8080")

    # Health check
    health = client.health()
    print("Health:", health)

    # Invoke add function from math_utils module
    result1 = client.invoke("math_utils", "add", [3, 7])
    print("3 + 7 =", result1)

    # Invoke multiply function
    result2 = client.invoke("math_utils", "multiply", [4, 5])
    print("4 * 5 =", result2)

    # Invoke greet function
    result3 = client.invoke("math_utils", "greet", ["World"])
    print(result3)


if __name__ == "__main__":
    main()
