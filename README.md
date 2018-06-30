# hbencode 1.1

> **Retired:** This project was originally created as part of my video transcoding
> pipeline for watching videos from my media center computer from mobile devices
>  such as my phone. However I now use [VLC Streamer] for that purpose.

[VLC Streamer]: http://hobbyistsoftware.com/vlcstreamer/

Encodes video files in bulk for playback on an iPhone or iPod Touch 
(non-retina), optimizing for space.

I have used this program for several years to encode anime, movies, 
and TV shows for my iPhone so that I can watch them while on the bus, 
on the plane, or otherwise stuck waiting for long periods of time.


## Requirements

* Operating System:
    * Mac OS X 10.5.8 (Leopard) or later
    * Linux &mdash; probably works, but untested
    * Windows &mdash; probably works, but untested
* [Python] 2.5.1 or later
    * Already included on Mac OS X.
* [HandBrakeCLI] 0.9.5 or later
    * Tested with:
        * HandBrakeCLI svn3563 (2010100201) - Reference implementation
        * HandBrakeCLI svn3567 (2010100301)

[Python]: http://www.python.org
[HandBrakeCLI]: http://handbrake.fr/downloads2.php


## Installation

Copy `hbencode.py` to somewhere in your system path.


## Usage

Encode a file using:

```
hbencode.py INPUT_FILE.avi
```

Encode all files in the current directory using:

```
hbencode.py *.avi
```

This will automagically encode the video(s) for iPhone / iPod Touch and save it
to your preferred output directory.


## Configuration and Options

When run for the first time:

1. hbencode will try to locate the `HandBrakeCLI` program in your 
   current `PATH`.
    * If it cannot be found, you will be prompted to input its location manually.
2. hbencode will prompt you for a directory to save all output files.


### Automatic Mode

If the `--auto` option is specified, all other configuration options are detected automatically.

The particular heuristic for how these options are computed may change in subsequent versions of hbencode without warning. At present the current heuristic is:

* Use an output aspect ratio which is as close to the input aspect ratio as possible.
* Use constant quality encoding.
* Use the first Japanese audio track if there is one, or the first one otherwise.
* Use the first Japanese subtitle track if there is one, or the first one otherwise.
* If there is a subtitle track, burn it in to the video.

### Aspect Ratio

The output width, height, and bitrate of the encoded video are determined by
the aspect ratio of the input file.
By default this is assumed to be `--w1` (16:9, widescreen).
This be be overridden with other options such as `--tv` (4:3, traditional TV).

You can get a complete list of supported aspect ratios with the `-r list`
option. Then use that ratio with `-r RATIO_NAME`

In the future, hbencode will try to automatically guess the aspect ratio of the
input file by default.

### Increasing Encode Quality

By default, encoding parameters optimize for constant (and small) file size.
If you prefer to optimize for constant quality, use the `-C` option.

Or if you want to multiply the automatically determined bitrate to increase
quality (for music videos and similar), you can use the `-q 1.5` option to
multiply the bitrate by 1.5x (or any value).

Finally, you can use one of the higher quality aspect ratio variants.
For example, if you normally use `-r w1` (the default), you can also use
`-r w1-hq`. See the "Aspect Ratio" section for more details.

### Subtitles

Subtitles in the input file are detected and included in the output file by
default. If you want to select a subtitle track other than the first one,
use `-s SUBTITLE_TRACK_NUMBER`.

Subtitles are normally converted to plain text and stored as a native subtitle
track for the iPhone. SSA subtitles (common in anime) can alternatively be
**burned in** to the video track using the `-B` option. Subtitle burn-in is the
most accurate way to display SSA subtitles, at the cost of not being able to
turn them off during playback.

### Other Options

You can use `-x "OPTION_1 OPTION_2 ... OPTION_N"` to specify custom options to
the underlying `HandBrakeCLI` program.

You can get a complete list of supported options by running hbencode with no
parameters:

```
hbencode.py
```


## Support

If you run into problems or have questions, feel free to file a
[bug] or [contact] me.

[contact]: http://dafoster.net/about#contact
[bug]: https://github.com/davidfstr/hbencode/issues


## Changelog

Information about earlier releases can be found in the [CHANGELOG].

[CHANGELOG]: https://github.com/davidfstr/hbencode/blob/master/CHANGELOG.md


## License

This software is licensed under the [MIT License].

[MIT License]: https://github.com/davidfstr/hbencode/blob/master/LICENSE.txt
