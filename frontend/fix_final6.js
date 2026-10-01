const fs = require('fs');
const content = fs.readFileSync('src/app/approvals/[id]/page.tsx', 'utf8');
console.log('First char:', content.charCodeAt(0));
console.log('First 15:', content.slice(0,15));
let fixed = content;
if (fixed.charCodeAt(0) === 34) {
  fixed = fixed.slice(1);
  console.log('After slice, first 5:', fixed.slice(0,5));
}
fixed = fixed.replace('use client";', '"use client";');
console.log('After replace, first 20:', JSON.stringify(fixed.slice(0,20)));
fs.writeFileSync('src/app/approvals/[id]/page.tsx', fixed, 'utf8');
console.log('Written');