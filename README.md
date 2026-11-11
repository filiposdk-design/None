# Home Theater: a remote-friendly player for Android TV

A small media server for your home network, with a full-screen interface you control with the TV remote.
It plays video files you own (for example, a backup of your own Blu-ray or DVD, or home videos).

## Run it (on a computer on the same Wi-Fi as your TV)

```bash
python3 server.py                      # serves ./media on port 8080
python3 server.py --media ~/Movies     # or point it at any folder
```

It prints a link like `http://192.168.1.23:8080`. Open that link in the TV's browser
(TV Bro and Puffin TV work well on Android TV). You can also add it to your home screen.

You need Python 3.8 or newer, and nothing else to install. If the TV can't connect, allow port 8080 through your computer's firewall.

## Remote controls

| Key | Library | While playing |
| --- | --- | --- |
| ◀ ▲ ▼ ▶ | Move between movies | With controls hidden: ◀ goes back 10s, ▶ skips 30s. With controls showing: move between buttons |
| OK | Play | Shows the controls, or presses the selected button |
| Back | | Hides the controls, or closes the player |
| Play/Pause, FF, RW | | Work as expected |

The player switches to full screen automatically, remembers where you stopped, and shows a progress bar on each movie.

## Media folder tips

- **Format:** MP4 (H.264 video with AAC audio) plays almost everywhere. Some TVs can't play MKV or HEVC in the browser. To convert one: `ffmpeg -i in.mkv -c:v libx264 -c:a aac out.mp4`
- **Poster:** add `Movie.jpg` next to `Movie.mp4`
- **Subtitles:** add `Movie.en.vtt`. Press the CC button to cycle through them. To convert `.srt` files: `ffmpeg -i Movie.srt Movie.en.vtt`
