# Example: Using the PeaLang Go SDK

# Generate the SDK:
#   pea sdk generate go ./sdk

# Build and run:
#   cd ./sdk
#   go build -o pea-client ./example.go
#   ./pea-client

package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

type Client struct {
	baseURL string
	http    *http.Client
}

func NewClient(baseURL string) *Client {
	return &Client{baseURL: strings.TrimRight(baseURL, "/"), http: &http.Client{}}
}

func (c *Client) Health() (string, error) {
	resp, err := c.http.Get(c.baseURL + "/health")
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	return string(body), nil
}

func (c *Client) Invoke(module, function string, args ...string) (string, error) {
	payload, _ := json.Marshal(map[string]interface{}{
		"module":   module,
		"function": function,
		"args":     args,
	})
	resp, err := c.http.Post(c.baseURL+"/v1/invoke", "application/json", strings.NewReader(string(payload)))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	return string(body), nil
}

func main() {
	client := NewClient("http://localhost:8080")

	health, _ := client.Health()
	fmt.Println("Health:", health)

	result1, _ := client.Invoke("math_utils", "add", "3", "7")
	fmt.Println("3 + 7 =", result1)

	result2, _ := client.Invoke("math_utils", "multiply", "4", "5")
	fmt.Println("4 * 5 =", result2)

	result3, _ := client.Invoke("math_utils", "greet", "World")
	fmt.Println(result3)
}
