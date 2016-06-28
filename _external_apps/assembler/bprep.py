#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import glob
import httplib
from ConfigParser import ConfigParser
from django.utils.encoding import smart_str, force_unicode


class HttpObject():

    def get_data_from_http_response(self, method, host, uri):
        """Get data from the server via API
        Returns dict
        """
        conn= httplib.HTTPConnection(host)
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


def fill_prog_data(slug):
    """Collect data about program, num in prog
    as well as paths to comps and mixes.
    """
    curr_path= os.path.dirname(os.path.realpath(__file__)) # Save current path
    result= {'program_no': None, 'num_in_program': None}

    # Get manifest files.
    os.chdir(conf.MANIFEST)
    for fl in glob.glob("*.mnf"):
        prog_no= None
        manifest_cfg= ConfigParser()
        manifest_cfg.read(fl)
        for i in (1, 2, 3):
            # bookmark - i'm doing something wrong here!
            try:
                section= manifest_cfg.items('celebrity'+str(i))
            except:
                section= None
            try:
                id_line= manifest_cfg.get('celebrity'+str(i), 'id')
            except:
                id_line= None
            if id_line:
                if slug in id_line:
                    try:
                        prog_no= int(fl.split('_')[0])
                    except Exception as e:
                        print 'Warning! %s found in manifest %s, but the file name is wrong!\nCannot get program number' % (
                            slug, fl)
                    break
        if prog_no: # If program number is found, no reason to walk through the rest of files
            result['program_no']= prog_no
            result['num_in_program']= i
            result['celebrity_house']= manifest_cfg.get('celebrity'+str(i), 'house')
            break

    os.chdir(curr_path) # Restore current path
    return result


def get_comp_filename(program_no, slug, lang):
    """Obtain filename of the composition
    based on known program number and slug
    """
    curr_path= os.path.dirname(os.path.realpath(__file__)) # Save current path
    result= {'comp_'+lang: '', 'mix_'+lang: '', 'seq_'+lang: ''}

    # Try to get program number.
    try:
        no= "%05d" % int(program_no)
    except:
        return result # If program number can't be obtained, the rest doesn't make sense

    # Try to comp filename.
    os.chdir(conf.COMP_OUT)
    comp_lang_file= glob.glob("%s*%s*%s.nk" % (no, slug, lang))
    if comp_lang_file:
        result.update({'comp_'+lang: comp_lang_file[0]})

    # Try to get file of sound mix.
    mix_lang_file= None
    try:
        os.chdir("%s%s_%s/sound" % (conf.ROOT_OUT, no, lang))
        mix_lang_file= glob.glob("%s*%s*%s_mix.wav" % (no, slug, lang))
    except:
        pass
    if mix_lang_file:
        result.update({'mix_'+lang: mix_lang_file[0]})

    # Try to get number of files in seq folder.
    seq_lang= None
    try:
        path, dirs, files= os.walk('%s%s_%s/seq/' % (
            conf.ROOT_OUT, no, lang)).next()
        seq_lang= len(files)
    except Exception as e:
        print e
    if seq_lang:
        result.update({'seq_'+lang: seq_lang})
        
    os.chdir(curr_path) # Restore current path
    return result
    


def fill_voice_data(slug, lang):
    """Collect data from filesystem
    """
    curr_path= os.path.dirname(os.path.realpath(__file__)) # Save current path
    result= {}

    # Get voice files.
    i= 0
    os.chdir(conf.NARRATOR_PATH)
    for fl in glob.glob("%s_%s_*.%s" % (slug, lang, conf.AUDIO_FORMAT)):
        i += 1
    result.update({'voice_'+lang: i})

    os.chdir(curr_path) # Restore current path
    return result


def fill_lang_data(slug, lang):
    """Fill language specific data for a Celebrity
    """
    celeb_lang_uri= '%s%s/%s/?all=1' % (conf.CELEBRITY_URI_TEMPL, slug, lang)
    try:
        celeb_lang_request= HttpObject().get_data_from_http_response('GET',
            conf.HOST, celeb_lang_uri)
    except Exception as e:
        print "WARNING! Cannot get script data from http://%s%s\nThe error is: %s" % (
            conf.HOST, celeb_lang_uri, e)
        return None
    celeb_lang_data= celeb_lang_request['celebrity'][lang]
    script= celeb_lang_data.pop('script')

    # Rename keys.
    celeb_lang_data['name_'+lang]= celeb_lang_data.pop('name')
    celeb_lang_data['duration_'+lang]= celeb_lang_data.pop('total_dur')
    celeb_lang_data['scenes_'+lang]= celeb_lang_data.pop('total_scenes')
    celeb_lang_data['user_'+lang]= celeb_lang_data.pop('user')

    return celeb_lang_data


def fill_celebrity_list(celebrity_list):
    """Fill the list of Celebrities with language specific data
    """
    for celebrity in celebrity_list:
        print '...processing %s' % celebrity['slug']
        celeb_langs_uri= '%s%s/?all=1' % (conf.CELEBRITY_URI_TEMPL, celebrity['slug'])

        # Data obtained from the db
        try:
            celeb_langs_request= HttpObject().get_data_from_http_response('GET',
                conf.HOST, celeb_langs_uri)
        except Exception as e:
            print "WARNING! Cannot get the list of languages from http://%s%s\nThe error is: %s" % (
                conf.HOST, celeb_langs_uri, e)
            return None

        # Try to obtain data about program and number in it
        prog_data= fill_prog_data(celebrity['slug'])
        celebrity.update(prog_data)
        
        if celeb_langs_request['status'] == 'OK':
            langs= celeb_langs_request['celebrity']['language']
            slug= celebrity['slug']
            for lang in langs:
                celebrity.update({'completed_'+lang['title']: lang['completed']})
                celebrity_lang_details= fill_lang_data(slug, lang['title'])
                if celebrity_lang_details:
                    celebrity.update(celebrity_lang_details)

                # Data obtained from filesystem

                celebrity_voice_data= fill_voice_data(slug, lang['title'])
                if celebrity_voice_data:
                    celebrity.update(celebrity_voice_data)

                # Try to get filename of the composition
                comp_filename= get_comp_filename(
                    prog_data['program_no'], celebrity['slug'], lang['title'])
                celebrity.update(comp_filename)

        else:
            print "ERROR! The response from http://%s%s is %s" % (
                conf.HOST, celeb_lang_uri, celeb_request['celebrity'])
            return None

    return celebrity_list
        

def define_rp_header():
    """Define template of the Report
    """
    return ['num', 'name', 'slug', 'uri', 'name_russian', 'name_kazakh',
        'user_russian', 'user_kazakh', 'duration_russian', 'duration_kazakh',
        'scenes_russian', 'scenes_kazakh', 'completed_russian', 'completed_kazakh',
        'voice_russian', 'voice_kazakh',
        'celebrity_house', 'program_no', 'num_in_program',
        'comp_russian', 'comp_kazakh', 'mix_russian', 'mix_kazakh',
        'seq_russian', 'seq_kazakh']


def fill_csv(schema, rows):
    """
    """
    print '...creating lists for CSV'
    final_list= [schema]
    i= 0
    for row in rows:
        i += 1
        final_row= []
        for column in schema:
            try:
                final_row.append(row[column])
            except:
                if column == 'num':
                    final_row.append(i)
                else:
                    final_row.append('')
        final_list.append(final_row)
    # Save it to CSV.
    print os.path.basename(os.path.dirname(__file__))
    os.chdir(os.path.normpath(os.path.dirname(__file__)))
    myfile= open('%s.csv' % __file__.rsplit('.',1)[0], 'wb')
    wr= csv.writer(myfile, delimiter=';', quotechar='"',
        quoting=csv.QUOTE_ALL)
    try:
        wr.writerows(final_list)
        res= myfile.name
    except Exception as e:
        print "ERROR! Cannot save file. The system message is:\n%s" % e
        res= None

    return res


def main():
    celeb_uri= '%s?all=1' % conf.CELEBRITY_URI_TEMPL
    print '...connecting to http://%s%s' % (conf.HOST, celeb_uri)
    try:
        celeb_request= HttpObject().get_data_from_http_response('GET',
            conf.HOST, celeb_uri)
    except Exception as e:
        print "ERROR! Cannot get the list of celebrities from http://%s%s\nThe error is: %s" % (
            conf.HOST, celeb_uri, e)
        return None

    if celeb_request['status'] == 'OK':
        # Fill celebrity list with names and basic data
        result_list= fill_celebrity_list(celeb_request['celebrity'])

        rp_header= define_rp_header()

        return fill_csv(rp_header, result_list)
    else:
        print "ERROR! The response from http://%s/%s is %s" % (
            conf.HOST, conf.CELEBRITY_URI_TEMPL, celeb_request['celebrity'])
        return None


if __name__ == '__main__':
    # Define config.
    conf_filename= os.path.join(os.path.dirname(__file__), 'assemble.conf')

    LANGUAGES= ['russian', 'kazakh']
    DEFAULT_LANGUAGE= 'russian'
    
    conf= Conf(conf_filename)

    result_filename= main()
    if result_filename:
        msg= 'Finished successfully.'
        print "%s\n%s\nThe result is %s" % ('='*len(msg), msg, result_filename)
    else:
        msg= 'Finished with errors!'
        print "%s\n%s" % ('='*len(msg), msg)

