# Deploying MooiBanana on the VPS

`start.sh` runs Gunicorn in the **foreground** on purpose (migrations →
collectstatic → `exec gunicorn`). That is what a container (see `Dockerfile`)
needs, and it is also what a process supervisor needs. Do **not** background
Gunicorn inside `start.sh` — let the supervisor own it.

## Recommended: systemd (survives logout, auto-restarts, starts on boot)

```bash
# 1. Install the unit
sudo cp /root/mooibanana_project/deploy/mooibanana.service /etc/systemd/system/mooibanana.service

# 2. Load + enable (start now, and on every boot)
sudo systemctl daemon-reload
sudo systemctl enable --now mooibanana

# 3. Check it
systemctl status mooibanana --no-pager
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/   # expect 200/302
```

Everyday commands:

```bash
sudo systemctl restart mooibanana     # after pulling new code
sudo systemctl stop mooibanana
journalctl -u mooibanana -f           # live logs (Gunicorn access/error)
```

Tune worker count without editing code — set `WEB_CONCURRENCY` in the unit
(`Environment=WEB_CONCURRENCY=3`) then `daemon-reload` + `restart`. Default is
`(2 x CPU cores) + 1`.

## Quick alternative: nohup (NOT recommended for production)

Dies on reboot and does not restart on crash — only for a throwaway test:

```bash
cd /root/mooibanana_project
nohup ./start.sh > gunicorn.out 2>&1 &
disown
tail -f gunicorn.out
```

Stop it with: `pkill -f 'gunicorn mooibanana_project.wsgi'`

## openresty (reverse proxy) must point at Gunicorn

The 502 you saw was openresty reaching a dead upstream. Its `proxy_pass` must
target `http://127.0.0.1:8080`:

```bash
sudo nginx -T 2>/dev/null | grep -nE "proxy_pass|server_name|listen "
```

## WebSockets note (django-channels)

This project has `channels` in `INSTALLED_APPS`, but `start.sh` serves the
**WSGI** app, so WebSocket routes (chat / live updates) will not work over
`gunicorn ... wsgi`. If you need real-time features, run the ASGI app instead,
e.g. with uvicorn workers:

```bash
pip install uvicorn
exec gunicorn mooibanana_project.asgi:application \
    -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 --workers 3
```

(Left as WSGI by default so the current HTTP deploy is unchanged.)
