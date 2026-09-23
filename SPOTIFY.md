# Spotify integration contract

The workflow expects three GitHub Actions repository secrets:

```text
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
SPOTIFY_REFRESH_TOKEN
```

The refresh token should be granted the read scopes used by the profile panels:

```text
user-read-currently-playing
user-read-playback-state
user-read-recently-played
user-read-playback-position
user-top-read
```

The script does not write any secret values into the repository.

Generated files:

```text
assets/spotify-now-playing.svg
assets/spotify-queue.svg
assets/spotify-history.svg
assets/spotify-top.svg
```


## Current Spotify platform note

For newly created Spotify Development Mode apps, Spotify requires the app owner to have an active **Spotify Premium** subscription. Development Mode is intended for personal/experimental use and has user/app limits. Check the current Spotify Developer documentation before enabling the live panels.
