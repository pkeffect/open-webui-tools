# Open WebUI Tools
- Various functions and tools for the Open-WebUI project 
- Code by me with help from various LLMs
- Official Open-WebUI links below
- Various Open-WebUI tips and stuff

| SITE | ADDRESS |
| ------------- | ------------- |
| Changelog | https://github.com/open-webui/open-webui/blob/e9d6ada25cd6ce84be067ba794af4c9d7116edc7/CHANGELOG.md |
| Community | https://openwebui.com/ |
| Discord | https://discord.com/invite/5rJgQTnV4s |
| Documentation | https://docs.openwebui.com/ |
| Documentation Archive | https://github.com/open-webui/docs/archive/refs/heads/main.zip |
| GitHub | https://github.com/open-webui/open-webui |
| GitHub (Community) | https://github.com/open-webui/community |
| GitHub (Pipelines) | https://github.com/open-webui/pipelines |
| Official Maintainer AMA (Reddit) | https://www.reddit.com/r/OpenWebUI/comments/1gjziqm/im_the_sole_maintainer_of_open_webui_ama/ |
| Reddit | https://www.reddit.com/r/OpenWebUI/ |
| X (Formerly Twitter) | https://x.com/OpenWebUI |

## DOCKER IMAGE DOWNLOADS
 - [OpenWebUI Docker Images](https://github.com/open-webui/open-webui/pkgs/container/open-webui/versions?filters%5Bversion_type%5D=tagged)

| IMAGE | BRANCH |
| ------------- | ------------- |
| ```docker pull ghcr.io/open-webui/open-webui:latest``` | Latest |
| ```docker pull ghcr.io/open-webui/open-webui:main``` | Main |
| ```docker pull ghcr.io/open-webui/open-webui:cuda``` | Nvidia CUDA |
| ```docker pull ghcr.io/open-webui/open-webui:ollama``` | Ollama bundle |
| ```docker pull ghcr.io/open-webui/open-webui:dev``` | (Main) development |
| ```docker pull ghcr.io/open-webui/open-webui:dev-cuda``` | Nvidia CUDA development |
| ```docker pull ghcr.io/open-webui/open-webui:dev-ollama``` | Ollama bundle development |
 * I use [Watchtower](https://github.com/containrrr/watchtower) in docker to keep all images updated automatically

## ADDRESSES
If installed, Ollama should be listening on 0.0.0.0 and port 11434 by default
| ADDRESS | DESCRIPTION |
| ------------- | ------------- |
| ```http://localhost:11434``` | Local (host) Machine |
| ```http://127.0.0.1:11434``` | Local (host) Machine | 
| ```http://192.168.xxx.xxx:11434``` | Local (host) Machine |
| ```http://ollama:11434``` | Local (host) Machine | 
| ```http://host.docker.internal:11434``` | Internal Docker |
| ```http://172.xxx.xxx.xxx:11434``` | Internal Docker |
 * I use [Nginx Proxy Manager](https://nginxproxymanager.com/guide/) in docker for websocket and proxying/SSL certification control

## OWUI PROMPT VARIABLES 
| VAR | DESCRIPTION |
| ------------- | ------------- |
| ```{{CLIPBOARD}}``` | Contents of your current clipboard |
| ```{{USER_NAME}}``` | Your name |
| ```{{USER_LOCATION}}``` | Your location |
| ```{{USER_LANGUAGE}}``` | Your language |
| ```{{CURRENT_DATE}}``` | Current date |
| ```{{CURRENT_TIME}}``` | Current time |
| ```{{CURRENT_DATETIME}}``` | Current date and time |
| ```{{CURRENT_TIMEZONE}}``` | Your timezone |
| ```{{CURRENT_WEEKDAY}}``` | Current weekday |
 
## DEVELOPMENT
 * To edit OpenWebUI, you must first set up a development environment
 * See [Advanced Topics - Development](https://docs.openwebui.com/getting-started/advanced-topics/development)
 * Then [fork](https://github.com/open-webui/open-webui/fork) the repo 
 * Make any edits you need to the code
 * Rebuild your project image
 * Deploy new image
 * These edits need to be made each time you update OpenWebUI as they will be overwritten
