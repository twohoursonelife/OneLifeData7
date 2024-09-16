const execSync = require('child_process').execSync;
const fs = require('fs');

if (!process.argv[2]) {
  console.log(`Run with node ${process.argv[1]} <start_number> <offset?> <end_number?>`);
  return;
}

const sourceNumber = Number(process.argv[2]);
let startNumber = 0;
let offset = 0;
let endNumber = null;
let highestId = 0;
if (process.argv[3]) {
  startNumber = sourceNumber;
  offset = Number(process.argv[3]);
}
if (process.argv[4]) {
  endNumber = Number(process.argv[4]);
}

console.log('Reading sprite files');
const spriteFileList = execSync('ls sprites/').toString().split('\n');
const spriteFileNames = [];
const spriteFileContents = [];

if (!process.argv[3]) {
  for (const file of spriteFileList) {
    if (!file || isNaN(parseInt(file[0])) || !file.includes(".tga")) {
      continue;
    }
    const id = file.match(/(\d+).tga/);
    if (Number(id[1]) + 1 < sourceNumber) {
      startNumber = Math.max( startNumber, Number(id[1]) + 1 );
    }
  }
  offset = startNumber - sourceNumber;
}


console.log('Renaming sprite files');
for (let i = spriteFileList.length - 1; i >= 0; i--) {
  file = spriteFileList[i]
  if (!file || isNaN(parseInt(file[0]))) {
    continue;
  }
  const fileContent = fs.readFileSync(`sprites/${file}`).toString();
  const id = file.match(/(\d+).(?:tga|txt)/);
  if( !id ) continue;
  if (Number(id[1]) >= startNumber && (endNumber === null || Number(id[1]) <= endNumber)) {
    fs.rename( `sprites/${file}`, `sprites/${file.replace(id[1], Number(id[1]) + offset)}`, ()=>{} )
  }
  highestId = Math.max( highestId, Number(id[1]) + offset);
}
if (process.argv[3]) {
  fs.writeFileSync(`sprites/nextSpriteNumber.txt`, String(highestId + 1));
} else {
  fs.writeFileSync(`sprites/nextSpriteNumber.txt`, String(sourceNumber));
}


console.log('Reading object files');
const objectFileList = execSync('ls objects').toString().split('\n');
const objectFileNames = [];
const objectFileContents = [];

for (const file of objectFileList) {
  let needsReplacing = false;
  if (!file || isNaN(parseInt(file[0]))) {
    continue;
  }
  let fileContent = fs.readFileSync(`objects/${file}`).toString();
  const sprites = fileContent.match(/spriteID=(\d+)?\r?\n/g);
  for (const sprite of sprites) {
    const idMatch = sprite.match(/spriteID=(\d+)?\r?\n/);
    if (idMatch && Number(idMatch[1]) > startNumber && (endNumber === null || Number(idMatch[1]) <= endNumber)) {
      needsReplacing = true;
      fileContent = fileContent.replace(`spriteID=${idMatch[1]}`, `spriteID=${Number(idMatch[1]) + offset}`);
    }
  }
  
  if (needsReplacing) {
    objectFileNames.push(file);
    objectFileContents.push(fileContent);
    execSync(`rm objects/${file}`);
  }
}

console.log('Writing object files');
for (let i = 0; i < objectFileNames.length; i++) {
  fs.writeFileSync(`objects/${objectFileNames[i]}`, objectFileContents[i]);
}