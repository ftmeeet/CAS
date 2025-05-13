import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create public/data directory if it doesn't exist
const publicDataDir = path.join(__dirname, 'public', 'data');
if (!fs.existsSync(publicDataDir)) {
  fs.mkdirSync(publicDataDir, { recursive: true });
}

// Copy TLE data files
const sourceFiles = [
  { src: '../data/tle_data.csv', dest: 'public/data/tle_data.csv' },
  { src: '../user_tle.csv', dest: 'public/user_tle.csv' }
];

sourceFiles.forEach(({ src, dest }) => {
  const sourcePath = path.join(__dirname, src);
  const destPath = path.join(__dirname, dest);
  
  if (fs.existsSync(sourcePath)) {
    fs.copyFileSync(sourcePath, destPath);
    console.log(`Copied ${src} to ${dest}`);
  } else {
    console.error(`Source file not found: ${src}`);
  }
}); 