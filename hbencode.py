#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 
# Encodes video files using HandBrake for the iPhone and iPod Touch (2nd gen)
# (non-retina), optimizing for space, and drops them to a destination directory.
# 
# Requires: Python 2.5.1 or later
# 
# Copyright (c) 2012 David Foster
# 

import getopt
import os
import os.path
import subprocess
import sys

# ------------------------------------------------------------------------------
# Constants

PREFERENCES_FILEPATH = os.path.join(os.path.expanduser('~'), '.hbencode_prefs')

# iPod Touch (2nd gen) has resolution 480 x 320
# Medium-quality target resolution is 360 x 240
# PAR (Pixel aspect ratio) makes these numbers appear a bit weird
RATIOS = {
    # 4:3
    'tv':       {'vb': 196, 'w': 320, 'h': 240},
    'tv-hq':    {'vb': 352, 'w': 432, 'h': 320},
    
    # 16:9
    'w1':       {'vb': 230, 'w': 432, 'h': 240},
    'w1-hq':    {'vb': 333, 'w': 480, 'h': 272},
    'w1-hq2':   {'vb': 470, 'w': 576, 'h': 320},
    
    # 2.39
    'w3-hq':    {'vb': 255, 'w': 480, 'h': 208},
    
    'same':     {'absame':None}
}

# ------------------------------------------------------------------------------

def main(args):
    # Visually separate the program invocation line from the program output
    print
    
    # Parse arguments
    opts, args = getopt.getopt(args, 'r:s:x:STBq:C', ['vb=', 'tv', 'w1', 'sb', 'test'])
    
    if len(args) == 0:
        exit("""syntax: hbencode.py [<ratio>] [<modifiers>] (FILE ...)
    
    Aspect ratio:
        -r RATIO_NAME
        
        --w1 (DEFAULT)
        --tv
    
    Modifiers:
        -S                      Scan only.
        -T, --test              Test encode. First 30 seconds only. Open result file automatically.
        
        -s SUBTITLE_TRACK       Select subtitle track. Default is 1.
        --sb, -B                Burn the subtitle track. This is what you want if it is SSA.
        
        -q QUALITY_MULTIPLIER   Multiplies video bitrate.
        
        -C                      Use constant quality instead of average bitrate for video.
                                (HandBrake uses RF 20.0 by default.)
        
        -x EXTRA_ARGS           Passes extra argument(s) to HandBrakeCLI.
    """)
    
    ratio = 'w1'
    sub = 1
    subburn = False
    quality = 1.0
    test = False
    constant_quality = None
    extraargs = []
    for o, a in opts:
        if o == '-r':
            ratio = a
            if ratio not in RATIOS:
                exit("unknown ratio '" + ratio + "' not one of " + str(RATIOS.keys()))
        if o == '--w1':
            ratio = 'w1'
        if o == '--tv':
            ratio = 'tv'
        
        if o == '-s':
            sub = int(a)
        if o in ['--sb', '-B']:
            subburn = True
        if o == '-q':
            quality = float(a)
        if o in ['-T', '--test']:
            test = True
        if o in ['-C']:
            constant_quality = 20.0
        if o == '-x':
            extraargs.extend(a.split(" "))
        if o == '-S':
            extraargs.append('--scan')
    
    # Load preferences
    preferences = load_preferences(PREFERENCES_FILEPATH)
    
    # Locate HandBrakeCLI
    HB = preferences.get('handbrake_cli', None)
    while True:
        if HB is None:
            default = which('HandBrakeCLI')
            if default is None:
                default = ''
            
            choice = raw_input('Path to HandBrakeCLI(.exe) [%s]: ' % default)
            if choice == '':
                choice = default
                if choice == '':
                    sys.exit(1)
                    return
            
            HB = choice
        
        if not os.path.exists(HB):
            print 'HandBrakeCLI not found at: %s' % HB
            HB = None
            continue
        else:
            break
    
    # Locate destination directory
    DESTDIR = preferences.get('output_directory', None)
    while True:
        if DESTDIR is None:
            default = '.'
            
            choice = raw_input('Directory to save output files [%s]: ' % default)
            if choice == '':
                choice = default
                if choice == '':
                    sys.exit(1)
                    return
            
            DESTDIR = choice
        
        if not os.path.exists(DESTDIR):
            print 'Destination directory not found at: %s' % DESTDIR
            DESTDIR = None
            continue
        else:
            break
    
    # Save preferences, in case they were updated
    preferences['handbrake_cli'] = HB
    preferences['output_directory'] = DESTDIR
    save_preferences(PREFERENCES_FILEPATH, preferences)
    
    # Encode video files
    for srcfilepath in args:
        srcfilebase = os.path.basename(srcfilepath)
        dstfilebase = srcfilebase.rsplit('.', 1)[0] + '.m4v'
        dstfilepath = os.path.join(DESTDIR, dstfilebase)
        
        hbargs = []
        
        # Standard iPod Touch options
        hbargs.extend(['-Z', "Apple/iPhone & iPod Touch"])
        hbargs.extend(['-e', 'x264', '--x264opts', "cabac=0:ref=2:me=umh:bframes=0:subq=6:8x8dct=0:weightb=0"])
        
        # Use high quality AAC audio encoder, since it's available on the Mac
        # 96kbit AAC audio is good quality
        hbargs.extend(['-E', 'ca_aac'])
        if 'absame' not in RATIOS[ratio]:
            hbargs.extend(['--ab', '96'])
        
        # Ratio-determined...
        if constant_quality is not None:
            hbargs.extend(['-q', str(constant_quality)])
        elif 'vb' in RATIOS[ratio]:
            hbargs.extend(['--vb', str(int(RATIOS[ratio]['vb'] * quality))])
        if 'w' in RATIOS[ratio]:
            hbargs.extend(['-w', str(RATIOS[ratio]['w'])])
        if 'h' in RATIOS[ratio]:
            hbargs.extend(['-l', str(RATIOS[ratio]['h'])])
        
        # Subtitles
        hbargs.extend(['-s', str(sub)])
        if subburn:
            hbargs.extend(['--subtitle-burn', str(sub)])
        else:
            hbargs.extend(['--subtitle-default', str(sub)])
        
        if test:
            hbargs.extend(['--stop-at', 'duration:30'])
        
        # Input and output
        hbargs.extend(['-i', srcfilepath, '-o', dstfilepath])
        
        # Invoke HandBrake
        cmdline = [HB]
        cmdline.extend(hbargs)
        cmdline.extend(extraargs)
        print ' '.join(cmdline)
        subprocess.check_call(cmdline)
        
        # If performing a test encode, open the result file
        if test:
            try:
                # Mac OS X
                subprocess.check_call(['open', dstfilepath])
            except:
                try:
                    # Windows
                    os.startfile(dstfilepath)
                except:
                    print 'Could not open file: %s' % dstfilepath


def load_preferences(preferences_filepath):
    preferences = {}
    
    if not os.path.exists(preferences_filepath):
        return preferences
    
    preferences_file = open(preferences_filepath, 'rb')
    try:
        for line in preferences_file:
            (k, v) = line.strip('\r\n').split('=', 1)
            preferences[k] = v
    finally:
        preferences_file.close()
    
    return preferences


def save_preferences(preferences_filepath, preferences):
    preferences_file = open(preferences_filepath, 'wb')
    try:
        for (k, v) in preferences.iteritems():
            preferences_file.write(k)
            preferences_file.write('=')
            preferences_file.write(v)
            preferences_file.write('\n')
    finally:
        preferences_file.close()


def which(program_name):
    """
    Locates the program with the specified name.
    
    Returns None if not found.
    """
    try:
        # Mac OS X, Linux
        return subprocess.check_output(['which', program_name]).strip('\r\n')
    except:
        return None

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print
        sys.exit(1)
