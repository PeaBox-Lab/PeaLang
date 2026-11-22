// Example: Using the PeaLang Rust SDK
//
// Generate the SDK:
//   pea sdk generate rust ./sdk
//
// Build:
//   cd ./sdk && cargo build
//
// Run:
//   cargo run

use pealang_rust_sdk::SdkClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = SdkClient::new("http://localhost:8080");

    // Health check
    let health = client.health().await?;
    println!("Health: {}", health);

    // Invoke add function from math_utils module
    let result1 = client.invoke("math_utils", "add", vec!["3".to_string(), "7".to_string()]).await?;
    println!("3 + 7 = {}", result1);

    // Invoke multiply function
    let result2 = client.invoke("math_utils", "multiply", vec!["4".to_string(), "5".to_string()]).await?;
    println!("4 * 5 = {}", result2);

    // Invoke greet function
    let result3 = client.invoke("math_utils", "greet", vec!["World".to_string()]).await?;
    println!("{}", result3);

    Ok(())
}
