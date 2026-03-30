import * as lucide from 'lucide-react';
['Target', 'Activity', 'RefreshCw', 'Clock', 'Info', 'ArrowUpRight', 'ArrowDownRight', 'TriangleAlert'].forEach(name => {
  if (!lucide[name]) console.error('MISSING:', name);
  else console.log('OK:', name);
});
