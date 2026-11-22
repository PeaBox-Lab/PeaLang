// Example: Using the PeaLang Node.js SDK
// Generate with: pea sdk generate node ./sdk
//
// Then compile and run:
//   npx tsc ./sdk/src/index.ts
//   node example.js

import { PeaClient } from './sdk/src/index';

async function main() {
  const client = new PeaClient('http://localhost:8080');

  // Health check
  const health = await client.health();
  console.log('Health:', JSON.stringify(health));

  // Invoke add function from math_utils module
  const result1 = await client.invoke('math_utils', 'add', [3, 7]);
  console.log('3 + 7 =', result1);

  // Invoke multiply function
  const result2 = await client.invoke('math_utils', 'multiply', [4, 5]);
  console.log('4 * 5 =', result2);

  // Invoke greet function
  const result3 = await client.invoke('math_utils', 'greet', ['World']);
  console.log(result3);
}

main().catch(console.error);
