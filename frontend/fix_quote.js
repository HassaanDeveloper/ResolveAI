const fs = require('fs');
const content = fs.readFileSync('src/app/approvals/[id]/page.tsx', 'utf8');
console.log('First 50 chars:', JSON.stringify(content.slice(0, 50)));
const fixed = content.replace(/^use client";/, '"use client";');
fs.writeFileSync('src/app/approvals/[id]/page.tsx', fixed, 'utf8');
console.log('Fixed');