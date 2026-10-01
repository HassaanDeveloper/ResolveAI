const fs = require('fs');
const content = fs.readFileSync('src/app/approvals/[id]/page.tsx', 'utf8');
// Remove leading " and trailing " after "use client"
let fixed = content;
if (fixed.startsWith('"')) {
  fixed = fixed.slice(1);
}
fixed = fixed.replace('use client";', '"use client";');
fs.writeFileSync('src/app/approvals/[id]/page.tsx', fixed, 'utf8');
console.log('Fixed');