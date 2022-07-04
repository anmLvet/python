#!/usr/bin/python3
import os
import argparse
import re

parser =\
    argparse.ArgumentParser(description='Information about memory usage. '
                            + 'Sums resident memory usage as given by smem,'
                            + ' when it takes shared libs in account.'
                            + ' Requires smem.')
parser.add_argument('-p', '--proc_names', default='mem-usage-list.txt',
                    help='A file with list of process names'
                    + ' to show stats about.')
parser.add_argument('-ff', '--ff-dump-file', help='Optional. Memory dump file '
                    + 'from about:memory page in Firefox. (press \'Measure\' '
                    + 'and then copy-paste to a file)',
                    required=False)
args = parser.parse_args()


def print_sum(app):
    app = app.rstrip()

    # customize script output
    app_name = app
    app_name = app_name[0].upper() + app_name[1:8]
    app_name = app_name.ljust(9)

    app = f"[{app[0].upper()}{app[0].lower()}]{app[1:]}"
    cmd = f"smem -P {app}" + "| awk '{print $6;}' | awk '{ sum += $1 } END { "\
          + f"printf(\" {app_name}total by smem:" + " %\\047d\\n\",sum) }'"
    os.system(cmd)


os.system("smem | awk '{print $6;}' | awk '{ sum += $1 } END { "
          + "printf(\" All      total by smem: %\\047d\\n\",sum) }'")

if (not os.path.isfile(args.proc_names)):
    print("File with app list not found. Default output only.")
else:
    with open(args.proc_names) as f:
        for app_line in f:
            print_sum(app_line)

# Chrome

print('')
print('Chrome details:')

CHROME_PARA_RE =\
    re.compile(r"^(?P<head>.*)--enable-crashpad"
               + r" --crashpad-handler-pid=\d+"
               + r" --enable-crash-reporter=[a-f\-,\d]+"
               + r"\s*(?P<ep>--extension-process|)"
               + r"\s*--display-capture-permissions-policy-allowed"
               + r" --change-stack-guard-on-fork=enable --lang=en-US"
               + r" --num-raster-threads=(?P<nrt>\d+)"
               + r" --enable-main-frame-before-activation"
               + r" --renderer-client-id=(?P<rcid>\d+)"
               + r" --launch-time-ticks=(?P<ticks>\d+)"
               + r" --shared-files=v8_context_snapshot_data:100"
               + r" --field-trial-handle=[i,\d]+(?P<tail>.*)$")

os.system("smem -P chrome")
with os.popen("ps auxw | grep chrome | sort -n -r -k6") as c:
    for cl in c:
        m_cl = CHROME_PARA_RE.match(cl)
        # Parse chrome ps output for renderer type of processes
        if (m_cl is not None):
            cf_ep = "" if (m_cl.group('ep') == "") else 'ep'
            cf = f"{m_cl.group('head')} {cf_ep} nrt={m_cl.group('nrt')} "\
                + f"rcid={m_cl.group('rcid')} {m_cl.group('ticks')}"\
                + f"{m_cl.group('tail')}"
            print(cf)
        else:
            print(cl, end="")

# Firefox

print('')
print('Firefox details:')

print_sum('firefox')
os.system("smem -P firefox")

if (args.ff_dump_file is not None):
    if (os.path.isfile(args.ff_dump_file)):
        with (open(args.ff_dump_file)) as f:
            last_lines = [None, None, None]
            for line in f:
                # Parse ff about:memory details
                if (line.find("explicit") > 0):
                    print(' '.join(line.split()[0:2]), last_lines[0])
                elif (line.find("top(ht") > 0):
                    line_display = line.rstrip()
                    if (len(line_display) > 140):
                        line_display = line_display[:140]
                    print(line_display)
                last_lines.append(line.rstrip())
                del last_lines[0]
    else:
        print('Didn\'t find Firefox memory dump file')
else:
    print('Firefox memory dump file was not provided')
