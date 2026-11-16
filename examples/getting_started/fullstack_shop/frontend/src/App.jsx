import { useEffect, useState } from 'react';

export default function App() {
  const [health, setHealth] = useState(null);
  useEffect(() => {
    fetch('http://localhost:8000/health').then(r => r.json()).then(setHealth).catch(() => setHealth({error:'backend unreachable'}));
  }, []);
  return <pre>{JSON.stringify(health, null, 2)}</pre>;
}
