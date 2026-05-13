# CHANGELOG



## v1.1.1 (2026-05-13)

### Ci

* ci: replace release-please with semantic-release — single PR triggers full release ([`90464f5`](https://github.com/salecharohit/semhound/commit/90464f5d19a1ce5fee311c12b8199eedf8b7c9b7))

* ci: add workflow_dispatch to release.yml and use PAT for release-please ([`b884c54`](https://github.com/salecharohit/semhound/commit/b884c5439d1dffe34325b08d8fbce17cb1ccafc4))

* ci: use PAT and auto-merge release PRs — single PR per release ([`fdef614`](https://github.com/salecharohit/semhound/commit/fdef6145f82a7744594a340c867b792a11146e6f))

### Documentation

* docs: update contributing guide for new semantic-release workflow ([`d13dfa6`](https://github.com/salecharohit/semhound/commit/d13dfa6d06c6123b47d71d5661bfde333e1b110b))

### Fix

* fix: set git clone blob limit to 1MB to match semgrep&#39;s default max-target-bytes ([`770cd27`](https://github.com/salecharohit/semhound/commit/770cd27c001e18c986abce3c1671cfca63cc4b3d))

### Unknown

* Merge pull request #4 from salecharohit/fix/git-clone-filter

fix: set git clone blob limit to 1MB to match semgrep&#39;s default max-target bytes ([`131b7e7`](https://github.com/salecharohit/semhound/commit/131b7e7a8e81b85908ad144b896a4d8c54fc7ad2))


## v1.1.0 (2026-05-13)

### Chore

* chore(main): release 1.1.0 ([`7b9cab8`](https://github.com/salecharohit/semhound/commit/7b9cab83a3a1d5f37ce96a34682c6ed738d827ec))

### Ci

* ci: force Node.js 24 for release-please to fix deprecation warning ([`9b5cab1`](https://github.com/salecharohit/semhound/commit/9b5cab1bd9b983bc6e4ef576ca4fc9dc84ec4c3a))

### Feature

* feat: use combined blob:none+5m filter to skip large files during clone ([`3835164`](https://github.com/salecharohit/semhound/commit/3835164cb6dc20e4f99ec50858995010d2a2b7f3))

### Unknown

* Merge pull request #3 from salecharohit/release-please--branches--main

chore(main): release 1.1.0 ([`32cde7d`](https://github.com/salecharohit/semhound/commit/32cde7dcadd3cd4d7933de19d9566c4d1292f5e5))

* Merge pull request #2 from salecharohit/feat/optimise-clone-filter

feat: use combined blob:none+5m filter to skip large files during clone ([`1218475`](https://github.com/salecharohit/semhound/commit/1218475734898dab51c057c2cab5faa4085a375d))

* Update README.md

doc: update space ([`4551229`](https://github.com/salecharohit/semhound/commit/45512295b991cb22b971cf0f0f49369f40e9c0f0))


## v1.0.1 (2026-05-12)

### Chore

* chore(main): release 1.0.1 ([`0d9c940`](https://github.com/salecharohit/semhound/commit/0d9c9408c204078833aaf4b01497c8cbecd5eede))

### Documentation

* docs: recommend pipx for installation, clean up changelog and add contribution guide ([`90f9422`](https://github.com/salecharohit/semhound/commit/90f9422639682597b1aa9bd83ba2b7bc8b578fad))

* docs: add contribution guide, social card, and clean up changelog ([`d2a0e11`](https://github.com/salecharohit/semhound/commit/d2a0e115bd81b8b9b50dc5905a7acb68fa1402b3))

* docs: update social card image ([`9ffd8e7`](https://github.com/salecharohit/semhound/commit/9ffd8e78df4b3c6f23649d86bba85652400e8c6c))

### Unknown

* Merge pull request #1 from salecharohit/release-please--branches--main

chore(main): release 1.0.1 ([`6fd6604`](https://github.com/salecharohit/semhound/commit/6fd6604ecf7314454733b5b7d936029e4a8cc958))


## v1.0.0 (2026-05-12)

### Feature

* feat: add social card banner, CI workflow, and README update ([`42500cc`](https://github.com/salecharohit/semhound/commit/42500cc26f66971ca38074c36b055018a561b338))

### Unknown

* first commit ([`d4f22c4`](https://github.com/salecharohit/semhound/commit/d4f22c402bf35e7e8a02cb4113615dcd45f940a4))
