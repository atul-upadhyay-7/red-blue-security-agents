# red-blue-agents

A small attack-and-defend demo with two cooperating agents, built for the
Security track of the Diwali Festiverse agent-to-agent hackathon.

- **Red agent** scans a deliberately weak web app with
  [OWASP Nettacker](https://github.com/OWASP/Nettacker) and writes a list of findings.
- **Blue agent** reads those findings, explains each one in plain language and
  applies a fix to the app.
- The red agent then scans again to check that the fixes worked.

Everything runs on `127.0.0.1`. The target is a tiny Flask app in this repo.
Do not point the red agent at anything you do not own.

## What it finds and fixes

| Finding | Nettacker module | Blue agent fix |
|---|---|---|
| Wildcard CORS with credentials | `http_cors_vuln` | stop sending the wildcard header |
| Admin page open without login | `admin_scan` | return 403 on `/admin` |

`admin_scan` also reports 403 pages and the site root, so the red agent only
counts an admin finding when an admin path answers 200.

## Run it

```
python -m venv v && . v/bin/activate
pip install -r requirements.txt
python run_demo.py
```

Expected output: the red agent reports two findings, the blue agent patches
both, the retest reports none, and the script prints `RESULT: PASS`.
A full run takes about half a minute.

## Run it on Band

The two agents also run as separate agents on [Band](https://www.band.ai),
talking to each other in a shared room. They are plain Python with Band's
`SimpleAdapter`, so no language model or paid key is needed.

1. Make a free Band account and create two agents, `red-scanner` and `blue-patcher`.
2. Put their ids and API keys in `agent_config.yaml` (git-ignored, never commit it).
   Use the keys `red_scanner` and `blue_patcher`.
3. Use Python 3.11 or newer, then `pip install -r requirements.txt band-sdk`.
4. Start `python band_agents/red_band.py` and `python band_agents/blue_band.py`.
5. Make a Band room with both agents and write `@Red Scanner scan the practice app`.

Red scans and tags Blue with the findings. Blue explains and patches, then tags
Red. Red rescans and reports `RESULT PASS` back to you in the room.

## Layout

```
target/vulnerable_app.py   the weak app (patches are read from patches.json)
agents/red_agent.py        Nettacker scan, structured findings
agents/blue_agent.py       findings to explanation and patch
band_agents/               the two agents wired to Band
run_demo.py                scan, patch, rescan without Band
```

## Status

The local loop passed 5 of 5 runs, and the full loop has run live in a Band room.
