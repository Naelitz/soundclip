# SoundClip
Simple sound cue management for linux (Like [Q-Lab (Mac OS X)](http://figure53.com/qlab/) or [MultiPlay (Windows)](http://www.da-share.com/software/multiplay/))

![](http://techwiz24.github.io/soundclip/2015/03/15/Sound-Standing-By/gui.png)

## Project Status
SoundClip is currently under heavy, active development in an attempt to have it reliable enough to be used in a production
in March. Right now, basic audio playback works, but is **NOT PRODUCTION READY** yet. I try to keep the [dev blog](http://techwiz24.github.io/soundclip)
up to date, you can get the most recent project status update there.

## Planned Features
Below is a list of features I want to add, listed in order of importance

* [x] Basic Audio Cues
* [ ] Adjustable Playback Parameters (Pitch / Gain / Fade / EQ / etc.)
* [ ] Automation Cues
* [ ] Looping / Holds
* [ ] Import-Export of projects to/from other systems
* [ ] Remote-Control via OSC or similar
* [ ] Virtual Channels / `jack` integration
* [ ] D-Bus Service
* [ ] Video Cues?
* [ ] MIDI Cues?
* [ ] Developer Library / Plugins / Custom Cue support

## License
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Productions (program output) and all related files are considered derivative works and are therefore not governed by this license. Projects you produce with this program are considered your own; you may do what you want with them as long as the copy-right notice is maintained if you distribute SoundClip along with them. It'd also be nice to mention SoundClip in your show booklet or to your colleagues, but that's up to you.

## Running SoundClip
Make sure you have `PyGObject` and the python `gstreamer` bindings installed. You will need `python3`

Simply execute the `soundclip` script located in the `src` directory and you should be up and running with a blank production. Eventually, command line arguments will be implemented that will allow you to specify a project to open at startup (or even the most recent one)
