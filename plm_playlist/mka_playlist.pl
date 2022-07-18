#!/usr/bin/perl
# 1 ----------- ARGS

# Usage:
#	 mka_playlist.pl [-a] [-nr] PLAYLIST_NAME ["FILENAMES_PATTERN"]
# Note: Make sure to put pattern in quotes 
# 
# Mandatory argument:
# 	PLAYLIST_NAME: playlist to create or update
# 
# Optional argument:
# 	FILENAMES_PATTERN: glob expression for filenames to add into playlist. 
# 			If absent, all files would be added.
# 
# Options:
# 	-a: Append new files to end of the playlist.
#       By default, this script either creates new playlist, or completely overwrites an existing one.
#       If this option is set, and playlist had already existed, new files will be added to the end of it.
# 	-nr: Don't look for files in subdirectiories. Only files from current directory will be added.
# 		By default, all files from this directory and it's subdirectories, matching FILENAMES_PATTERN (or all files in absense of FILENAMES_PATTERN), will be added.
# 
# PLAYLIST_NAME is a name of playlist file without extension. 
# The script will create or update a playlist in the following file:
#   ~/bin/pll/PLAYLIST_NAME.txt, creating all necessary directories if needed.

use File::Path qw(make_path);
use File::Basename;

$pl_name = shift;
while ($pl_name =~ /^-(a|nr)$/) {
	# body...
	if ($pl_name eq "-a") {
		$opt_add =1;
		$pl_name = shift;
	}
	if ($pl_name eq "-nr") {
		$opt_nr =1;
		$pl_name = shift;
	}
}

$pt =shift;

if (not $pl_name)
{
	print qq{PLAYLIST_NAME is a required argument for this script.

This script creates or updates specified playlist for plm_playlist.pl using files and this directory and its subdirectories (or, optionally, this directory only).
In update mode new files are appended to existing playlist; in replace mode files are replaced completely. As an exception, in replace mode, if no files were found, playlist is not replaced.
Requirements: gnu find, pwd. 

Usage:
	mka_playlist.pl [-a] [-nr] PLAYLIST_NAME [\"FILENAMES_PATTERN\"]

Note: FILENAMES_PATTERN should be put in quotes to avoid shell expansion.

By default, all playlists are created in ~/bin/pll directory. This directory can be changed in plm_playlists.config file by setting pll_dir parameter. File plm_playlists.config should be in the same directory as mka_playlist.pl.
Playlist file name will be always PLAYLIST_NAME.txt.
FILENAMES_PATTERN filters files to add to the playlist.

Options:
	-a, don't override existing playlist, add new files to the end
	-nr, don't add files from subdirectories, only look for then in current directory
};
	exit;
}


$dir_op = ">";
$dir_op = ">>" if $opt_add;

$pll_dir = "~/bin/pll";

my $origin_dir = dirname(__FILE__);
if (-f "$origin_dir/plm_playlists.config")
{
	open (CFG,"$origin_dir/plm_playlists.config");
	while (<CFG>)
	{
		if (/^pll\_dir\s*(\S+)\s*$/)
		{ $pll_dir = $1; last; }
	}
	close(CFG);
}

$pll_dir =~ s/~/$ENV{HOME}/;
make_path ($pll_dir);

$find_rec = (not $opt_nr) ? "" : "-maxdepth 1";
$find_mask = $pt ? " -name \"$pt\" " : "";

# Finds absolute paths of all files, specified by $file_mask and $opt_nr
# Replaces or appends them in playlist
$filelist = `find \"\$(pwd -P)\" $find_rec $find_mask | sort`;
chomp $filelist;

# For replace mode only replace playlist if any files found
if ($filelist) {
  system "echo \"$filelist\" $dir_op $pll_dir/$pl_name.txt";
}

if (-f "$pll_dir/$pl_name.txt") {
	print "Resulting $pl_name playlist:\n";
	system "cat $pll_dir/$pl_name.txt";
} else {
	print "No files found in this directory" . ($pt?" with pattern $pt":"") . ". ";
	print "Playlist $pl_name.txt was not created\n";
}