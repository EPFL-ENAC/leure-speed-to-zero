# Changelog

## [0.6.1](https://github.com/EPFL-ENAC/leure-speed-to-zero/compare/v0.6.0...v0.6.1) (2025-09-15)


### Bug Fixes

* **package:** pin @quasar/app-vite version to 2.2.0 ([d222633](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/d222633de922fb2505ce86c984d3cc196056e65c))

## [0.6.0](https://github.com/EPFL-ENAC/leure-speed-to-zero/compare/v0.5.0...v0.6.0) (2025-09-15)


### Features

* **backend:** add test endpoint for lever data extraction functionality ([a634139](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/a6341392802a814dcf9283c31500474bed953bc1))
* clicks on kpi box navigate to route tab [#31](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/31) ([ea8cfc0](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/ea8cfc0bc2190b4844b62771b616738e4481c860))
* **front:** use the order from sectors in leversData to display [#24](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/24) ([d1b85f6](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/d1b85f6f56018c7727cdef7088bed741879d6f56))
* **kpi:** add hover tooltip + redesign kpi [#31](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/31) [#27](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/27) ([a12ea73](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/a12ea73819d9ac8f42c85d5e1db5d5ae6f0a24d1))
* **lever:** add disabled option for levers [#30](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/30) ([c43b0cd](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/c43b0cd705bf75c7f9730f57da18857edb58ac88))
* **lever:** add lever detail popup using data from model [#30](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/30) [#6](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/6) ([e86c486](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/e86c486b0cb2ace9d8dfc9303409706155ed04fb))
* **lever:** add lever expand chart details ([94ac90a](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/94ac90a12cc76e79257030623396b1b6769f985b))


### Bug Fixes

* **chart:** fix category selection persistence when levers are modified & fix line chart instead of bar [#26](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/26) ([7d2137f](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/7d2137f8c362510ae8563e90cacda43629d33f72))
* **front:** fix kpi logic [#9](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues/9) ([57734e7](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/57734e7f59806cbdf08270c86b196b5455c0a7fa))
* **front:** update miniState initialization for consistent mobile behavior ([552fed0](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/552fed0cbf1f807f8a78547d3bdedf9b6a38bbf9))
* **kpi:** simplify kpi status ring styling by removing box shadow and adjusting border ([0d08fb3](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/0d08fb366bb1148cbacd4125cc2e5669381e5cb3))
* minor visual fixes ([0693116](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/069311692e47cc8a64d62a3215779f947153d172))

## [0.5.0](https://github.com/EPFL-ENAC/leure-speed-to-zero/compare/v0.4.1...v0.5.0) (2025-08-13)


### Features

* **front:** add responsive design for mobile/tablet ([65ae6ab](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/65ae6ab29ee18f2dded072cf596335437cd42b60))
* **front:** enhance SectorTab for responsive design - mobile list ([430d269](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/430d26900b594d72cb2453d7bfb5b7847dcc2d3a))

## [0.4.0](https://github.com/EPFL-ENAC/leure-speed-to-zero/compare/v0.3.0...v0.4.0) (2025-08-13)


### Features

* **front:** enhance layout of LeverSelector and DashboardLayout ([99243e1](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/99243e1e39e1ed1937b739b7f4d3af293dcbef8c))


### Bug Fixes

* **buildings.json:** correct formatting of color property in KPI data ([e8df96a](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/e8df96a9c14f74f322116cac2b3c74e2d969d63b))

## [0.3.0](https://github.com/EPFL-ENAC/leure-speed-to-zero/compare/v0.2.1...v0.3.0) (2025-06-30)


### Features

* add .env file for cross-platform PYTHONPATH configuration ([98a7d1e](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/98a7d1e9a757d3ed7cc4e0fb98de1f65ea57ce19))


### Bug Fixes

* streamline extraPaths configuration in VSCode settings ([8697568](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/8697568c195a023c2a1ddea020e4dd295168d7ed))
* update Python settings in VSCode configuration ([24280df](https://github.com/EPFL-ENAC/leure-speed-to-zero/commit/24280df363955e20bc12bb612fb17af76fbc08e1))

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
