const fs = require('fs');
const content = fs.readFileSync('src/app/approvals/[id]/page.tsx', 'utf8');
console.log('First 50 chars:', JSON.stringify(content.slice(0, 50)));
console.log('First char code:', content.charCodeAt(0));