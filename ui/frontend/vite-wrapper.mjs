#!/usr/bin/env node

// CRITICAL: Set up crypto polyfill BEFORE any other imports
import { webcrypto } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

// Set up crypto globally before Vite loads
if (!globalThis.crypto || !globalThis.crypto.getRandomValues) {
  globalThis.crypto = webcrypto
}

// Get the path to vite's CLI using file system path resolution
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const viteCliPath = join(__dirname, 'node_modules', 'vite', 'bin', 'vite.js')

// Import Vite's CLI - this will execute it with our polyfill in place
// We need to set argv[1] to point to vite's CLI so it processes args correctly
process.argv[1] = viteCliPath

// Now import and execute Vite
await import('file://' + viteCliPath)

