<?php
// Example: Using the PeaLang PHP SDK
//
// Generate the SDK:
//   pea sdk generate php ./sdk
//   cd ./sdk && composer install
//
// Run:
//   php example.php

require __DIR__ . '/sdk/vendor/autoload.php';

use PeaLang\SdkClient;

$client = new SdkClient('http://localhost:8080');

// Health check
$health = $client->health();
echo "Health: $health\n";

// Invoke add function from math_utils module
$result1 = $client->invoke('math_utils', 'add', ['3', '7']);
echo "3 + 7 = $result1\n";

// Invoke multiply function
$result2 = $client->invoke('math_utils', 'multiply', ['4', '5']);
echo "4 * 5 = $result2\n";

// Invoke greet function
$result3 = $client->invoke('math_utils', 'greet', ['World']);
echo "$result3\n";
