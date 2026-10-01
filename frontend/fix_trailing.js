const fs = require('fs');
const content = fs.readFileSync('src/app/approvals/[id]/page.tsx', 'utf8');
console.log('Before:', JSON.stringify(content.slice(0, 20)));
let fixed = content;
fixed = fixed.replace('use client";', 'use client;');
console.log('After:', JSON.stringify(fixed.slice(0, 20)));
fs.writeFileSync('src/app/approvals/[id]/page.tsx', fixed, 'utf8');
console.log('Fixed trailing quote');