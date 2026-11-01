# YouTube Shorts: free-host feasibility test

This is an isolated hosting experiment, not the public blog downloader.
It uses yt-dlp directly, with Node.js and FFmpeg. It uses no Yoinku,
paid download API, browser cookies, proxy, or YouTube account.

## What is being tested

The service downloads the owner's fixed public test Short, then verifies:

- an MP4 was actually downloaded, at most 64 MiB;
- video and audio tracks are present;
- duration is at most three minutes;
- the file's SHA-256 hash and media details can be reported.

The temporary MP4 is deleted after verification. Successful metadata extraction
alone does not count as a successful hosting test.

## Render test deployment

Use the files in this folder as the deployment source root. `render.yaml`
specifies a **free** Docker web service in Frankfurt. The owner must connect
their Render account and confirm free capacity is available. Do not select a
paid instance, add paid storage, or enable paid upgrades for this experiment.

`HOST_TEST_TOKEN` must be a private random value of at least 32 characters.
Render's Blueprint can generate it. Never commit the value to a repository.
`HOST_TEST_VIDEO_URL` defaults to the owner's supplied test Short in the
Blueprint. The web endpoint cannot accept another URL.

Once deployed:

1. Request `GET /health` and confirm HTTP 200.
2. Make an authenticated `POST /probe` with an empty body or `{}` and
   `Authorization: Bearer <private token>`.
3. Count the result as a download success only when `ok` is true and
   `result` is `download_verified`, with both audio and video in `media`.
4. Record the host, region, timestamp and returned verification details.
5. If blocked, record the failure and stop. Do not add accounts, cookies,
   proxies, or paid APIs to work around it.

There is one active probe at a time and at most three probes per process
lifetime. The service returns verification JSON, not a public video file.
No blog integration should be activated before a cloud test succeeds.

## Important free-tier limits

Render's free web services sleep after 15 minutes idle and can take about one
minute to wake. They have ephemeral storage and workspace usage limits.
Render explicitly describes free instances as unsuitable for production.
This makes the free tier useful for this feasibility test, not a promise of
fast or reliable public downloads. A successful test also does not guarantee
YouTube will continue accepting the host's IP address.

Check the current official limits before deployment:

- https://render.com/docs/free
- https://render.com/docs/blueprint-spec
- https://github.com/yt-dlp/yt-dlp/wiki/EJS

## Local checks

Run `python -m unittest discover -s . -p test_app.py -v` from this folder.
Those tests cover validation, authentication and the test-run limit with a
fixture; they do not test YouTube or Render.

For a real local probe, install `requirements.txt`, ensure Node.js and
`ffprobe` are on PATH, set `HOST_TEST_VIDEO_URL`, and run `python probe_worker.py`.
Keep local results clearly separate from cloud results.

The blog's one-article-daily 09:00 UTC schedule and Telegram publishing
notifications are outside this experiment.
