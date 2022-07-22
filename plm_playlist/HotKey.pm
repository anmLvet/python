# HotKey.pm
package HotKey;

# Hotkey.pm is taken from Perl CookBook, by Tom Christiansen published by O’Reilly Media, Inc., ISBN 0596003137
 
use strict;
use warnings;

 
use parent 'Exporter';
our @EXPORT = qw(cbreak cooked readkey);

 
use POSIX qw(:termios_h);
my ($term, $oterm, $echo, $noecho, $fd_stdin);

 
$fd_stdin = fileno(STDIN);
$term     = POSIX::Termios->new();
$term->getattr($fd_stdin);
$oterm     = $term->getlflag();

 
$echo     = ECHO | ECHOK | ICANON;
$noecho   = $oterm & ~$echo;

 
sub cbreak {

    $term->setlflag($noecho);  # ok, so i don't want echo either
    $term->setcc(VTIME, 1);
    $term->setattr($fd_stdin, TCSANOW);

}

 
sub cooked {

    $term->setlflag($oterm);
    $term->setcc(VTIME, 0);
    $term->setattr($fd_stdin, TCSANOW);

}

 
sub readkey {

    my $key = '';

    cbreak();

    sysread(STDIN, $key, 1);

    cooked();

    return $key;

}

 
END { cooked() }

 
1;