# Reader walkthrough — 31 October 2026

We downloaded the public pinned ZIP into a new directory and followed the written commands. These are bounded observations, not a promise that every account, operating system or model output will work.

| Example | What was actually checked | Outcome |
|---|---|---|
| Facebook preparation | Fresh Windows Python 3.13 virtual environment; only declared Pillow dependency; untouched sample input | Arabic 1080×1350 PNG and preview package generated |
| Facebook publisher | Reviewed local input, offline preview, demo rejection, mismatched Page confirmation, missing private settings; actual read-only Meta request with a deliberately invalid dummy token | Success/stop behaviour as expected; error messages improved; **no live post sent** |
| Automated suite | Review guards, actual multipart request serialization, Page mismatch, mocked receipt, duplicate/timeout handling and credential-free CLI errors | 21 local tests pass; not a Facebook acceptance test |
| Faceless video | README command with installed FFmpeg/libass; inspect file using ffprobe and view first frame | Silent 9-second 1080×1920 MP4; Arabic text visible |
| REA | Analyze the publicly downloaded navigation example with REA 6.8.0 and vendor-checksummed portable Node 24.22.2 on Windows | Exit 0, ok=true, one JavaScript file parsed, no parse failures. Standard npx setup was blocked by missing Windows cmd.exe; direct CLI was tested instead |
| REA on Linux | Download public ZIP and use a fresh npm cache, supported Node and the pinned npx analysis command as an unprivileged user from an accessible tools folder | Exit 0, ok=true, one JavaScript file parsed, no parse failures; no agent configuration changed |
| Hostinger demo | Anonymous HTTP checks of all three files; compare public ZIP bytes; browser menu at 390, 860 and 861 px, link close, scroll lock and header change | Files match live demo; checked behaviour works |
| Make | Use the public planner buttons to download all three files, then import them into a new unsaved inactive editor | Five/five/six native modules render. Connections/Data store still need setup; **no new scenario execution or publication** |
| ZIP Checker | Real REA package, missing CSS, filename case mismatch, unsafe path | Candidate, repair diagnostics and rejection displayed as expected |
| Video Cost Calculator | Independently calculated per-clip and per-second cases; CSV; negative input | USD 11 and USD 27 as expected; invalid input blocked |
| AI Model Finder | Combined task/resolution/20-second-duration filters, reset, comparison limit, TXT export | Matching profile shown, reset works, fourth comparison rejected and three exported |

The REA intro/case study/deployment, Make article and Facebook article have reviewed drafts. The WordPress-to-Telegram and faceless-video topics were queued without full reviewed article text at this check, so we tested their downloadable examples rather than claiming to have followed finished articles.

The working examples do not eliminate account prerequisites: readers need their own Page token and Meta permissions, Make connections, Telegram destination and suitable Data store. No credentials or private project files are included here. Future release changes can alter requirements.
