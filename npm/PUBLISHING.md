# Publishing @cisco/cnl to npm

This guide explains how to publish the CNL npm package to the npm registry.

## Prerequisites

1. **npm account** with access to `@cisco` scope
2. **Authenticated npm CLI**: `npm login`
3. **Python package published** to PyPI as `cnl`

## Pre-publish Checklist

- [ ] Python package `cnl` is published to PyPI
- [ ] Version numbers match in `npm/package.json` and `pyproject.toml`
- [ ] README.md is up to date
- [ ] All scripts are executable (`chmod +x bin/* lib/*`)
- [ ] Tested locally with `npm pack` and manual install
- [ ] No secrets or credentials in package files

## Testing Locally

### 1. Create package tarball

```bash
cd npm/
npm pack
```

This creates `cisco-cnl-X.Y.Z.tgz`.

### 2. Install locally

```bash
npm install -g ./cisco-cnl-X.Y.Z.tgz
```

### 3. Test commands

```bash
cnl --version
cnl --help
```

### 4. Uninstall

```bash
npm uninstall -g @cisco/cnl
```

## Publishing to npm

### 1. Ensure you're logged in

```bash
npm whoami
```

If not logged in:

```bash
npm login
```

### 2. Check package contents

```bash
cd npm/
npm pack --dry-run
```

Verify:
- Only necessary files included (bin/, lib/, README.md, package.json)
- No test files, secrets, or development artifacts
- Package size is reasonable (should be < 20 KB)

### 3. Publish (first time)

For scoped packages, explicitly set public access:

```bash
npm publish --access public
```

### 4. Publish (updates)

Update version in `package.json` first:

```bash
npm version patch  # or minor, major
npm publish
```

## Version Management

CNL uses semantic versioning (semver):

- **Patch** (0.1.0 → 0.1.1): Bug fixes, no breaking changes
- **Minor** (0.1.0 → 0.2.0): New features, backward compatible
- **Major** (0.1.0 → 1.0.0): Breaking changes

Keep versions synchronized:
- `npm/package.json` (npm package)
- `pyproject.toml` (pip package)

## Post-publish Verification

1. **Check on npmjs.com**:
   ```
   https://www.npmjs.com/package/@cisco/cnl
   ```

2. **Test installation**:
   ```bash
   npm install -g @cisco/cnl
   cnl --version
   ```

3. **Test with npx**:
   ```bash
   npx @cisco/cnl --help
   ```

## Troubleshooting

### "You do not have permission to publish"

- Ensure you're logged in: `npm whoami`
- Ensure you have access to `@cisco` scope
- Contact npm org admin to add you

### "Package name already exists"

- The name `@cisco/cnl` is already taken
- Use a different name or scope in `package.json`

### "Forbidden - must be scoped"

Add `--access public`:
```bash
npm publish --access public
```

### Large package size

Check `.npmignore` to exclude unnecessary files:
```bash
npm pack --dry-run
```

## Unpublishing (Emergency Only)

⚠️ **Warning**: Unpublishing is permanent and discouraged.

```bash
npm unpublish @cisco/cnl@X.Y.Z
```

Better approach: Deprecate the version instead:

```bash
npm deprecate @cisco/cnl@X.Y.Z "This version has a critical bug, use X.Y.Z+1"
```

## CI/CD Integration

For automated publishing via GitHub Actions, create `.github/workflows/publish-npm.yml`:

```yaml
name: Publish to npm

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          registry-url: 'https://registry.npmjs.org'

      - name: Publish
        working-directory: ./npm
        run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Store `NPM_TOKEN` in GitHub Secrets.

## Support

For issues with publishing, contact:
- npm support: https://www.npmjs.com/support
- Cisco internal npm registry team
