# tandem race app

simple tandem race app with two pages:
- operator page: `http://localhost:8080/`
- scoreboard page: `http://localhost:8080/scoreboard`

## run

```bash
python app.py
```

## features

- phase 1 registry: add teams with number and name
- phase 2 race:
  - start race (3h)
  - +1 lap per team
  - revert last lap per team
  - manual lap entry with duration
  - magic lap entry using mean lap duration
- phase 3 finish:
  - finish race and lock results
  - final charts:
    - laps over time
    - lap duration over time

## notes

- state is in-memory only in v1 (restart resets race data)
- backend is python (bottle), frontend is html/css with lightweight js polling
