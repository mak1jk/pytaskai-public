# PyTaskAI v0.3.0 Deployment Guide

## Pre-Deployment Verification ✅

### Package Validation
- [x] All tests passing (168 tests)
- [x] Architecture validation complete
- [x] Package builds successfully
- [x] Local installation verified
- [x] CLI functionality confirmed
- [x] Core imports working

### Distribution Files Ready
- [x] `dist/pytaskai-0.3.0-py3-none-any.whl`
- [x] `dist/pytaskai-0.3.0.tar.gz`
- [x] Package validation: PASSED (twine check)

## Deployment Instructions

### 1. Deploy to TestPyPI (Recommended First)

```bash
# Upload to TestPyPI for final validation
python -m twine upload --repository testpypi dist/* --username __token__ --password <TEST_PYPI_TOKEN>

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pytaskai==0.3.0

# Verify test installation
pytaskai --help
pytaskai version
```

### 2. Deploy to Production PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/* --username __token__ --password <PYPI_TOKEN>

# Verify production installation
pip install pytaskai==0.3.0
pytaskai --help
```

### 3. Create Git Release

```bash
# Create and push git tag
git tag -a v0.3.0 -m "PyTaskAI v0.3.0 - Production Ready Hexagonal Architecture"
git push origin v0.3.0

# Create GitHub release through web interface or gh CLI
gh release create v0.3.0 --title "PyTaskAI v0.3.0" --notes-file RELEASE_NOTES.md
```

## API Token Configuration

### For TestPyPI:
1. Go to https://test.pypi.org/manage/account/token/
2. Create new API token for "pytaskai" project
3. Use format: `pypi-AgEIcHl...` (starts with pypi-)

### For Production PyPI:
1. Go to https://pypi.org/manage/account/token/
2. Create new API token for "pytaskai" project
3. Use format: `pypi-AgEIcHl...` (starts with pypi-)

## Deployment Status

- [x] Pre-deployment verification
- [x] Package build completed
- [x] Local installation tested
- [ ] TestPyPI deployment (requires API token)
- [ ] Production PyPI deployment (requires API token)
- [ ] Git tag and release creation

## Package Information

**Package Name:** pytaskai  
**Version:** 0.3.0  
**Status:** Production/Stable  
**Python Support:** 3.8+  
**Architecture:** Hexagonal (Ports & Adapters)  
**Test Coverage:** 80% (168 tests passing)  

## Post-Deployment Verification

After successful deployment, verify:

1. **Package Installation:**
   ```bash
   pip install pytaskai
   pytaskai --help
   ```

2. **CLI Functionality:**
   ```bash
   pytaskai init
   pytaskai task add "Test task"
   pytaskai task list
   ```

3. **MCP Integration:**
   ```bash
   python -m pytaskai.adapters.mcp
   ```

4. **Import Verification:**
   ```python
   from pytaskai.domain.entities.task import Task
   from pytaskai.application.container import ApplicationContainer
   ```

## Known Dependencies

Core production dependencies:
- fastmcp>=0.3.0
- pydantic>=2.0.0  
- sqlalchemy>=2.0.0
- openai>=1.0.0
- click>=8.0.0
- tabulate>=0.9.0
- python-dotenv>=1.0.0

All dependencies will be automatically installed via pip.

## Support

**GitHub Repository:** https://github.com/mak1jk/pytaskai-public  
**Issues:** https://github.com/mak1jk/pytaskai-public/issues  
**Documentation:** See README.md and CLAUDE.md  