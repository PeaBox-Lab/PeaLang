// Example: Using the PeaLang Java SDK
//
// Generate the SDK:
//   pea sdk generate java ./sdk
//
// Build:
//   cd ./sdk && mvn package
//
// Run:
//   java -cp target/pealang-java-sdk-1.0.0.jar:... com.pealang.SdkClientExample

import com.pealang.SdkClient;

public class SdkClientExample {
    public static void main(String[] args) throws Exception {
        SdkClient client = new SdkClient("http://localhost:8080");

        // Health check
        String health = client.health();
        System.out.println("Health: " + health);

        // Invoke add function from math_utils module
        String result1 = client.invoke("math_utils", "add", "3", "7");
        System.out.println("3 + 7 = " + result1);

        // Invoke multiply function
        String result2 = client.invoke("math_utils", "multiply", "4", "5");
        System.out.println("4 * 5 = " + result2);

        // Invoke greet function
        String result3 = client.invoke("math_utils", "greet", "World");
        System.out.println(result3);
    }
}
