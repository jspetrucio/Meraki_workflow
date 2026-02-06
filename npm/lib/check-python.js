#!/usr/bin/env node
/**
 * Python Environment Checker
 *
 * Checks if Python 3.10+ is available on the system.
 * Returns the path to the Python executable or null.
 */

const { execFileSync } = require('child_process');

/**
 * Check if a Python command meets minimum version requirement
 * @param {string} command - Python command to test (python3, python, etc.)
 * @returns {string|null} - Path to Python executable or null
 */
function checkPythonCommand(command) {
  try {
    // Use execFileSync to safely execute command
    const versionOutput = execFileSync(command, ['--version'], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe']
    }).trim();

    // Parse version: "Python 3.10.5" -> [3, 10, 5]
    const match = versionOutput.match(/Python (\d+)\.(\d+)\.(\d+)/);
    if (!match) {
      return null;
    }

    const major = parseInt(match[1], 10);
    const minor = parseInt(match[2], 10);

    // Check minimum version: Python 3.10+
    if (major >= 3 && minor >= 10) {
      // Get full path to executable
      const pythonPath = execFileSync(command, ['-c', 'import sys; print(sys.executable)'], {
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe']
      }).trim();
      return pythonPath;
    }

    return null;
  } catch (error) {
    // Command not found or execution error
    return null;
  }
}

/**
 * Find suitable Python installation
 * @returns {{found: boolean, path: string|null, version: string|null}}
 */
function findPython() {
  // Try common Python commands in order of preference
  const commands = ['python3', 'python', 'python3.11', 'python3.10'];

  for (const cmd of commands) {
    const pythonPath = checkPythonCommand(cmd);
    if (pythonPath) {
      try {
        const version = execFileSync(cmd, ['--version'], {
          encoding: 'utf8',
          stdio: ['ignore', 'pipe', 'pipe']
        }).trim();

        return {
          found: true,
          path: pythonPath,
          version: version,
          command: cmd
        };
      } catch {
        // Version check failed, continue
      }
    }
  }

  return {
    found: false,
    path: null,
    version: null,
    command: null
  };
}

// If run directly (not imported)
if (require.main === module) {
  const result = findPython();

  if (result.found) {
    console.log('✓ Python found:', result.version);
    console.log('  Path:', result.path);
    process.exit(0);
  } else {
    console.error('✗ Python 3.10+ not found');
    console.error('\nPlease install Python 3.10 or later:');
    console.error('  macOS:   brew install python@3.11');
    console.error('  Ubuntu:  sudo apt install python3.11');
    console.error('  Windows: https://www.python.org/downloads/');
    process.exit(1);
  }
}

module.exports = { findPython, checkPythonCommand };
