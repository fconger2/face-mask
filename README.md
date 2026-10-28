# face-mask
Different NFL Games to Enjoy!

Play at **https://fconger2.github.io/face-mask/**

NFL skill-player games: Mystery Player, Higher or Lower, Grid, Draft Day and Blurry Box Score, plus the Four Downs word puzzle.

- `index.html`: the Face Mask site (built file; don't edit by hand)
- `templates/face-mask.tpl.html`: the page source, edit this one
- `scripts/build.py`: downloads the latest [nflverse](https://github.com/nflverse/nflverse-data) rosters, stats and draft picks and rebuilds `index.html`
- `scripts/stars.txt`: the well-known players the mystery answers are drawn from (`Name|POS`, one per line)
- `.github/workflows/update.yml`: runs the build every Tuesday morning and commits the result

To update right away: Actions tab → "Weekly data update" → Run workflow.
