#!/usr/bin/env python
# -*- coding: utf8 -*-
# -*- coding: iso-8859-1 -*-

import re
import datetime
import exifread
import piexif
from unidecode import unidecode
from os.path import join,dirname,splitext
from shutil import copyfile
from distutils.version import LooseVersion
import hashlib
import math


import PIL
from PIL import Image

from kivy.storage.jsonstore import JsonStore

#========================================================================#
# global variables
#========================================================================#

maxTextureSize = None

#========================================================================#
def convert(jsonfile,version):
#========================================================================#
    """
    Convert a json file created with an old version of the app to a newer 
    version
    """
    
    #TODO compare to json schema?

    store = JsonStore(jsonfile)
    
    
    #in really really old json files, "info" was called "map"
    if not store.exists('info'):
        if store.exists('map'):
            info = store.get('map')
            store['info']=info
            store.delete('map')
            
            #in really really old json files, calibration parameters were different
            #better delete it to force recalibration
            if store.exists('calibration'):
                store.delete('calibration')
    
    #version number is not written in json files with version < 0.1
    if (not 'version' in store.get('info') or 
        LooseVersion(store.get('info')['version']) <= LooseVersion("0.2.1")):
        
        #do conversion from markerList do MarkerDict
        if store.exists('markers'):
            markerDict = store.get('markers')
            newdict = {}
            if 'entries' in markerDict:
                markerList = markerDict['entries']
                
                for m in markerList:
                    hash = hashlib.sha1()
                    if 'time' in m:
                        hash.update(m['time'].encode('utf-8'))
                    else:
                        dt = datetime.datetime.now()
                        hash.update(dt.__str__().encode('utf-8'))
                        dt = dt.replace(microsecond=0)
                        m['time'] = dt.__str__()
                    if not 'active' in m:
                        m['active']=True
                    key = hash.hexdigest()[:8]
                    newdict[key]=m                    
                store.put('markers',dict=newdict)
                markerDict.pop('entries',None)
        
        if not store.exists('projection'):
            projectionsFile = join(dirname(__file__), 'projections.json')
            projectionDict  = JsonStore(projectionsFile)
            pname = projectionDict["default"]
            store.put('projection',
                projkey    =pname,
                description=projectionDict[pname]['description'],
                projparams =projectionDict[pname]['projparams'])
        
        if not 'time' in store.get('info'):
            #for very old json versions, creation time is conversion time
            tstr = date2string(datetime.datetime.now())
            info = store.get('info')
            info['time']=tstr
            store['info']=info
            
    #update version string in info
    info = store.get('info')
    info['version']=version
    store['info']=info

#========================================================================#
def strip_string(strin):
#========================================================================
    stripped = unidecode(strin)         #translate special characters
    stripped = stripped.lower()         #lower case
    stripped = re.sub(" ","_",stripped) #no spaces
    #finally, only asci letters and numbers
    stripped = ''.join(e for e in stripped if e.isalnum() or e == "_" )
    
    return stripped 

#========================================================================#
def dec2dms(deg):
#========================================================================#
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    
    return d,m,sd
    
#========================================================================#


##========================================================================#
#def string2date(datestring):
##========================================================================#

    ##'Jun 1 2005  1:33PM'
    ##return datetime.strptime(datestring, '%b %d %Y %I:%M%p')
    #return dateutil.parser.parse(datestring)
    
#========================================================================#
def date2string(date,seconds=False):
#========================================================================#

    #dt = date.replace(microsecond=0)
    #return dt.isoformat(' ')
    if seconds:
        return date.strftime("%B %d, %Y %H:%M:%S")
    else:
        return date.strftime("%B %d, %Y %H:%M")
    
#========================================================================#

#========================================================================#
def now_string(seconds=False):
#========================================================================#

    return date2string(datetime.datetime.now(),seconds)
    
#========================================================================#

#========================================================================#
def exif_rotation(filepath):
#========================================================================#

#FIXME exif rotation with PIL, problem getting 32bit PIL with buildozer
    #try:
        #image = Image.open(filepath)
        #exifdict = image._getexif()
        #orientation = exifdict[274]
        #if orientation == 1:
                #rotation = 0
        #elif orientation == 3:
                #rotation = 180
        #elif orientation == 6:
                #rotation = 270
        #elif orientation == 8:
                #rotation = 90
    #except:
        #print "EXIF Cannot Parse, Image Not Loaded: %s" % filepath
        #rotation = 0
    #return rotation
    
    #print orientation.printable
    #print orientation.tag 
    #print orientation.field_type
    #print orientation.field_offset
    #print orientation.field_length
    #print orientation.values
    
#exif rotation with exifread
    try:
        f = open(filepath, 'rb')
        tags = exifread.process_file(f)
        orientation=tags['Image Orientation'].values
        if orientation[0] == 1:
                    rotation = 0
        elif orientation[0] == 3:
                rotation = 180
        elif orientation[0] == 6:
                rotation = 270
        elif orientation[0] == 8:
                rotation = 90
        else:
            rotation = 0
    except:
        print("EXIF Cannot Parse Orientation: %s" % filepath)
        rotation = 0
    return rotation
#========================================================================#

#========================================================================#
def ImageSizeExif(filepath):
#========================================================================#
    try:
        f = open(filepath, 'rb')
        tags = exifread.process_file(f)
        width = tags['EXIF ExifImageWidth'].values[0]
        height = tags['EXIF ExifImageLength'].values[0]
        #for key in tags:
        #    print("{}:{}".format(key,str(tags[key])))
        #print width,height
        return width, height
    except:
        print("EXIF Cannot Parse Image dimensions: %s" %filepath)
# ========================================================================#

#========================================================================#
def ImageSize(filepath):
#========================================================================#
    try:
        image = Image.open(filepath)
        return image.size[0], image.size[1]
    except:
        print("Cannot determine image size of {}".format(filepath))
# ========================================================================#

#========================================================================#
def resizeImage(filepath, *args):
#========================================================================#

    # make a copy of the original file
    filepathNoExt = splitext(filepath)[0]
    ext = splitext(filepath)[1]
    filePathOrig = filepathNoExt + "_orig" + ext
    copyfile(filepath, filePathOrig)

    # determine new size = max texture size
    print(maxTextureSize)
    w,h = ImageSize(filepath)
    ratio = float(maxTextureSize)/float(max(w,h))
    W = int(math.floor(ratio*w))
    H = int(math.floor(ratio*h))

    try:
        #open image and resize using PIL
        image = Image.open(filepath)
        image = image.resize((W, H), PIL.Image.ANTIALIAS)


        #try to preserve the exif data
        #TODO: what if the original format is not jpeg?
        exif_dict = piexif.load(image.info["exif"])
        exif_bytes = piexif.dump(exif_dict)
        image.save(filepath,"JPEG", exif = exif_bytes)
    except:
        print("helper.resizeImage: Unable to resize the image.")

# ========================================================================#
