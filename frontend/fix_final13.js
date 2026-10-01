const fs = require('fs');
const content = fs.readFileSync('src/app/approvals/[id]/page.tsx', 'utf8');
console.log('Before fix, first 30:', JSON.stringify(content.slice(0,30)));
let fixed = content;
if (fixed.charCodeAt(0) === 34) {
  fixed = fixed.slice(1);
}
console.log('After slice, first 30:', JSON.stringify(fixed.slice(0,30)));
// The string now is: use client\";\n\nimport...
// Need to replace 'use client\";\n' with '"use client\";\n'
fixed = fixed.replace('use client\";\n', '"use client";\n');
console.log('After replace, first 30:', JSON.stringify(fixed.slice(0,30)));
fs.writeFileSync('src/app/approvals/[id]/page.tsx', fixed, 'utf8');
console.log('Written');