import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { rimraf } from 'rimraf';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const staticFolderPath = path.join(__dirname, '../server/static');
const distFolderPath = path.join(__dirname, 'dist');

async function copyRecursive(src, dest) {
    const stats = await fs.stat(src);

    if (stats.isDirectory()) {
        // Create directory if it doesn't exist
        await fs.mkdir(dest, { recursive: true });

        // Read directory contents
        const items = await fs.readdir(src);

        // Recursively copy each item
        for (const item of items) {
            const srcPath = path.join(src, item);
            const destPath = path.join(dest, item);
            await copyRecursive(srcPath, destPath);
        }
    } else {
        // Copy file
        await fs.copyFile(src, dest);
        console.log(`Copied: ${path.relative(distFolderPath, src)}`);
    }
}

async function clearAndCopy() {
    try {
        console.log('Static folder path:', staticFolderPath);
        console.log('Dist folder path:', distFolderPath);

        // Clear the contents of the static folder
        const files = await fs.readdir(staticFolderPath);
        for (const file of files) {
            await rimraf(path.join(staticFolderPath, file));
        }
        console.log('Static folder contents cleared successfully');

        // Check if the dist folder exists
        const distFolderExists = await fs.access(distFolderPath).then(() => true).catch(() => false);
        if (!distFolderExists) {
            console.error('Dist folder does not exist');
            process.exit(1);
        }

        // Copy dist contents to static folder with preserved structure
        await copyRecursive(distFolderPath, staticFolderPath);
        console.log('Dist files copied successfully with folder structure preserved!');

    } catch (err) {
        console.error('Error in clearAndCopy:', err);
        process.exit(1);
    }
}

clearAndCopy();