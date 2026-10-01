const fs = require('fs');
const content = fs.readFileSync('src/app/approvals/[id]/page.tsx', 'utf8');
console.log('First 15 codes:', content.slice(0,15).split('').map(c=>c.charCodeAt(0)));
let fixed = content;
if (fixed.charCodeAt(0) === 34) {
  fixed = fixed.slice(1);
}
fixed = fixed.replace('use client";', '"use client";');
console.log('After fix, first 15 codes:', fixed.slice(0,15).split('').map(c=>c.charCodeAt(0)));
console.log('First 20 chars:', JSON.stringify(fixed.slice(0,20)));
fs.writeFileSync('src/app/approvals/[id]/page.tsx', fixed, 'utf8');
console.log('Written');