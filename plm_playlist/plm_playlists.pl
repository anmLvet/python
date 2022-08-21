#!/usr/bin/perl
use File::Basename;
use lib dirname (__FILE__);
use HotKey;
use IO::Handle;
use utf8;
use Encode;

#use TreeLeaf;
$|=1;
$deb=1;

print("\e]0;plm\7");



# ******0.1. Init data ********
@delay = (0,2,5,10,20);
$delay_ptr = 0;

$search_mode = 0;
$video_mode = 0; # 0 dont' change, 1 - no video, 2 - force video

# Directory for playlists is taken from plm_playlists.config if exists,
# as pll_dir parameter
$conf{'pll_dir'} = "~/bin/pll";
$conf{'pll_list'} = "_list.txt";

my $origin_dir = dirname(__FILE__);
if (-f "$origin_dir/plm_playlists.config")
{
	open (CFG,"$origin_dir/plm_playlists.config");
	while (<CFG>)
	{
		if (/^(\S+)\s*(\S.*\S|\S)\s*$/)
		{ $conf{$1} = $2;  }
	}
	close(CFG);
}
$conf{'pll_dir'} =~ s/~/$ENV{HOME}/;

$heart_options = '';
if ($conf{'heart_cmd'}) {
 	$heart_options = "-heartbeat-cmd \"$conf{'heart_cmd'}\" ";
	if ($conf{'heart_int'}) {
	 	$heart_options .= "-heartbeat-interval $conf{'heart_int'} ";
	}
}

# ******0.2 Open LOG ***********
open(LOG,">>$conf{'pll_dir'}/debug.log");
LOG->autoflush(1);
print LOG "{\n";
print LOG "\t\"start\" : \"" . time_string() . "\",\n";
print LOG "\t\"keys\" : [\n";
$log_divider = '';

# ***** 0.3. Read ARGs *********
print qq{Wrapper around mplayer for manipulating multiple playlists with few simple commangs.

Usage:
    plm_playlist.pl [-mode (0|1|2)] [LIST_OF_PLAYLISTS_OR_DIRS]

A list of playlists or directories is required for plm_playlist.pl with containing path to at least one existing file or directory. If LIST_OF_PLAYLISTS_OR_DIRS argument is provided, the list is looked up first in current directory, then in \$conf{'pll_dir'}. With no LIST_OF_PLAYLISTS_OR_DIRS argument list of playlists will be looked up at \$conf{'pll_dir'}\\\$conf{'pll_list'}. Here \$conf{'pll_dir'} and \$conf{'pll_list'} are configuration parameters, that can be configured in plm_playlists.config file.

Option:
    -mode (0|1|2) - configures playback for use with pomodoro mode. If this option is specified and pomodoro timer 258mute.py is run, playback will be unmuted only during corresponding pomodoro stage and unmuted during other stages. Stage correspondence is:
    0 - work/study stage
    1 - rest/break stage
    2 - additional stage (if present).
    Only values of 0,1 or 2 are allowed. Option -mode should be specified before LIST_OF_PLAYLISTS_OR_DIRS.

Keys:
    Up, Right - next entry
    Left, Down - previous entry
    Enter - start playback
    F1 - search mode on/off
    [a-zа-я] - forward search in search mode only. Looks for first letter of playlist filename or last directory name
    [A-ZА-Я] - backward search, search mode only.
    F9,F10,F11,F12, and if search mode is off: [qasw] - exit
    Cntr-D, and if search mode is off: d - switch delay mode
    Cntr-V, and if search mode is off: v - switch video mode (no option alterations, no video, force video)

};

$lst = shift;

# ***** 0.3.1.  -258 ***********

$new258 = '';
$mode258 = '';

if ($lst eq '-mode') {
	$new258 = "$$";	
	$mode258 = shift;
	unless ($mode258 =~ /^[012]$/) {
		print "Unsupported mode $mode258. Only modes 0,1 or 2 are supported.";
		exit;
	}
	$lst = shift;	
}

check_258($new258, $mode258);

# ****** 0.3.2.  filelist or playlist *****

if ($lst and not -f $lst) {
	$lst = $conf{'pll_dir'} . "/" . $lst;
	# body...
}
elsif (not $lst) {
	$lst = $conf{'pll_dir'} . "/$conf{'pll_list'}";
}

#$tree = TreeLeaf->new ();


# *******0.4 Check exist and load files list *****
# *****   into @pll ******************************

# ld pl lst
open (S,$lst);

while (<S>)
{
	chomp;
	@pts = split;
	if (-d $pts[0]  or -f $pts[0]  ) {
		push @pll,$pts[0]  ;
        $ctg{$pts[0]} = $pts[1];
	}
	#if (-d $_  or -f $_  ) {
	#	push @pll,$_  ;
	#}
}

close(S); 

if ($#pll < 0) {
	print "There should be at least 1 playlist\n";
	exit;
}

# ************ 1.0 ** Main part parameters **********

$ptr = 0;
info();

# $keyback = "yuiophjklbnmнгшщзхъролджэитьбю";
$keyquit = "qwasйцфы";
$keydelay = "dв";
$keyvideo = "vм";
# wt
$play_options = "";

# ******* 1.1 Main cycle ***************

while (1) {


# ******* 1.2 Read key, unicode modification ******

	$key = readkey();
	log_key($key);

	if (ord($key) >= 0xc0) {
		# utf8 - 2 bytes only
		$key2 = readkey();
		log_key($key2);
		$key .= $key2;
	}

	$key = decode("UTF-8",$key);
# ******** 2. Main operation mode selection *****

	if ($search_mode and ( $key =~ /[a-zA-Z\x{0410}-\x{044F}ёЁ]/u )) {
		# ****** 2.1 Search by key ********
    	log_result("Search $key");
    	search($key);       
	} elsif ($keyquit =~ /\Q$key/i) {
		# ******* 2.2 Quit ****************
		log_result("Quit");
		last;
	} elsif (($keydelay =~ /\Q$key/i) or (ord($key) eq 4)) {
		# ******** 2.4 Enter start delay *****
		log_result("Delay");
		ndelay();
	} elsif (($keyvideo =~ /\Q$key/i) or (ord($key) eq 22)) {
		log_result("Video mode");
		nvideo();
	} elsif (ord($key) eq 27) {
		log_result("processing escape...");
		$key = readkey();
		log_key($key);
		if ($key eq "[") {
			$key = readkey();
			log_key($key);
			if ($key =~ /[AC]/) {
				# ******** 2.5 == 2.3.2 Navigation forward ****
				log_result("Forward");
				nlst();
			} elsif ($key =~ /[BD]/) {
				# ******** 2.5 == 2.3.2 Navigation forward ****
				log_result("Back");
				plst();
			} elsif (ord($key) eq 50) { # F9 .. F12
				# ******** 2.6 == 2.2.2 Quit 2nd variant ******
				readkey();
				readkey();
				log_result("Quit");
				last;
			}
		} elsif (ord($key) eq 79) {
			$key = readkey();
			log_key($key);
			if (ord($key) eq 80) { # F1
				# ********* 2.7 Toggle search ************
				log_result("Search");
				toggle_search();
			}
		} 
	} elsif ($key eq "\n") {
		# ********** 2.8 Play ***************
		log_result("Play");
		playcurr();
		info();
	} 
}


# **** 3. Ending section *************

print LOG "\t]\n";
print LOG "}\n";



# ----- A (for 2.8) Play current playlist --------

sub playcurr {
	# 220714 Fix for delay_mode
	if ($delay[$delay_ptr] > 0) {
		print "Playback will start after $delay[$delay_ptr] minutes...\n";
	}
	sleep 60*$delay[$delay_ptr];

	$current = $pll[$ptr];
	# 220511 Remove lowercase for categ
	$low_categ = "$ctg{$current}";
	title($low_categ . " " . basename($current));
	if (-f $current) {
		# 1.MY playlist style
		chdir dirname($current);
		@fl2play=();
		$spec_loop =0;
		#$mode='';

		# 1.1 "предпросмотр"
		open (PP,$current);
		while (<PP>) {
			chomp;
			if (-f) {
				push @fl2play;
			} elsif (/^\s*-(aid|speed|shuffle|novideo|vo|ss|loop|cache)/) {
				$play_options .= "$_ "; # $play_options contains all current options 
				$spec_loop = 1 if ($play_options =~ /-loop/);
			# TODO: implement balabolka mode
			# } elsif (/^\s*-balabolka/) {
			# 	$mode = 'balabolka';
			} 
		}
		close(PP);
		$play_options .= " -loop 0 " unless $spec_loop;
		$play_options .= " -vo null " if (($video_mode eq "1") and not ($play_options =~ /-vo null/));
		$play_options =~ s/-vo\s*null// if ($video_mode eq "2");
		$play_options =~ s/-novideo// if ($video_mode eq "2");


		# TODO: implement balabolka mode (reader with sync text)
		# if ($mode eq 'balabolka') {
		#	 debug("mplayer -af scaletempo $play_options -fs -ass -playlist $current");
		#	 foreach my $x (@array) {
				# split filen
				# find track len
				# template
				# wait 4 keys
		#	 }
		#	 system "mplayer -af scaletempo $play_options -fs -ass -playlist $current";
		# } else {        	
		debug("mplayer -af scaletempo $play_options $heart_options -fs -ass -playlist $current");
		system "mplayer -af scaletempo $play_options $heart_options -fs -ass -playlist $current";
		# }
		$play_options="";
	} elsif (-d $current) {
		# 2.obligatory mplayer plays directory - no playlist
		chdir $current;
		debug("dir $current; mplayer -af scaletempo $play_options $heart_options -fs -ass -loop 0 *");
		system "mplayer -af scaletempo $play_options $heart_options -fs -ass -loop 0 *";
	} 
}

# ----- B (for 2.1, 2.7) Search for playlist ----------

sub search {
	$search_for = $_[0];
	$direction = 1;
	if ($search_for =~ /[A-Z\x{0410}-\x{042F}Ё]/u)  
	{ $direction = -1; }

	$search_for = lc($search_for);

	$max_steps = $#pll+1;
	while ($max_steps > 0)
	{
	    ($direction > 0 ? nlst() : plst());
		$current_filename = fileparse($pll[$ptr]);
		$current_filename = decode("UTF-8",$current_filename);
		last if (lc($current_filename) =~ /^$search_for/iu);
		$max_steps--;
	}
	unless($max_steps)
	{
		print encode("UTF-8","No playlists starting with $search_for\n");
	}
}

sub toggle_search {
	$search_mode = 1 - $search_mode;
	info();
}

# ----- C (for 2.3, 2.5) Navigation forward and backward ------

sub nlst {
    $ptr++;
    $ptr = 0 if ($ptr > $#pll);
    info();
}

sub plst {
    $ptr--;
    $ptr = $#pll if ($ptr < 0);
    info();
}

sub info {
	# body...
	print "Current playlist:\n$pll[$ptr]\t" . $ctg{$pll[$ptr]} . "\nStart delay $delay[$delay_ptr] mins\n";
	print "Search mode " . ($search_mode?"on":"off") . "\n";
	print (($video_mode eq "1")?"No video\n":"Force video\n") if $video_mode > 0; 
    title();
}

sub title {
	$track = @_[0];
	$title_mode = ($mode258 ne ''?"M$mode258" : '' ) . ($search_mode?'S':'');
	$title_mode = ' '.$title_mode if ($title_mode ne '');
	print("\e]0;plm$title_mode $track\7");
}

# ------ D. (for 2.4) for delay and video modes--------------------

sub ndelay {
	$delay_ptr++;
	$delay_ptr = 0 if ($delay_ptr > $#delay);
	info();
}

sub nvideo {
	$video_mode++;
	$video_mode = 0 if $video_mode > 2;
	info();
}

# ---- E. Set 258 flag -----------------

sub check_258 {	

	my ($current_pid, $current_mode) = @_[0..1];
    $current_mode = 0 unless defined $current_mode;

	@pid258 = ();
	@modes258 = (); 
	if ($current_pid) {
		push @pid258, $current_pid;
		push @modes258, $current_mode;
	}
	open (PID,"$conf{'pll_dir'}/period_play.pid");
	while (<PID>)
	{
		chomp;
		($apid ,$amode) = split (/\s+/,$_);

		$pid_info = `ps $apid`;
		if ($pid_info =~ /plm_playlist.*-(258|mode)/)
		{
			push @pid258, $apid;
			push @modes258, $amode;
		}
	}
	close(PID);

	# open (PID,">$conf{'pll_dir'}/258.pid");
	# foreach $pid (0..$#pid258)
	# {
	# 	if ($modes258[$pid] eq "0") {
	# 		print PID "$pid258[$pid]\n";
	# 	}
	# }
	# close(PID);

	open (PID,">$conf{'pll_dir'}/period_play.pid");
	foreach $pid (0..$#pid258)
	{
		print PID "$pid258[$pid]\t$modes258[$pid]\n";
	}
	close(PID);
}

# ------- L. Logging ---------------------

sub debug {
	print "debug: @_" if $deb;
}

sub log_key {
	my $lkey = $_[0];
	my @vals = ();
	push @vals, val_string("key",$lkey);
	push @vals, val_string("code",ord($lkey));
	push @vals, val_string("time",time_string());
	print_obj(@vals);
}

sub log_result {
	print_obj(val_string("result",@_[0]));	
}

sub print_obj {
	print LOG "\t\t$log_divider {" . join(",",@_) . "}\n";
	$log_divider = ",";
}

sub val_string {
	my $result = sprintf "\"%s\" : \"%s\"", $_[0], $_[1];
	return $result;
}

sub time_string {
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) =
                                            localtime(time);
    my $time_string = sprintf "%02s.%02s.%04s %02s:%02s:%02s",$mday,$mon,$year+1900,$hour,$min,$sec;
    return $time_string;                                            
}




