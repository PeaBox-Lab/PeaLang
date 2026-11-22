// Example: Using the PeaLang Browser SDK
//
// Generate the SDK:
//   pea sdk generate browser ./sdk
//
// Include in your HTML:
//   <script src="./sdk/src/client.ts"></script>
//   or bundle with a bundler (webpack, vite, etc.)

import { PeaLangClient } from './sdk/src/client';

async function main() {
  const client = new PeaLangClient('http://localhost:8080');

  // Health check
  const health = await client.health();
  console.log('Health:', health);

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
