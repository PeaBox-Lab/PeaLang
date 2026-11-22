// Example: Using the PeaLang C# SDK
//
// Generate the SDK:
//   pea sdk generate csharp ./sdk
//
// Build:
//   cd ./sdk && dotnet build
//
// Run:
//   dotnet run --project ./sdk

using PeaLang;

class Example
{
    static void Main()
    {
        var client = new SdkClient("http://localhost:8080");

        // Health check
        string health = client.Health();
        System.Console.WriteLine("Health: " + health);

        // Invoke add function from math_utils module
        string result1 = client.Invoke("math_utils", "add", "3", "7");
        System.Console.WriteLine("3 + 7 = " + result1);

        // Invoke multiply function
        string result2 = client.Invoke("math_utils", "multiply", "4", "5");
        System.Console.WriteLine("4 * 5 = " + result2);

        // Invoke greet function
        string result3 = client.Invoke("math_utils", "greet", "World");
        System.Console.WriteLine(result3);
    }
}
