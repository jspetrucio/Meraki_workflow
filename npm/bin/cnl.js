#!/usr/bin/env node
/**
 * CNL CLI Entry Point
 *
 * This is a thin Node.js wrapper that launches the Python-based CNL CLI.
 * It ensures Python is available and the CNL package is installed before
 * forwarding all arguments to the Python implementation.
 */

const { spawn } = require('child_process');
const { findPython } = require('../lib/check-python');
const { isCnlInstalled, installCnl } = require('../lib/install');

/**
 * Launch the Python CNL CLI with arguments
 * @param {string} pythonCommand - Python command (python3, python)
 * @param {string[]} args - CLI arguments to forward
 */
function launchCnl(pythonCommand, args) {
  // The pip package installs 'cnl' as a CLI script entry point
  // Try to run it directly first, fall back to python -m if not in PATH
  const cnlProcess = spawn('cnl', args, {
    stdio: 'inherit',
    cwd: process.cwd(),
    shell: true // Use shell to find cnl in PATH
  });

  cnlProcess.on('exit', (exitCode) => {
    process.exit(exitCode || 0);
  });

  cnlProcess.on('error', (error) => {
    if (error.code === 'ENOENT') {
      // cnl command not in PATH, try invoking via Python
      console.log('CNL command not in PATH, trying alternate method...\n');

      const fallbackProcess = spawn(pythonCommand, ['-m', 'scripts.cli', ...args], {
        stdio: 'inherit',
        cwd: process.cwd()
      });

      fallbackProcess.on('exit', (code) => {
        process.exit(code || 0);
      });

      fallbackProcess.on('error', (err) => {
        console.error('✗ Failed to launch CNL:', err.message);
        console.error('\nTry reinstalling: npm install -g @cisco/cnl');
        process.exit(1);
      });
    } else {
      console.error('✗ Error launching CNL:', error.message);
      process.exit(1);
    }
  });
}

/**
 * Main CLI handler
 */
async function main() {
  // Get command line arguments (skip node and script path)
  const args = process.argv.slice(2);

  // Step 1: Find Python
  const python = findPython();

  if (!python.found) {
    console.error('✗ Python 3.10+ is required but not found\n');
    console.error('Please install Python 3.10 or later:');
    console.error('  macOS:   brew install python@3.11');
    console.error('  Ubuntu:  sudo apt install python3.11');
    console.error('  Windows: https://www.python.org/downloads/\n');
    process.exit(1);
  }

  // Step 2: Check if CNL package is installed
  if (!isCnlInstalled(python.path)) {
    console.log('CNL Python package not found. Installing...\n');

    const success = installCnl(python.path);
    if (!success) {
      console.error('\n✗ Failed to install CNL package');
      console.error('\nTry installing manually:');
      console.error(`  ${python.command} -m pip install --user cnl\n`);
      process.exit(1);
    }

    console.log(''); // Empty line for spacing
  }

  // Step 3: Launch Python CLI
  launchCnl(python.command, args);
}

// Handle errors gracefully
process.on('uncaughtException', (error) => {
  if (error.code === 'ENOENT') {
    console.error('✗ Command not found');
  } else {
    console.error('✗ Unexpected error:', error.message);
  }
  process.exit(1);
});

// Run the CLI
main().catch((error) => {
  console.error('✗ Fatal error:', error.message);
  process.exit(1);
});
