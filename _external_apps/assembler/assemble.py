#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import time
import shutil
import string
import random
import httplib
import optparse
import threading
import subprocess
from math import ceil
from datetime import date
from platform import platform
from ConfigParser import ConfigParser
from os import path, listdir, makedirs
from django.utils.encoding import smart_str, force_unicode


class HttpObject():

    def get_data_from_http_response(self, method, uri):
        """Get data from the server via API
        Returns dict
        """
        conn= httplib.HTTPConnection(conf.HOST)
        try:
            conn.request(method, uri)
        except:
            return None
        response= conn.getresponse()
        data= response.read()
        data= force_unicode(smart_str(data), encoding='utf-8')
        data_dict= eval(data)
        conn.close()
        if data_dict['status'].strip() != 'OK':
            data_dict= None
        return data_dict


class Conf():
    def __init__(self, path):
        cfg= ConfigParser({'basedir': path})
        cfg.read(path)
        self.fill_conf_values(cfg)

    def fill_conf_values(self, cfg):
        # Connection
        try:
            self.HOST= cfg.get('connect', 'host')
            self.CELEBRITY_URI_TEMPL= cfg.get('connect', 'celebrity_uri_templ')
            self.BILLBOARD_URI_TEMPL= cfg.get('connect', 'billboard_uri_templ')
            self.API_URI= '/%s/' % self.CELEBRITY_URI_TEMPL.split('/')[1]
            self.BASE_LANG= cfg.get('connect', 'base_lang')
            # Video
            self.INIT_SHIFT= int(cfg.get('video', 'init_shift'))
            self.FINAL_SHIFT= int(cfg.get('video', 'final_shift'))
            self.SCENE_SHIFT= int(cfg.get('video', 'scene_shift'))
            self.SCRIPT_SHIFT= int(cfg.get('video', 'script_shift'))
            self.FRAME= int(cfg.get('video', 'frame'))
            # Audio
            self.AUDIO_FORMAT= cfg.get('audio', 'format')
            self.AUDIO_OUT_FORMAT= cfg.get('audio', 'out_format')
        except Exception as e:
            print "ERROR! Cannot read config value. The system message is:\n%s" % e
            exit()
        try:
            self.AMP_CORRECT= cfg.get('audio', 'amp_correct')
        except:
            self.AMP_CORRECT= '1'
        # Local
        try:
            self.TEMPLATE= cfg.get('local', 'template')
            self.MANIFEST= cfg.get('local', 'manifest')
            self.COMP_OUT= cfg.get('local', 'comp_out')
            self.ROOT_OUT= cfg.get('local', 'root_out')
            self.IMAGE_PATH= cfg.get('local', 'image_path')
            self.HOUSES_PATH= cfg.get('local', 'houses_path')
            self.PLANTS_PATH= cfg.get('local', 'plants_path')
            self.NARRATOR_PATH= cfg.get('local', 'narrator_path')
            self.OPENING_THEME= cfg.get('local', 'opening_theme')
            self.FINAL_THEME= cfg.get('local', 'final_theme')
            self.OPENING_TITLES= cfg.get('local', 'opening_titles')
            self.FINAL_TITLES= cfg.get('local', 'final_titles')
            self.CLIENT_TEXT= cfg.get('local', 'client_text')
        except Exception as e:
            print "ERROR! Cannot read config value. The system message is:\n%s" % e
            exit()


class Alert():
    """System alerts
    """
    def __init__(self, code, details= None):
        return self.get_alert(code, details)

    def get_alert(self, code, details=None):
        alert_codes= {
            'not_found': {'type': 'ERROR', 'descr': 'Record not found!'},
            'empty_set': {'type': 'ERROR', 'descr': 'No data in the set!'}
            }
        alert= alert_codes[code]
        if details:
            alert.update({'descr':' '.join([alert[code]['descr'], details])})
        return alert


class AudioBlock():
    """Storage Class for an Audio Block as a part of the Program
    """
    def __init__(self, voice_amp=1):
        self.lang= None
        self.celeb= None
        self.slug= ''
        self.dur= 0 # To be calculated in assemble().
        self.scernes_total= 0 # To be calculated in assemble().
        self.narrator_filenames= [] # To be filled by assemble().
        self.voice_amp= voice_amp # Raise/dump volume (only voices)

    def _collect_narrator_filenames(self, filename_template):
        """Collect filenames with Audio
        recorded by Narrator.
        """
        filename_parts= {'slug': self.slug, 'lang': self.lang, 'scene': 0,
            'ext': conf.AUDIO_FORMAT, 'path': conf.NARRATOR_PATH}
        i= 0
        scenes_total= self.celeb['celebrity'][self.lang]['total_scenes']
        if scenes_total == 0:
            return Alert('not_found',
                details='Celebrity %s; Language %s' % (self.slug, self.lang))
        filelist= []
        while i < scenes_total:
            filename_parts['scene']= i
            filename= filename_template % filename_parts
            if path.exists(filename):
                # Normalize and convert it before the processing chain
                flout_parts= filename_parts.copy()
                flout_parts.update({'ext': conf.AUDIO_OUT_FORMAT,
                    'path': TEMP_DIR})
                flout= filename_template % flout_parts
                do_popen(['sox', '-V1', filename, flout, 'norm'])
                filelist.append(flout)
            else:
                raise IOError('File %s does not exist!' % filename)
            i += 1
        return filelist

    def concatenate_files(self, filelist, fl=None):
        scene_shift_s= conf.SCENE_SHIFT * conf.FRAME / 1000 # Scene shift in seconds
        script_shift_s= conf.SCRIPT_SHIFT * conf.FRAME / 1000 # Script shift in seconds
        print '...concatenating audio files'
        if not fl: # fl is initial file - the mix of the previous script
            fl= filelist[0].replace('.'+conf.AUDIO_OUT_FORMAT,
                '_c.'+conf.AUDIO_OUT_FORMAT)
            do_popen(['sox', '-V1', filelist[0], fl,
                'pad', '0', str(scene_shift_s)])
        for flc in filelist: # Concatenated file
            # Concatenate fl with the current,
            # write it to nfl with scene shift at the end
            if filelist.index(flc) < len(filelist)-1: # Add scene shift to the end
                nfl= flc.replace('.'+conf.AUDIO_OUT_FORMAT,
                    '_c.'+conf.AUDIO_OUT_FORMAT)
                shift= str(scene_shift_s)
            else: # Last file, add script_shift.
                nfl= TEMP_DIR + '%s_%s_mix.%s' % (
                    self.slug, self.lang, conf.AUDIO_OUT_FORMAT)
                shift= str(script_shift_s)
            # Normalize every voice sample
            do_popen(['sox', '-V1', fl, flc, nfl, 'pad', '0', shift])
            fl= nfl # The result of the last operation is an input for the next one.
        return fl

    def mix_scenes(self, filelist, fl):
        """Mix scenes for a program.
        Pad every scene with silence at the beginning,
        and mix with what the result of the previous stage.
        """
        i= 0
        for fl_current in filelist:
            fl_padded= fl_current.replace('.'+conf.AUDIO_OUT_FORMAT,
                '_P.'+conf.AUDIO_OUT_FORMAT)
            paddur= SCENE_START[self.lang][self.slug][i]['start_ms']
            do_popen(['sox', '-V1', '-v', str(self.voice_amp), fl_current, fl_padded, 'pad', paddur])
            if fl: # Not the initial file, mix it with newly padded file.
                fl_mixed= fl_padded.replace('.'+conf.AUDIO_OUT_FORMAT,
                    '_M.'+conf.AUDIO_OUT_FORMAT)
                do_popen(['sox', '-V1', '-m', fl, fl_padded, fl_mixed, 'norm'])
                fl= fl_mixed # Newly created file is the input for the next step.
            else:
                fl= fl_padded
            i += 1
        return fl

    def assemble(self, language, celebrity, initial=None):
        """Assemble the Block of narrator's fragments
        """
        self.lang= language
        self.celeb= celebrity
        self.slug= celebrity['celebrity']['slug']
        filename_templ= "%(path)s%(slug)s_%(lang)s_%(scene)d.%(ext)s"
        try:
            filelist= self._collect_narrator_filenames(filename_templ)
        except Exception as e:
            print e
            exit()
        combined_file= self.mix_scenes(filelist, initial)
        # combined_file= self.concatenate_files(filelist, initial)
        return combined_file

    def complete(self, slugs, lang, audioblock):
        """Complete processing of previously assembled AudioBlock:
        - normalize and remove silence at the end
        - rename file and mix it with backround music
        - put the mix to comp_out directory
        """
        if not audioblock:
            return Alert('not_found')
        else:

            # Mix with opening theme and background loop
            fname= '_'.join([PROJECT_ID] + slugs + [lang, 'mix.'])
            opening_theme_loop= conf.OPENING_THEME.replace('%%lang%%', lang)
            opening_theme_mix= TEMP_DIR + fname.replace('mix.', 'mixo.') + conf.AUDIO_OUT_FORMAT
            do_popen(['sox', '-m', audioblock, opening_theme_loop, opening_theme_mix, 'norm'])

            # Trim ending
            program_frames= TOTAL_FRAMES + FINAL_ADJUST
            program_dur= print_dur_pretty(float(program_frames) * conf.FRAME,
                with_ms= True)
            opening_theme_trim= TEMP_DIR + fname.replace('mix.', 'mixt.') + conf.AUDIO_OUT_FORMAT
            print "...trimming according to the program duration: frames %s, time %s" % (program_frames, program_dur)
            do_popen(['sox', opening_theme_mix, opening_theme_trim, 'trim', '0', program_dur])

            # Final mix, splice with final theme.
            print "...splicing with final theme %s" % conf.FINAL_THEME
            final_mix= '%s%s/%s%s' % (PROJECT_DIR, 'sound', fname, conf.AUDIO_OUT_FORMAT)
            xfade= '%s,%f' % (program_dur, 0.5)
            do_popen(['sox', '-v', conf.AMP_CORRECT, opening_theme_trim, conf.FINAL_THEME, final_mix, 'splice', '-q', xfade, 'norm'])

            return final_mix


def do_popen(params):
    try:
        p= subprocess.Popen(params)
        while p.poll() != 0: # Time delay for a process to complete
            time.sleep(0.1)
    except Exception as e:
        print "ERROR! Subprocess can't be started:\n%s\nSystem's message is:\n%s" % (' '.join(params), e)
        exit()


def frames_to_smpte(frames):
    framerate= 1000 / float(conf.FRAME)
    ff= frames % framerate
    s= frames // framerate
    smpte= (s // 3600, s // 60 % 60, s % 60, ff)
    return "%02i:%02i:%02i:%02i" % smpte


def print_dur_pretty(miliseconds, with_ms= False):
    hours, milliseconds= divmod(miliseconds, 3600000)
    minutes, milliseconds= divmod(miliseconds, 60000)
    seconds= float(milliseconds) / 1000
    if with_ms:
        return "%i:%02i:%06.3f" % (hours, minutes, seconds)
    else:
        return "%02i:%02i:%02i" % (hours, minutes, seconds)


def id_generator(size=6, chars=string.ascii_lowercase+string.digits):
    """Generate unique id from random \w
    """
    return ''.join(random.choice(chars) for x in range(size))


def retrieve_images(script, timeout):
    """Downloading all images for the script
    """
    success= []
    for scene in script:
        img_url= scene['media_url']
        img_filename= img_url.split('/')[-1]
        # Image should be downloaded only once.
        if path.exists(conf.IMAGE_PATH + img_filename):
            continue
        # Getting images
        if 'Darwin' in platform():  # Mac OS X
            p= subprocess.Popen(['curl', '-s',
                '-o', conf.IMAGE_PATH + img_filename, '--create-dirs', img_url])
        elif 'Linux' in platform():  # Linux
            p= subprocess.Popen(['wget', '-q', '-nH', '-P',
                conf.IMAGE_PATH, img_url])
        tmout= timeout
        while p.poll() != 0 and tmout > 0:
            time.sleep(0.1)
            tmout= float(tmout) - 0.1
        if tmout == 0: # reached timeout
            success.append(False)
        else:
            success.append(True)

    # Check if everything went well, and report only in case of problems
    if all(success):
        pass
    else:
        print "WARNING! There were problems downloading images. Check your internet connection and try again"


def process_scene(text, start, duration, picture, scene_id):
    """Processes raw text,
    substitutes template tags with values
    from the Script
    """
    result= ''
    for line in text.split('\n'):

        # Calculating expressions.
        rg= r"\%{2}[-+\w]+\%{2}"
        if re.search(rg, line):
            for m in re.finditer(rg, line):
                if 'picture' in m.group(0):
                    line= line.replace(m.group(0), picture)
                else:
                    value= eval(m.group(0).replace('%%', ''))
                    line= line.replace(m.group(0), str(int(value)))

        # Re-identifying billboards (bb_).
        rg= r"bb_"
        if re.search(rg, line):
            line= line.replace(rg, scene_id)

        result += line + '\n'
    return result


def merge_billboard():
    """Return merge code for billboards
    with generated unique id
    """
    return "Merge2 {\n inputs 2\n name %s\n selected true\n}\n" % id_generator(10)


def process_script(start, script, script_id):
    """Processing Celebrity script,
    returns full text for the source file
    """
    src= ''
    start_list= []
    for scene in script:
        # WARNING! At the moment duration comes from the script,
        # but in fact it should be obtained from narrator's mp3.
        duration= ceil(float(scene['dur']) / conf.FRAME)

        picture= conf.IMAGE_PATH + scene['media_url'].split('/')[-1]
        bb_id= scene['billboard'].split('/')[-1]
        bb_uri= '%s%s/' % (conf.BILLBOARD_URI_TEMPL, bb_id)
        bb= HttpObject().get_data_from_http_response('GET', bb_uri)
        if bb:
            start_ms= print_dur_pretty(start*conf.FRAME, with_ms=True)
            dur_ms= print_dur_pretty(scene['dur'], with_ms=True)
            print 'bb %s: start = frames %d (ms %s), dur = frames %d (ms %s)' % (
                bb['title'].strip(), start, start_ms, duration, scene['dur'])

            # Collect scene beginnings
            start_list.append({'start_frames': start,
                'start_ms': start_ms})

            # Scene processing function.
            bb_body= process_scene(
                bb['body'], start, duration, picture,
                'srcipt%d_bb%d_' % (script_id, script.index(scene)+1)
                )
        # Filling out image copyrights.
        if scene['media_copyright'].strip() != '':
            global COPYRIGHTS
            COPYRIGHTS.append(scene['media_copyright'])
            
        src += bb_body + merge_billboard()
        start += duration + conf.SCENE_SHIFT

    start -= conf.SCENE_SHIFT # The last shift should be removed before proceed.

    return src, start, start_list


def process_program(slugs, lang):
    """Processing the program
    consisting of choosen Celebrities
    """
    start= conf.INIT_SHIFT
    source= ''
    audio_program_lang= None

    for celebrity_slug in slugs:
        celebrity_uri= '%s%s/%s/' % (conf.CELEBRITY_URI_TEMPL,
            celebrity_slug, lang)
        print '...connecting to http://%s%s' % (conf.HOST, celebrity_uri)

        celebrity= HttpObject().get_data_from_http_response('GET',
            celebrity_uri)
        if celebrity:
            script= celebrity['celebrity'][lang]['script']

            # Downloading images in a separate thread.
            t_img= threading.Thread(target=retrieve_images, args=(script, 10))
            t_img.start()

            # Processing the Script.
            print "...building code for scripts"
            script_source, start, start_list= process_script(
                start,
                script,
                slugs.index(celebrity_slug)+1 # Index is the script id.
                )
            # Update SCENE_START - count starts for particular lang and celeb
            SCENE_START[lang].update({celebrity_slug: start_list})

            # Assemble audio block.
            if WITH_AUDIO:
                print "...processing audio for %s in %s" % (
                    celebrity['celebrity'][lang]['name'], lang.upper())
                audio_program_lang= AudioBlock(voice_amp=VOICE_AMP).assemble(
                    lang,
                    celebrity,
                    audio_program_lang
                    )

            global TRANSITIONS
            TRANSITIONS.append(int(start))
            print '*** TRANSITION %d' % start

            # Shifting to the next script.
            start += conf.SCRIPT_SHIFT

            # Filling up the source.
            source += script_source
        else:
            print 'WARNING! No data for %s!' % celebrity_slug

    global TOTAL_FRAMES # Counting total frames.
    TOTAL_FRAMES= start # To be used in the result filename

    # Last operations on audio block
    if WITH_AUDIO:
        print '...completing audio mix'
        audio_program_lang= AudioBlock().complete(
            slugs, lang, audio_program_lang)
        print "%(div)s\nSUCCESS: final mix in\n%(fm)s\n%(div)s" % {
            'div': '='*20, 'fm': audio_program_lang}

    return source


def get_celebrity_name(num):
    """Retrieve language specific Celebrity name from api
    """
    def _get_celebrity(language):
        celebrity_uri= '%s%s/%s/' % (conf.CELEBRITY_URI_TEMPL,
            slugs[int(num)-1], language)
        celebrity= HttpObject().get_data_from_http_response('GET',
            celebrity_uri)
        if celebrity:
            return celebrity
        else:
            return None
    out= ''
    celeb= _get_celebrity(lang)
    if celeb:
        out= celeb['celebrity'][lang]['name'].strip()
        if out == '': # If there is no language specific name, get default lang
            celeb= _get_celebrity(conf.BASE_LANG)
            if celeb:
                out= celeb['celebrity'][conf.BASE_LANG]['name'].strip()
                if out == '': # If no default lang name, get celebrity base name
                    out= celeb['celebrity']['name']
    return out


def get_random_filename(path):
    return random.choice(listdir(path))


def get_titles_text(kind):
    conf_set= ''.join(['conf.', kind.upper(), '_TITLES'])
    titles_fname= eval(conf_set).replace('%%lang%%', lang.lower())
    f= open(titles_fname, 'r')
    return f.read()


def get_client_text():
    client_fname= conf.CLIENT_TEXT.replace('%%lang%%', lang.lower())
    f= open(client_fname, 'r')
    return f.read()


def process_template_line(line):
    """Processesing a line of template,
    substitute variables
    """
    # WARNING! Ugly! Refactor!
    # Suppose, any variable can appear several times in a line!
    
    # Catching template tags %%...%%
    def _report_subst(tmpl, substln):
        print "...caught %s, replacing it with %s" % (tmpl, substln)

    # Transitions (several occurences in a line with expressions).
    re_trans_single= r"\%{2}(?P<const>Transition_)(?P<num>\d+)\%{2}"
    re_trans_expr= r"\%{2}(?P<const>Transition_)(?P<num>\d+)(?P<expr>[-+\d]+)\%{2}"
    if re.search(re_trans_single, line): # Caught %%Transition_N%%
        for m in re.finditer(re_trans_single, line):
            trans= str(TRANSITIONS[int(m.group('num'))-1])
            line= line.replace(m.group(0), trans)
            _report_subst(m.group(0), trans)
    if re.search(re_trans_expr, line): # Caught %%Transition_N(+-)%% - WARNING! it's an expression, so, processed differently
        for m in re.finditer(re_trans_expr, line):
            trans= str(TRANSITIONS[int(m.group('num'))-1])
            value= eval(m.group(0).replace(m.group('const')+m.group('num'), trans).replace('%%', ''))
            line= line.replace(m.group(0), str(int(value)))
            _report_subst(m.group(0), str(int(value)))

    # Language (several occurences in a line with expressions).
    re_lang= r"\%{2}language\%{2}"
    if re.search(re_lang, line): # Caught %%language%%
        for m in re.finditer(re_lang, line):
            line= line.replace(m.group(0), lang)
            _report_subst(m.group(0), lang)

    # The rest (single occurences, no expressions)
    r_bb= re.search(r"\%{2}billboards\%{2}", line)
    r_cname= re.search(r"\%{2}(?P<const>Celebrity_Name_)(?P<num>\d+)\%{2}", line)
    r_chouse= re.search(r"\%{2}(?P<const>Celebrity_House_)(?P<num>\d+)\%{2}", line)
    r_rhouse= re.search(r"\%{2}Random_House\%{2}", line)
    r_rplant= re.search(r"\%{2}Random_Plant\%{2}", line)
    r_ottl= re.search(r"\%{2}Opening_Titles_Text\%{2}", line)
    r_fttl= re.search(r"\%{2}Final_Titles_Text\%{2}", line)
    r_client= re.search(r"\%{2}Ministry_Text\%{2}", line)
    r_cc= re.search(r"\%{2}Copyrights\%{2}", line)
    r_frames= re.search(r"\%{2}TotalDuration\%{2}", line)
    r_outfile= re.search(r"\%{2}output_file_name\%{2}", line)
    r_compname= re.search(r"\%{2}Comp_Name\%{2}", line)
    # Processing caught lines.
    if r_bb: # Caught %%billboards%%
        line= program + '\n'
        _report_subst('%%billboards%%', 'script code')
    if r_cname: # Caught %%Celebrity_Name_N%%
        celeb_name= get_celebrity_name(r_cname.group('num'))
        line= line.replace(r_cname.group(0), celeb_name)
        _report_subst(r_cname.group(0), celeb_name)
    if r_chouse: # Caught %%Celebrity_House_N%%
        celeb_house= houses[int(r_chouse.group('num'))-1]
        line= line.replace(r_chouse.group(0), celeb_house)
        _report_subst(r_chouse.group(0), celeb_house)
    if r_rhouse: # Caught %%Random_House%%
        r_house_path= conf.HOUSES_PATH + get_random_filename(conf.HOUSES_PATH)
        line= line.replace(r_rhouse.group(0), r_house_path)
        _report_subst(r_rhouse.group(0), r_house_path)
    if r_rplant: # Caught %%Random_Plant%%
        r_rplant_path= conf.PLANTS_PATH + get_random_filename(conf.PLANTS_PATH)
        line= line.replace(r_rplant.group(0), r_rplant_path)
        _report_subst(r_rplant.group(0), r_rplant_path)
    if r_ottl: # Caught %%Opening_Titles_Text%%
        line= line.replace(r_ottl.group(0), get_titles_text('Opening'))
        _report_subst(r_ottl.group(0), 'opening titles')
    if r_fttl: # Caught %%Final_Titles_Text%%
        line= line.replace(r_fttl.group(0), get_titles_text('Final'))
        _report_subst(r_fttl.group(0), 'final titles')
    if r_client: # Caught %%Ministry_Text%%
        line= line.replace(r_client.group(0), get_client_text())
        _report_subst(r_client.group(0), 'client text')
    if r_cc: # Caught %%Copyrights%%
        line= line.replace(r_cc.group(0), '; '.join(COPYRIGHTS))
        _report_subst(r_cc.group(0), 'copyrights')
    if r_frames: # Caught %%TotalDuration%%
        line= line.replace(r_frames.group(0), str(TOTAL_FRAMES))
        _report_subst(r_frames.group(0), str(TOTAL_FRAMES))
    if r_outfile: # Caught %%output_file_name%%
        outfile= '%s%s_%s/seq/%s_%s_' % (
            conf.ROOT_OUT, PROJECT_ID, lang, PROJECT_ID, lang)
        line= line.replace(r_outfile.group(0), outfile)
        _report_subst(r_outfile.group(0), outfile)
    if r_compname: # Caught %%Comp_Name%%
        line= line.replace(r_compname.group(0), PROJECT_FILENAME)
        _report_subst(r_compname.group(0), PROJECT_FILENAME)
    return line


def process_template():
    """Processing the main template.
    """
    template= open(conf.TEMPLATE, 'r')
    result= ""
    print "Processing main template"
    for line in template:
        if line.strip() != '':
            result += process_template_line(line)
    return result


def initiate_file(slugs, lang, dur):
    """Create file name and returm FILE object
    open for writing
    """
    fname= [PROJECT_ID] + slugs + [dur, lang]
    global PROJECT_FILENAME
    PROJECT_FILENAME= ''.join([conf.COMP_OUT, '_'.join(fname), '.nk'])
    return open(PROJECT_FILENAME, 'w')


def create_dirs(lang):
    """Create initial directories
    """
    print "...creating directories for language %s" % lang.upper()
    dir_name_tmpl= ['seq', 'sound', 'avi', 'mpeg']
    for d in dir_name_tmpl:
        dirname= '%s%s_%s/%s' % (conf.ROOT_OUT, PROJECT_ID, lang, d)
        if not path.exists(dirname):
            makedirs(dirname)
    return '%s%s_%s/' % (conf.ROOT_OUT, PROJECT_ID, lang)

def process():
    # Processing the programm.
    # (MAIN FUNCTION)

    global program
    program= process_program(slugs, lang)

    # Add final subtitles to total frames
    global TOTAL_FRAMES
    TOTAL_FRAMES += conf.FINAL_SHIFT 

    # SMTE-formatting total duration 'hh-mm-ss-ff'
    total_dur= frames_to_smpte(TOTAL_FRAMES).replace(':','-')

    # Processing the main template.
    source= process_template()

    source_file= initiate_file(slugs, lang, total_dur)

    source_file.writelines(source)
    try:
        source_file.close()
        print "%(div)s\nSUCCESS: the result is in the file\n%(fn)s\n%(div)s" % {
            'div': '='*20, 'fn': source_file.name}
    except Exception as e:
        print 'ERROR! %s' % e


def fill_lang(lang_title):
    """Fill the list of languages.
    """
    error= True
    out= []
    info= HttpObject().get_data_from_http_response('GET', conf.API_URI)
    for lang in info['language']:
        if lang_title:
            if lang_title != lang['title'].lower():
                continue
        out.append(lang['title'].lower())
        error= False
    return out, error


def read_manifest(path):
    """Fill the list of slugs and houses for 3 Celebrities
    from given manifest file.
    """
    error= None
    out= []
    project_id= ''
    try:
        f= open(path, 'r')
    except Exception as e1:
        try:
            path= conf.MANIFEST + path
            f= open(path, 'r')
        except Exception as e2:
            return project_id, out, 'ERROR! Cannot find manifest file. System response is:\n%s\n%s' % (e1, e2)
    try:
        project_id= int(path.split('/')[-1].split('_')[0])
    except:
        return project_id, out, 'ERROR! Cannot extract Project ID from filename!'
    cfg= ConfigParser({'basedir': conf.MANIFEST + path})
    cfg.read(path)
    for i in (1, 2, 3):
        # Process slug.
        try:
            celeb_id= cfg.get('celebrity' + str(i), 'id')
        except Exception as e:
            return project_id, out, 'ERROR! Cannot find Celebrity %d id. System response is: %s' % (i, e)
        celeb_id= celeb_id.split('/')
        if len(celeb_id) == 1:
            slug= celeb_id[0]
        else:
            last_id= celeb_id[-1].strip()
            if last_id == '':
                slug= celeb_id[-2].strip()
            else:
                slug= last_id
        # Process celebrity house
        try:
            house= cfg.get('celebrity' + str(i), 'house')
        except Exception as e:
            return project_id, out, 'ERROR! Cannot find Celebrity %d house. System response is: %s' % (i, e)
        out.append({'slug': slug.strip(), 'house': house.strip()})
    return project_id, out, error


def manage_temp_dir(dirname= None):
    """Create or delete temp directory
    for all intermediate files
    """
    if dirname: # Remove dir under dirname.
        try:
            shutil.rmtree(dirname)
        except Exception as e:
            return e, False
    else: # No dir name given - create.
        try:
            dirname= '%s.%s/' % (conf.COMP_OUT, id_generator(12))
            makedirs(dirname)
        except Exception as e:
            return e, False
    return dirname, True


if __name__ == '__main__':
    # Define config.
    conf_filename= path.join(path.dirname(__file__),
        __file__.split('.')[0]+'.conf')
    conf= Conf(conf_filename)

    # Process command line options.
    cmdparser= optparse.OptionParser(usage="usage: python %prog [Options] manifest.bmf")
    cmdparser.add_option("-l", "--lang", action="store", dest="language",
        help="Language (if None - all db languages)")
    cmdparser.add_option("-a", "--amp", action="store", dest="voice_amp",
        help="Voice-over amplification")
    cmdparser.add_option("-f", "--finadjust", action="store", dest="final_adjust",
        help="Adjust final theme (frames)")
    cmdparser.add_option("-n", "--no-audio", action="store_true", dest="no_audio",
        help="Process without audio")
    opts, args = cmdparser.parse_args()
        
    # --- Globals ---
    # Voice amplification option
    VOICE_AMP= 1
    if opts.voice_amp:
        try:
            amp= float(opts.voice_amp)
            VOICE_AMP= str(opts.voice_amp)
        except:
            print "WARNING! Voice amplification given in wrong format (should be int or decimal).\nIgnoring it, proceeding further with amp=1"

    # Final theme adjust
    FINAL_ADJUST= 0
    if opts.final_adjust:
        try:
            FINAL_ADJUST= int(opts.final_adjust)
        except:
            print "WARNING! Final theme adjustment given in wrong format (should be positive or negative integer).\nIgnoring it, proceeding further with 0"

    # Chosen language
    langs, err= fill_lang(opts.language)
    if err:
        print "ERROR! Language not found in the database!"
        exit()

    # Assemble audio?
    WITH_AUDIO= True
    if opts.no_audio:
        WITH_AUDIO= False

    # Manifest
    PROJECT_ID, info, err= read_manifest(args[0].strip())
    if err:
        print err
        exit()
    slugs= [k['slug'] for k in info]
    houses= [k['house'] for k in info]
    PROJECT_ID= '%05d' % PROJECT_ID
    TEMP_DIR, success= manage_temp_dir()
    if not success:
        print "ERROR! Cannot create temp directory! Check your permissions!"
        exit()

    SCENE_START= {}
    for lang in langs:
        # Initial.
        COPYRIGHTS= []
        TOTAL_FRAMES= 0
        TRANSITIONS= []
        SCENE_START.update({lang: {}})
        PROJECT_FILENAME= ''
        
        # Create Project directories.
        PROJECT_DIR= create_dirs(lang)
        print '\nProcessing language: %s' % lang.upper()
        process()

    success, report= manage_temp_dir(TEMP_DIR)
    if not success:
        print "ERROR! Cannot delete temp directory! Check your permissions!"
