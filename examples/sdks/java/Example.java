// Example: Using the PeaLang Java SDK
//
// Generate the SDK:
//   pea sdk generate java ./sdk
//
// Build:
//   cd ./sdk && mvn package
//
// Run:
//   java -cp 'target/pealang-java-sdk-*.jar:target/classes' io.pealang.client.SdkClientExample

import io.pealang.client.SdkClient;

public class SdkClientExample {
    public static void main(String[] args) throws Exception {
        SdkClient client = new SdkClient("http://localhost:8080");

        String health = client.health();
        System.out.println("Health: " + health);

        String added = client.invoke("math_utils", "add", java.util.List.of("3", "7"));
        System.out.println("3 + 7 = " + added);

        String greeted = client.invoke("math_utils", "greet", java.util.List.of("World"));
        System.out.println(greeted);
    }
}
