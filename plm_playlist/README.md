# plm_playlist

A collection of scripts, that allows creating lists of playlists, loading a list of playlists, selecting and playing playlists from this list in mplayer in console (essentially a wrapper around mplayer). Playlists can be played in regular and pomodoro mode. In pomodoro mode additional timer is run, which determines which of the playlists currently playing should be muted, depending on the stage of pomodoro cycle.

Interface is designed to allow full functionality with minimal amount of keyboard input.

Following scripts are in the collection:
- **mka_playlist.pl** - a helper for creating playlist files.
- **plm_playlist.pl** - main script, the wrapper around mplayer. On start this scripts reads a list of playlists and/or directories. After that, it allows searching. selecting and playing playlists and/or directories from this list in mplayer. When used with `-mode` option, marks playback to be muted and unmuted during pomodoro stages when **258mute.py** pomodoro timer is run.
- **258mute.py** - the pomodoro timer. Mutes and unmutes playback that was marked by *plm_playlist.pl* with `-mode` option.

On start **plm_playlist.pl** script requires a list of playlists or directories to load. It can be given as an argument or taken from default settings (see [plm_playlist.pl](#plm_playlistpl), [plm_playlist.config](#plm_playlistconfig)).

**plm_playlist.pl** will start playback with default options of `-af scaletempo -fs -ass -loop 0`. Playlist files may be of any format, that are recognizeable by mplayer, but in one-file-per-line format may contain additional options for playback, that will be parsed by **plm_playlist.pl** and passed to mplayer.

Pomodoro cycle consist of 2 or 3 stages. To start pomodoro timer, run **258mute.py**. Number and length of stages are specified in arguments to **258mute.py**. **plm_playlist.pl** can be started with option `-mode (0|1|2)`, which means, that in pomodoro mode, playback is unmuted only during corresponding stage. The stages and corresponding `-mode` values are:
| Stage | Default length | `-mode` option for **plm_playlist.pl** | Display | Comments |
| -- | -- | -- | -- | -- |
| Work/study | 25 minutes | `-mode 0` | `work period`, `W` |
| Rest/break | 8 minutes | `-mode 1` | `rest period`, `R` |
| Additional stage | Optional stage, no default length | `-mode 2` | `add period`, `A` | Possible application for this stage may be if there's work to be done away from computer, which is needed to be interspersed with regular work/study. |


### **mka_playlist.pl** 

Playlist creation helper script. Usage:
> $ mka_playlist.pl [-a] [-nr] PLAYLIST_NAME [\"FILENAMES_PATTERN\"]

This script creates or updates specified playlist for plm_playlist player, using files in current directory and either its subdirectories(default), or just the current directory. Script has two modes:
- in create or replace mode (default) script either creates new playlist or replace an existing one. As an exception in this mode, if script doesn't find any files to add to the playlist, no changes occur - new playlist is not created, or existing playlist is not replaced. 
- in append mode new files are appended to existing playlist; or used to create new playlist if there was not one.

For control, after its work script outputs contents of resulting playlist to console in all modes. <br/>
Requirements: gnu `find, pwd`. 

Required argument:
- PLAYLIST_NAME. Name of playlist to create or update. Script will create or update playlist at `$conf{'pll_dir'}/PLAYLIST_NAME.txt`,
where `$conf{'pll_dir'}` is default directory for playlists and lists of playlists files, which defaults to `\~/.plm` unless configured otherwise. See [plm_playlist.config](#plm_playlistconfig) for details.

Optional argument:
- [\"FILENAMES_PATTERN\"]. Pattern for files to add into playlist. Be sure to use quotes to hide this argument from shell expansion. <br/>If absent, all files from current directory, with or without subdirectories will be added.

Options:
- -a (append_mode). Sets append mode. New files will be appended to existing playlist.<br/> Without this option existing playlist will be fully replaced.
- -nr (not recursive). Don't look into subdirectories for files to add to playlist, use only files in this directory.


### **plm_playlist.config**
Configuration file for plm_playlist. 
Optional. Should be located in the same directory as scripts. In its absense scripts assume default values for their parameters.


File consists of lines, each of which has format: `PARAM_NAME PARAM_VALUE`. Incorrect lines are ignored. Missing parameters are treated as having default values.


List of parameters:

| PARAM_NAME | Description                            | Default value |
| ---------- | ---------------------------------------| ------------- |
| pll_dir    | default directory for playlists and lists of playlists (and various technical files).<br/> *mka_playlist.pl* will place and edit playlists here. However, lists of playlists are edited manually, so they may include playlist files located anywhere. <br/> *plm_playlist.pl* will use this directory for looking up lists of playlists, either specified as command argument, or a default one. | \~/.plm |
| pll_list   | Filename of default list of playlists for *plm_playlist.pl*, used when no list specified as argument. Default list of playlists is looked up only at `$conf{'pll_dir'}/$conf{'pll_list'}` | \_list.txt |


### **plm_playlist.pl** 
Main script that plays playlists and directories, acting as a wrapper around mplayer. Usage:

`$	plm_playlist.pl [-mode (0|1|2)] [LIST_OF_PLAYLISTS_OR_DIRS]`

On start script always reads a file with list of playlists and/or directories (see [Playlists list file format](#playlists-list-file-format)). It will form a working list of playlists and directories using only those entries, that point to existing files or directories. This working list will not be further changed while script is running, and will be used to search and play its entries. List file location is specified in optional LIST_OF_PLAYLISTS_OR_DIRS argument and is looked up in following order:
| LIST_OF_PLAYLISTS_OR_DIRS argument is | Lookup order |
| -- | :-- |
| present | `$cwd\LIST_OF_PLAYLISTS_OR_DIRS` <br/> `$conf{'pll_dir'}\LIST_OF_PLAYLISTS_OR_DIRS` |
| absent | `$conf{'pll_dir'}\$conf{'pll_list'}` |

where `$cwd` is current directory and `$conf{'pll_dir'}` and `$conf{'pll_list'}` are configuration parameters for directory for playlist files and default listfile name respectively from *plm_playlist.config* (see [plm_playlist.config](#plm_playlistconfig)). 

*plm_playlist.pl* would only start successfully if will manage to create working list of at least one entry. 

Option:
- -mode (0|1|2) - mark playback for being muted/unmuted in pomodoro mode. When this option is specified, pomodoro timer **258mute.py** will unmute playback only during corresponding pomodoro stage. Only modes 0, 1 and 2 are supported, which set playback to be unmuted in work/study, rest/break or additional pomodoro stage respectively. This option doesn't have effect outside of pomodoro mode.

#### Modes of operation

Script has several groups of modes of operations. In each group, only one mode is active at any time, and they can be cycled by user in each group independently. 

Two main modes of operation are playback mode, when a playlist or directory is played with mplayer, and standby mode, when script waits for and performs user instructions. In standby mode user can search and select playlist or directory to play, start playback, exit script or change other modes of operations. 

Other groups of modes are: 
- **Delay modes**. User can instruct script to wait specified amount of time on entering playback mode before starting actual playback. Default delay mode is no delay, start playback immediately. <br/> Available options are cycled by pressing `d` (only when search_mode is off) or `Cntr-D`. <br/> Available options are: **no delay** (immediate playback), delay of **2 minutes, 5 minutes, 10 minutes** and **20 minutes**. <br/>
TODO: Add list of delay modes to configuration parameters (as a workaround, it is possible to edit values for @delay array in the script). <br/>Add delay timer indicator. <br/>Currently, when script starts the delay timeout on entering playback mode, there is no means to cancel it other than restarting the script completely - better have such possibility.
- **Search modes**. Can be **off** (default) and **on**. Switched by pressing `F1`. <br/> In search mode playlists and directories can be searched and selected by pressing letter keys. Following Latin and Cyrillic keys are supported: `a-zA-Zа-яА-Я`. After pressing the key script will perform case-insensitive search for either a playlist with filename starting with this letter, or directory, in which last directory will start from the same letter, whichever comes first, starting from the current entry. Lowercase letters do a forward search and uppercase letters - backwards search. Pressing the same key repeatedly will cycle through all existing playlists or directories in which filename or last directory start from this letter, respectively. <br/> When search mode is off, the only way for user to browse list of playlists and directories is to scroll forward or backwards. `Up` and `Right` will show next entry in the list, while `Down` and `Left` - previous entry. List scrolling works regardless of search mode. <br/> TODO: implement search by other letters and symbols.
- **Video modes**. As explained in [Playlist files format](#playlist-files-format), each playlist has its own set of options which are passed to mplayer. Among them may be `-novideo` option to suppress playing video. Video modes modify applying this option to playback mode. <br/> Following modes exist: **no modification** - no modifications applied, **no video** - `-novideo` option always added, **force video** - `-novideo` option not passed to mplayer even if it was specified for playlist. <br/> Video modes are switched by pressing `v` (only when search mode is off) or `Cntr-V`.  

Every time when any mode is changed (except from going from standby mode to playback mode), or a new entry in list of playlists and directories is selected, information about current state is printed to console. Following information is given:
- Always: currently **selected playlist or directory**, (press `Enter` to play current entry with mplayer). <br/>If exist: **category** and **subcategory** of current entry (see [Playlists list file format](#playlists-list-file-format))
- Always: **Delay mode** information and **Search mode** information
- **Video mode** information - only for **no video** and **force video** modes


#### Playlists list file format
File with list of playlists and directories should consist of lines of format:

`PLAYLIST_OR_DIRECTORY [CATEGORY[.SUBCATEGORY]]`

,where:
- PLAYLIST_OR_DIRECTORY is an absolute path to a playlist or a directory, 
- CATEGORY and SUBCATEGORY are arbitrary optional strings, describing kind of a playlist or directory. In playback mode script modifies its window title to include CATEGORY of the current entry playing. Both CATEGORY and SUBCATEGORY are printed to console as current entry details in standby mode.

All lines with incorrect format, including lines that do not point to existing file or directory, are silently ignored. <br/>
TODO: Watch for filesystem changes and update working list of playlists accordingly. Exclude playlists with incorrect format.

#### Playlist files format
Playlist files can be of any regular mplayer playlist format. For one-file-per-line format additional lines are allowed, which will specify additional options to pass to mplayer when playlist will be played. These lines will be interpreted by *plm_playlist.pl* and ignored by mplayer. 

Format of these additional lines are simply sequence of options as they should appear in the command line. Currently, for *plm_playlist.pl* to recognize a line in playlist as additional options line, it should start with one of the following options: `-aid|-speed|-shuffle|-novideo|-ss|-loop|-cache`. If you have to pass any other option to mplayer, but not one of those, start line with `-loop 0`, this will be ignored, as such option is already in default ones.

Default options that are passed to mplayer, are: `-af scaletempo -loop 0 -fs -ass`.

*plm_playlist.pl* does following modifications: 
- if `-loop` option is specified in additional options, the default one is dropped and value of loops specified in additional lines is used (so while by default playlist is looping forever, number of loops can be limited by additional options).
- if script is **no video** video_mode, `-novideo` option is added to all other options; if script is in **force video** video mode - `-novideo` option is removed from additional options, if it was there.

Other than that *plm_playlist.pl* concatenates all options from additional option lines, making no checks and puts them to command line as is.

TODO: Rework whole additional options lines mechanism. At the very least, clarify recognition pattern for additional options lines and add some safeties for option merges. Furthermore, each additional option line should provide options only for files that follow in the next lines. For that, rather than starting *mplayer* with `-playlist` option, script should play files individually, which will require bunch of other modifications - like support for moving to previous track in playlist - and will be implemented really later on if at all.

##### Keyboard control
- **Up, Right**. Select next playlist or directory from loaded list of playlists/directories. 
- **Down, Left**. Select previous playlist or directory. 
- **Enter**. Enter playback mode and start playback of selected playlist or directory with mplayer (possibly after amount of time, specified in delay mode). The script will return to standby mode when mplayer will exit.
- **F1**. Search mode on/off. In search mode, playlists are searched by the first letter of playlist file name.
- **a-z,а-я**. Only in search mode. Do a case-insensitive forward search for playlist or directory, using typed letter. Looks for either playlist with filename, that starts with matching letter, or directory path, where last directory starts again from the same letter.
- **A-Z,А-Я**. Only in search mode. Do the same search as above, only in backwards direction.
- **q,w,a,s** keys (only when search mode is off), **F9, F10, F11, F12**. Quit script.
- **d** key (only when search mode is off), **Cntr-D**. Switch delay_mode. Sets delay after user presses `Enter` before playback starts. Cycles through following values of delay: 0 (no delay, default), 2 minutes, 5 minutes, 10 minutes, 20 minutes.
- **v** key (only when search mode is off), **Cntr-V**. Switch video_mode. Cycles through following modes: "no video mode enabled" (no additional changes), "no video", "force video". See comment above.
