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
import re
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

CONSTANT_QUALITY_LEVEL = 20.0

# ------------------------------------------------------------------------------

def main(args):
    # Visually separate the program invocation line from the program output
    print
    
    # Parse arguments
    opts, args = getopt.getopt(args, 'r:s:a:x:STBq:C', ['vb=', 'tv', 'w1', 'sb', 'test', 'auto'])
    
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
        
        -a AUDIO_TRACK          Select audio track. Default is 1.
        
        -q QUALITY_MULTIPLIER   Multiplies video bitrate.
        
        -C                      Use constant quality instead of average bitrate for video.
                                (HandBrake uses RF 20.0 by default.)
        
        -x EXTRA_ARGS           Passes extra argument(s) to HandBrakeCLI.
    """)
    
    s = {} # settings
    s['auto'] = False
    s['ratio'] = 'w1'
    s['sub'] = 1
    s['audio'] = 1
    s['subburn'] = False
    s['quality'] = 1.0
    s['test'] = False
    s['constant_quality'] = False
    s['extraargs'] = []
    for o, a in opts:
        if o == '--auto':
            s['auto'] = True
        if o == '-r':
            s['ratio'] = a
            if s['ratio'] not in RATIOS:
                exit("unknown ratio '" + s['ratio'] + "' not one of " + str(RATIOS.keys()))
        if o == '--w1':
            s['ratio'] = 'w1'
        if o == '--tv':
            s['ratio'] = 'tv'
        
        if o == '-s':
            s['sub'] = int(a)
        if o == '-a':
            s['audio'] = int(a)
        if o in ['--sb', '-B']:
            s['subburn'] = True
        if o == '-q':
            s['quality'] = float(a)
        if o in ['-T', '--test']:
            s['test'] = True
        if o in ['-C']:
            s['constant_quality'] = True
        if o == '-x':
            s['extraargs'].extend(a.split(" "))
        if o == '-S':
            s['extraargs'].append('--scan')
    
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
        
        # Perform automatic setting detection if requested
        if s['auto']:
            detect_settings_automatically(s, HB, srcfilepath)
        
        # Standard iPod Touch options
        hbargs.extend(['-Z', "Apple/iPhone & iPod Touch"])
        hbargs.extend(['-e', 'x264'])
        # NOTE: HandBrake 0.9.9 does not recognize the following option anymore
        #hbargs.extend(['--x264opts', "cabac=0:ref=2:me=umh:bframes=0:subq=6:8x8dct=0:weightb=0"])
        
        # Use high quality AAC audio encoder, since it's available on the Mac
        # 96kbit AAC audio is good quality
        hbargs.extend(['-E', 'ca_aac'])
        if 'absame' not in RATIOS[s['ratio']]:
            hbargs.extend(['--ab', '96'])
        
        # Ratio-determined...
        if s['constant_quality']:
            hbargs.extend(['-q', str(CONSTANT_QUALITY_LEVEL)])
        elif 'vb' in RATIOS[s['ratio']]:
            hbargs.extend(['--vb', str(int(RATIOS[s['ratio']]['vb'] * s['quality']))])
        if 'w' in RATIOS[s['ratio']]:
            hbargs.extend(['-w', str(RATIOS[s['ratio']]['w'])])
        if 'h' in RATIOS[s['ratio']]:
            hbargs.extend(['-l', str(RATIOS[s['ratio']]['h'])])
        
        # Subtitles
        hbargs.extend(['-s', str(s['sub'])])
        if s['subburn']:
            hbargs.extend(['--subtitle-burn', str(s['sub'])])
        else:
            hbargs.extend(['--subtitle-default', str(s['sub'])])
        
        # Audio
        hbargs.extend(['-a', str(s['audio'])])
        
        if s['test']:
            hbargs.extend(['--stop-at', 'duration:30'])
        
        # Input and output
        hbargs.extend(['-i', srcfilepath, '-o', dstfilepath])
        
        # Invoke HandBrake
        cmdline = [HB]
        cmdline.extend(hbargs)
        cmdline.extend(s['extraargs'])
        print ' '.join(cmdline)
        subprocess.check_call(cmdline)
        
        # If performing a test encode, open the result file
        if s['test']:
            try:
                # Mac OS X
                subprocess.check_call(['open', dstfilepath])
            except:
                try:
                    # Windows
                    os.startfile(dstfilepath)
                except:
                    print 'Could not open file: %s' % dstfilepath

# ------------------------------------------------------------------------------
# Automatic Setting Detection

DISPLAY_ASPECT_RE = re.compile(r'display aspect: ([0-9.]+)')
PREFERRED_RATIO_NAMES = ['tv-hq', 'w1-hq', 'w3-hq']

# Detects encode settings for the specified source file
# and populates the provided settings dictionary with those settings.
def detect_settings_automatically(s, HB, srcfilepath):
    scan_output = subprocess.check_output(
        [HB, '--scan', '-i', srcfilepath],
        stderr=subprocess.STDOUT)
    scan_output_lines = scan_output.split('\n')
    
    # Extract title lines, which begin with '+'
    title_lines = []
    for line in scan_output_lines:
        if line.strip().startswith('+'):
            title_lines.append(line)
    
    # Extract display aspect
    display_aspect = None
    for line in title_lines:
        m = DISPLAY_ASPECT_RE.search(line)
        if m is not None:
            display_aspect = float(m.group(1))
    
    # Extract audio track & subtitle track info lines
    audio_track_lines = []
    subtitle_track_lines = []
    state = 'initial'
    for line in title_lines:
        if 'audio tracks' in line:
            state = 'audio'
        elif 'subtitle tracks' in line:
            state = 'subtitle'
        elif state == 'audio':
            audio_track_lines.append(line)
        elif state == 'subtitle':
            subtitle_track_lines.append(line)
    
    # Pick the ratio that is closest to the display aspect of the source file
    best_ratio_name = None
    best_ratio_fraction = None
    for cur_ratio_name in PREFERRED_RATIO_NAMES:
        cur_ratio = RATIOS[cur_ratio_name]
        cur_ratio_fraction = float(cur_ratio['w']) / cur_ratio['h']
        
        if best_ratio_name is None:
            best_ratio_name = cur_ratio_name
            best_ratio_fraction = cur_ratio_fraction
        elif abs(cur_ratio_fraction - display_aspect) < abs(best_ratio_fraction - display_aspect):
            best_ratio_name = cur_ratio_name
            best_ratio_fraction = cur_ratio_fraction
    
    # Pick the first Japanese audio track if found, otherwise track #1
    if len(audio_track_lines) == 0:
        audio_track_index = None
    else:
        audio_track_index = 0
        for (i, line) in enumerate(audio_track_lines):
            if 'Japanese' in line or 'jpn' in line:
                audio_track_index = i
    
    # Pick the first Japanese subtitle track if found, otherwise track #1
    if len(subtitle_track_lines) == 0:
        subtitle_track_index = None
    else:
        subtitle_track_index = 0
        for (i, line) in enumerate(subtitle_track_lines):
            if 'Japanese' in line or 'jpn' in line:
                subtitle_track_index = i
    
    # Return the detected settings
    s['ratio'] = best_ratio_name
    s['constant_quality'] = True
    s['sub'] = (subtitle_track_index + 1) if (subtitle_track_index is not None) else 1
    s['subburn'] = True if (subtitle_track_index is not None) else False
    s['audio'] = (audio_track_index + 1) if (audio_track_index is not None) else 1

# ------------------------------------------------------------------------------
# Preferences

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

# ------------------------------------------------------------------------------
# Utility

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
