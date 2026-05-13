# CHANGELOG

<!-- version list -->

## [1.1.0](https://github.com/salecharohit/semhound/compare/v1.0.1...v1.1.0) (2026-05-13)


### Features

* use combined blob:none+5m filter to skip large files during clone ([1218475](https://github.com/salecharohit/semhound/commit/1218475734898dab51c057c2cab5faa4085a375d))
* use combined blob:none+5m filter to skip large files during clone ([3835164](https://github.com/salecharohit/semhound/commit/3835164cb6dc20e4f99ec50858995010d2a2b7f3))

## [1.0.1](https://github.com/salecharohit/semhound/compare/v1.0.0...v1.0.1) (2026-05-12)


### Documentation

* add contribution guide, social card, and clean up changelog ([d2a0e11](https://github.com/salecharohit/semhound/commit/d2a0e115bd81b8b9b50dc5905a7acb68fa1402b3))
* recommend pipx for installation, clean up changelog and add contribution guide ([90f9422](https://github.com/salecharohit/semhound/commit/90f9422639682597b1aa9bd83ba2b7bc8b578fad))
* update social card image ([9ffd8e7](https://github.com/salecharohit/semhound/commit/9ffd8e78df4b3c6f23649d86bba85652400e8c6c))

## v1.0.0 (2026-05-12)

### Initial Release

- First public release of semhound
  ([`d4f22c4`](https://github.com/salecharohit/semhound/commit/d4f22c4))

### Features

- Automated Semgrep scanning across GitHub organisations and user accounts
- Parallel repository cloning and scanning with configurable thread count
- AI triage support via Claude, OpenAI, GPT, Gemini, and AWS Bedrock
- CSV and SARIF output with GitHub permalinks to every finding
- Automated versioning and GitHub releases via release-please
  ([`42500cc`](https://github.com/salecharohit/semhound/commit/42500cc))

### Documentation

- Add social card banner to README
- Add CI workflow for pull request checks
- Add CONTRIBUTING.md with conventional commits and release pipeline guide
  ([`9ffd8e7`](https://github.com/salecharohit/semhound/commit/9ffd8e7))
