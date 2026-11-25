use reqwest::Client;
use serde::{Serialize, Deserialize};

#[derive(Serialize)]
struct InvokeRequest {
    module: String,
    function: String,
    args: Vec<String>,
}

pub struct SdkClient {
    client: Client,
    base_url: String,
}

impl SdkClient {
    pub fn new(base_url: &str) -> Self {
        SdkClient {
            client: Client::new(),
            base_url: base_url.trim_end_matches('/').to_string(),
        }
    }

    pub async fn health(&self) -> Result<String, reqwest::Error> {
        let response = self.client
            .get(&format!("{}/health", self.base_url))
            .send()
            .await?;
        if !response.status().is_success() {
            return Err(reqwest::Error::status(response.status()));
        }
        response.text().await
    }

    pub async fn add(&self, a: &str, b: &str) -> Result<String, reqwest::Error> {
        let payload = InvokeRequest {
            module: "PeaModule".to_string(),
            function: "add".to_string(),
            args: vec![a.to_string(), b.to_string()],
        };
        let response = self.client
            .post(&format!("{}/v1/invoke", self.base_url))
            .json(&payload)
            .send()
            .await?;
        if !response.status().is_success() {
            return Err(reqwest::Error::status(response.status()));
        }
        response.text().await
    }

}
