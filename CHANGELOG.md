# Changelog

## [0.2.1](https://github.com/EPFL-ENAC/leure-speed-to-zero/compare/v0.2.0...v0.2.1) (2025-06-26)


### Bug Fixes

* add CHANGELOG.md to Prettier ignore list ([cc34af0](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/cc34af019f16ad886f4a759df02d920400f33691))

## [0.2.0](https://github.com/EPFL-ENAC/leure-speed-to-zero/compare/v0.1.0...v0.2.0) (2025-06-26)


### Features

* add .gitattributes file for consistent line endings and text handling ([3b0b508](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/3b0b50805a774883014fa15f2d5b19b73a76c26e))
* add cleanup target in Makefile to remove lingering FastAPI processes ([c1686b2](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/c1686b215cc488d1e8312bf7e68e3a57ae5c4cd4))
* add difficulty indicator for lever ([e86de93](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/e86de93aa4ed1ffab2b4c0e16a6823b7c7d600b2))
* add fake kpis component ([4c118db](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/4c118db0c6278e85bacfef7e60cd11b8047585ab))
* add feature request and performance issue templates ([2c15cfe](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/2c15cfec82b207cf1bab8683c08f8f30c72ac044))
* add labels plot ([d8905e9](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/d8905e98321db0841146f5ca558201923a58626e))
* add lever_harvest-rate to API and frontend data structures ([eb06ba1](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/eb06ba1e72bb3606cb603eaf492b1552436c26fd))
* add lever_harvest-rate to API and frontend data structures ([f56a1d3](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/f56a1d3f826be4a5041d2bc565fa9b0c050c9704))
* add Redis caching setup instructions to README ([982a4c0](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/982a4c02191bf8ed80e9355711997713279f98d7))
* add setup script and update Makefile for repository initialization ([8acb3a5](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/8acb3a53ca866575c798932c2d7efb386cf7c4e9))
* add transport tab ([37a8661](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/37a866121c79f7013454d22ae25303ce6758989f))
* add wait-for-backend command to Makefile for health check before running servers ([65c087a](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/65c087af8ccef59c1a7c98626c51046165d14d88))
* **contributing:** simplify pull-request flow ([3eead68](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/3eead682cf887639848440c8fa48d9bdbb85d5e9))
* create virtual environment for backend dependencies installation ([79dbda2](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/79dbda2815151955fb68c4e8df2f5de2c9405c7c))
* enhance caching initialization and health check logging with detailed backend info ([04d7345](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/04d7345ee0f89805de8ba34a84fac116f214adfd))
* enhance caching mechanism with Redis fallback and improved health checks ([b4e8f97](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/b4e8f97a71a30cdad32233f128dc7acc6fbc1fe6))
* enhance Makefile and docker-compose for local development and container management ([e2d67fe](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/e2d67fe53584910ef46ba119444b488ff270291c))
* enhance Makefile with run-backend and run-frontend commands, improve dependency sync logic ([3c0c3ab](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/3c0c3ab5c9348c6637a42c5eb91e820e55c1b060))
* enhance README with development tools installation instructions and WSL2 troubleshooting ([d988286](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/d988286cd24b82b5d51dec8069e8869ad85758d1))
* enhance run command in Makefile to include server stop message and trap ([a185907](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/a1859075134ed944c6fd994f94e19a40ddf6c262))
* enhance run command in Makefile to support uv command detection ([b3fe170](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/b3fe170f0facbd663b39f8c8717edb67f1378100))
* give subtabs initial values ([829c9d5](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/829c9d547d8af9022f4c5821afc58b6b3528d809))
* refactor dashboard layout ([6274dbe](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/6274dbe05b1cdb16ff626079d95790e5003b6091))
* update Python version in README and enhance Makefile for virtual environment support ([000d58e](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/000d58e4a51efc137bbd1e71e973c66abd78ef58))


### Bug Fixes

* correct formatting in settings.json and streamline pip installation in Makefile ([1cb0c6a](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/1cb0c6accba1e3ffa2354e9f731179721c75873b))
* ensure newline at end of file in release-please workflow ([6d7a61f](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/6d7a61f33c8362d1b928f2f4f526976a445ab862))
* expose Redis port to host in docker-compose configuration ([720737d](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/720737d9b8170e86f9e28a757880d278b0e301be))
* improve shutdown message and exit handling for server processes ([9520e82](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/9520e820b21050fdd6bfa73e030ab5157a12c81b))
* **README.md:** link to right repo ([29dea51](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/29dea51e998397f1e549a729a3b99e73fbd12f19)), closes [#8](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/8)
* remove unnecessary blank lines in Redis caching instructions ([9c8b0c4](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/9c8b0c44af2e84a02d070e5f29eda6718cf02c96))
* remove unnecessary newlines in issue template option lists ([da32f72](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/da32f72f3630ac449bde45882875884aac2ff239))
* replace ASSIGNEE_USERNAME with LEAD_DEV in setup script ([6f226ae](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/6f226ae091b741f21cae97a15bba449d12f2e084))
* run prettier --write on all files ([76193ea](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/76193eaee2ec27bcb819b09e46b7569e934d322f))
* update action reference in release-please workflow ([44653f1](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/44653f19fab9fab0419daabeb583833819c1a597))
