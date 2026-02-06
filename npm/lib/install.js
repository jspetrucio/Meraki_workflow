#!/usr/bin/env node
/**
 * Post-install script for @cisco/cnl
 *
 * Verifies Python 3.10+ is available and installs the CNL pip package.
 */

const { execFileSync, spawnSync } = require('child_process');
const { findPython } = require('./check-python');

/**
 * Check if CNL pip package is installed
 * @param {string} pythonPath - Path to Python executable
 * @returns {boolean}
 */
function isCnlInstalled(pythonPath) {
  try {
    execFileSync(pythonPath, ['-m', 'pip', 'show', 'cnl'], {
      stdio: ['ignore', 'pipe', 'pipe']
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Install CNL pip package
 * @param {string} pythonPath - Path to Python executable
 * @returns {boolean} - Success status
 */
function installCnl(pythonPath) {
  console.log('Installing CNL Python package...');

  try {
    // Install using pip with --user flag for user-level installation
    const result = spawnSync(
      pythonPath,
      ['-m', 'pip', 'install', '--user', '--upgrade', 'cnl'],
      {
        stdio: 'inherit'
      }
    );

    if (result.status === 0) {
      console.log('✓ CNL Python package installed successfully');
      return true;
    } else {
      console.error('✗ Failed to install CNL Python package');
      return false;
    }
  } catch (error) {
    console.error('✗ Error installing CNL:', error.message);
    return false;
  }
}

/**
 * Main installation flow
 */
function main() {
  console.log('=== CNL Installation ===\n');

  // Step 1: Check Python
  console.log('Checking Python installation...');
  const python = findPython();

  if (!python.found) {
    console.error('\n✗ Python 3.10+ is required but not found');
    console.error('\nPlease install Python 3.10 or later:');
    console.error('  macOS:   brew install python@3.11');
    console.error('  Ubuntu:  sudo apt install python3.11');
    console.error('  Windows: https://www.python.org/downloads/');
    console.error('\nAfter installing Python, run: npm install -g @cisco/cnl');
    process.exit(1);
  }

  console.log(`✓ ${python.version} found at ${python.path}\n`);

  // Step 2: Check if CNL is already installed
  console.log('Checking CNL package...');
  if (isCnlInstalled(python.path)) {
    console.log('✓ CNL package already installed\n');
    console.log('Installation complete! Run: cnl --help');
    return;
  }

  // Step 3: Install CNL pip package
  console.log('CNL not found, installing...\n');
  const success = installCnl(python.path);

  if (success) {
    console.log('\n=== Installation Complete ===');
    console.log('\nGet started with:');
    console.log('  cnl --help           # Show help');
    console.log('  cnl --version        # Show version');
    console.log('  cnl                  # Start web UI');
  } else {
    console.error('\n=== Installation Failed ===');
    console.error('\nYou can try installing manually:');
    console.error(`  ${python.command} -m pip install --user cnl`);
    process.exit(1);
  }
}

// Run installation
if (require.main === module) {
  main();
}

module.exports = { isCnlInstalled, installCnl };
