# Contributing

We welcome contributions to this project! Whether it's bug reports, documentation improvements, or code enhancements, your help is appreciated.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an [Issue](https://github.com/themetalleg/forticlient-linux-ipsec-sso/issues) with:

1. **Description**: What went wrong?
2. **Environment**:
   - Linux distribution and version (e.g., Ubuntu 26.04 LTS)
   - FortiClient version (Windows and Linux)
   - Python version
3. **Steps to reproduce**: How can we recreate the issue?
4. **Expected behavior**: What should happen?
5. **Actual behavior**: What actually happened?
6. **Error messages**: Include any error output (without credentials)

**Important**: Do NOT include:
- Pre-shared keys or passwords
- Configuration backups or database files
- Real gateway addresses or customer information

### Suggesting Improvements

Open an [Issue](https://github.com/themetalleg/forticlient-linux-ipsec-sso/issues) with the `enhancement` label to suggest:
- New features
- Documentation improvements
- Performance optimizations
- Compatibility with newer FortiClient versions

### Submitting Code Changes

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** to your branch
4. **Test thoroughly** before submitting
5. **Submit a pull request** with:
   - Clear description of changes
   - Explanation of why the change is needed
   - Any relevant issue numbers

## Code Style

- **Python**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- **Markdown**: Keep line length reasonable (~80-100 characters)
- **Comments**: Only comment non-obvious logic
- **Naming**: Use clear, descriptive variable and function names

## Security Considerations

When contributing code:

1. **Never log credentials**: Do not print or store pre-shared keys, passwords, etc.
2. **Use hidden input**: Use `getpass.getpass()` for sensitive input
3. **Validate input**: Check for injection attacks or unexpected input
4. **Error handling**: Catch exceptions gracefully without exposing secrets
5. **Review dependencies**: Only use necessary libraries

## Documentation

- Keep [README.md](./README.md) updated with major changes
- Update [docs/GUIDE.md](./docs/GUIDE.md) if steps or commands change
- Update [docs/SCRIPT.md](./docs/SCRIPT.md) if script behavior changes
- Update [docs/FAQ.md](./docs/FAQ.md) with new Q&A entries
- Use clear language and provide examples

## Testing

Before submitting:

1. **Manual testing**: Run the script on a test system
2. **Test all actions**: `setup`, `fix`, `restore`, `doctor`
3. **Test error cases**: What happens with invalid input?
4. **Check dependencies**: Do new dependencies work on supported systems?
5. **Verify compatibility**: Test on multiple Ubuntu versions if possible

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see [LICENSE](./LICENSE)).

## Code of Conduct

Be respectful and constructive. This is a community project for sharing knowledge.

## Questions?

Open an issue with the question label or start a discussion on the [Fortinet Community Forum](https://community.fortinet.com/support-forum-92/).

---

Thank you for contributing! 🎉
