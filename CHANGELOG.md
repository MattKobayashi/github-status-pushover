# Changelog

## [1.1.5](https://github.com/MattKobayashi/github-status-pushover/compare/v1.1.4...v1.1.5) (2025-07-21)


### Bug Fixes

* **docker:** use alpine base ([#43](https://github.com/MattKobayashi/github-status-pushover/issues/43)) ([d3a7449](https://github.com/MattKobayashi/github-status-pushover/commit/d3a7449110a92f733580d6b9f88ffc4dced1708e))

## [1.1.4](https://github.com/MattKobayashi/github-status-pushover/compare/v1.1.3...v1.1.4) (2025-06-09)


### Bug Fixes

* **deps:** update dependency requests to v2.32.4 ([#36](https://github.com/MattKobayashi/github-status-pushover/issues/36)) ([59b423e](https://github.com/MattKobayashi/github-status-pushover/commit/59b423e8362c809815534ad23e57eae18a36ed53))

## [1.1.3](https://github.com/MattKobayashi/github-status-pushover/compare/v1.1.2...v1.1.3) (2025-02-28)


### Bug Fixes

* Update save_last_checked_time to accept optional last_time parameter ([6297c5f](https://github.com/MattKobayashi/github-status-pushover/commit/6297c5f118ec18afc9f4317f1a55d14b70bb9ace))

## [1.1.2](https://github.com/MattKobayashi/github-status-pushover/compare/v1.1.1...v1.1.2) (2025-02-28)


### Bug Fixes

* Update html_to_text to convert &lt;br /&gt; tags to newlines and add test ([795441f](https://github.com/MattKobayashi/github-status-pushover/commit/795441fad24c365669b276c86b35401e5fa7d330))

## [1.1.1](https://github.com/MattKobayashi/github-status-pushover/compare/v1.1.0...v1.1.1) (2025-02-28)


### Bug Fixes

* Update check_feed to handle initial run and send most recent update ([fa675e2](https://github.com/MattKobayashi/github-status-pushover/commit/fa675e21dbe65f432a1e6e4d7313bc34f63b6bec))
* Update html_to_text to handle closing &lt;p&gt; tags as new paragraphs ([025508b](https://github.com/MattKobayashi/github-status-pushover/commit/025508b07301de0669d032040f16da875a18a167))

## [1.1.0](https://github.com/MattKobayashi/github-status-pushover/compare/v1.0.0...v1.1.0) (2025-02-28)


### Features

* Add HTML to text conversion for notification messages ([798ff57](https://github.com/MattKobayashi/github-status-pushover/commit/798ff5727a19caeaafe9083e2e44aac6592b8d1f))

## 1.0.0 (2025-02-27)


### Features

* Add CI workflow, improve code structure, and update dependencies ([1b783a4](https://github.com/MattKobayashi/github-status-pushover/commit/1b783a45a65a698232ebf9932bf0806ab1c75418))
* Add GitHub Status RSS monitor with Pushover notifications ([2becbe3](https://github.com/MattKobayashi/github-status-pushover/commit/2becbe3586d4e88992ad5d535a440c133702ae31))
* Add main.py with basic main function structure ([f1d9e29](https://github.com/MattKobayashi/github-status-pushover/commit/f1d9e299535c2750ad7e29997ec3da4ad177b2a0))
* Add user 'app' in Dockerfile for improved security ([2ae2f5d](https://github.com/MattKobayashi/github-status-pushover/commit/2ae2f5dcc0ca78c23fbe3c9a6c833a51cb3af793))


### Bug Fixes

* Correct indentation and move imports to top in main.py ([99b713a](https://github.com/MattKobayashi/github-status-pushover/commit/99b713ad5a761ae8fb61bbde6db1f4978a2fb0c3))
