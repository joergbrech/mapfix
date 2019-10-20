#!/usr/bin/env python
# -*- coding: utf8 -*- 
## -*- coding: iso-8859-1 -*- 
#========================================================================#
from kivy.app import App

#to query max texture size
from kivy.graphics.opengl_utils import gl_register_get_size
from kivy.graphics.opengl import glGetIntegerv

#some basic layouts and widgets
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatter import Scatter,ScatterPlane
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.bubble import Bubble

#length units
from kivy import metrics

# for keyboard action
from kivy.base import EventLoop

#properties
from kivy.properties import BooleanProperty,StringProperty,ObjectProperty

#check the current os
from kivy.utils import platform

# I am not really logging anything right now...
from kivy.logger import Logger

# screen manager for main menu, maps menu, settings menu...
from kivy.uix.screenmanager import ScreenManager, Screen

# for list of available maps in maps menu
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior

# reading and writing json files (auxilary data stored with image for maps)
from kivy.storage.jsonstore import JsonStore

# transformation matrix used for markers
from kivy.graphics.transformation import Matrix

# animations when creating deleting maps and markers
from kivy.animation import Animation

# Camera interface
from plyer import camera

# file manipulation (copy, move, delete)
import shutil

# file handling
from glob import glob
from os import getcwd,remove,makedirs
from os.path import join,dirname,exists,splitext,isfile

# GPS interace
from plyer import gps
from kivy.clock import Clock, mainthread

#regular expressions
import re

#for lin alg stuff
import numpy as np

## to get current time
import datetime

# to generate keys for markers
import hashlib

from functools import partial

import sys

import mapfix
import mapfix.transform as transform
import mapfix.helper as h

#========================================================================#
# global variables

screenManager = ScreenManager()

#maxTextureSize = None

#========================================================================#
def getExternalDir():
#========================================================================#
    return App.get_running_app().user_data_dir


#========================================================================#
class MainScreen(Screen):
#========================================================================#
    
    markers_visible = False
    has_map = False
    
    def on_touch_down(self,touch):
        
        #if super(MainScreen, self).on_touch_down(touch):
        if self.ids.info_bar.collide_point(*touch.pos):
            
            if self.ids.info_bar.format == 'dms':
                self.ids.info_bar.format = 'dec'
            else:
                self.ids.info_bar.format = 'dms'
            self.ids.info_bar.update()
            return True
        elif self.ids.sat_layout.collide_point(*touch.pos):
            return True
        else:
            return super(MainScreen, self).on_touch_down(touch)
            
    def add_map(self,name,json):
        
        # if a selected map exists in mapsLayout, do nothing
        for child in self.maps_layout.children:
            if child.id == name:
                return False

        try:
            m = Map(store=json,id=name)
            self.maps_layout.add_widget(m)
            m.fly_in(0.5)

            if m.is_locked:
                self.lock()

            self.has_map = True
            self.ids.map_info.update(json)
            self.ids.btn_info.opacity=1.
            self.page_layout.border = metrics.dp(40)

            return True
        except:
            #TODO If the image does not exist, the app crashes earlier
            popup = MsgPopup("Cannot open the map")

    
    def get_current_map(self):
        for child in self.maps_layout.children:
            if type(child) is Map:
                return child
        return None
    
    def remove_map(self,deselect=False):
        self.unlock()
        
        curmap = self.get_current_map()
        if curmap:
            if deselect:
                self.maps_layout.remove_map_and_deselect(curmap)
            else:
                self.maps_layout.remove_map(curmap)
                
            self.ids.map_info.update('')
            if self.page_layout.page>0:
                self.page_layout.page = 0
            self.page_layout.border = 0
            self.ids.btn_info.opacity=.25
            self.has_map = False
                
            return True
        
        return False
    
    def lock(self):
        self.ids.pin_button.source = 'data/images/pin_blue2_transparent_lock.png'
        if self.markers_visible:
            for child in self.maps_layout.children:
                child.ids.markerSpace.remove_marker_widgets()
        
    def unlock(self):
        if self.markers_visible:
            self.ids.pin_button.source = 'data/images/pin_blue2.png'
            for child in self.maps_layout.children:
                child.add_marker_widgets_from_json()
        else:
            self.ids.pin_button.source = 'data/images/pin_blue2_transparent.png'
    
    # on press of invisible button
    def invisible_button(self):
        if self.has_map and self.get_current_map().is_locked:
            return
        if self.markers_visible:
            self.ids.pin_button.source = 'data/images/pin_blue2_transparent.png'
            #self.ids.pin_button.opacity = 0.5
            self.markers_visible = False
            for child in self.maps_layout.children:
                child.ids.markerSpace.remove_marker_widgets()
        else:
            self.ids.pin_button.source = 'data/images/pin_blue2.png'
            #self.ids.pin_button.opacity = 1.0
            self.markers_visible = True
            for child in self.maps_layout.children:
                child.add_marker_widgets_from_json()
                
    # on press of info button
    def info_button(self):
        if self.has_map:
            p = self.page_layout.page + 1
            self.page_layout.page = p % 2
        
#========================================================================#
class LonLatLabel(Label):
#========================================================================#
    format = StringProperty('dms')
    altitude = True
    
    def __init__(self,f='dms',**kwargs):
        super(LonLatLabel,self).__init__(**kwargs)
        self.format = f
    
    def update(self,dt=1.,gps_location=None):
        
        if gps_location == None:
            gps_location = App.get_running_app().gps_location
            
        #if App.get_running_app().gps_quality_level > 0:
        if gps_location:
            
            # get longitude, latitude and altitude from gps_location
            lat = gps_location['lat']
            lon = gps_location['lon']
            alt = gps_location['altitude']
                
            if self.format=='dms':
                if lat>0:
                    NS = "N"
                else:
                    NS = "S"
                if lon>0:
                    EW = "E"
                else:
                    EW = "W"
                  
                d_lat,m_lat,s_lat = h.dec2dms(abs(lat))
                d_lon,m_lon,s_lon = h.dec2dms(abs(lon))
                
                self.text = ('{} {:3d}° {:02d}\' {:.3f}\"\n'.format(NS,d_lat,m_lat,s_lat,) +
                             '{} {:3d}° {:02d}\' {:.3f}\"'.format(EW,d_lon,m_lon,s_lon))
            else:
                self.text = "Lat: {:3.6f}\nLon: {:3.6f}".format(lat,lon)
            
            if self.altitude:
                self.text += "\nAltitude: {} m".format(int(alt))
        #else:
            #self.text = 'Bibedibabedibu'

#========================================================================#    
class MapInfo(RelativeLayout):
#========================================================================#
    global screenManager
    store_path = ''
    
    def update(self,storePath=None):
            
        if not storePath==None:
            self.store_path = storePath
            
        if self.store_path == '':
            self.ids.namelabel.text = ''
            self.ids.datelabel.text = ''
            return
    

        store = JsonStore(self.store_path)
        curmap = screenManager.get_screen('main').get_current_map()


        # Set the Lock/Unlock Button
        locked = False
        if 'is_locked' in store.get('info'):
            if store.get('info')['is_locked']:
                locked = True
                self.ids.button_lock.source = 'data/images/icon_lock_blue.png'
                self.ids.button_lock.labeltext = 'Unlock'
                self.ids.infolabel.text = 'Press Unlock to change the calibration'
            else:
                self.ids.button_lock.source = 'data/images/icon_lock.png'
                self.ids.button_lock.labeltext = 'Lock'
                self.ids.infolabel.text = ''

        #update the MapInfo header strings

        # name
        self.ids.namelabel.text = store.get('info')['name']
        # time
        if 'time' in store.get('info'):
            self.ids.datelabel.text = '{}'.format(store.get('info')['time'])
        else:
                self.ids.datelabel.text = ''

        #projection
        #if curmap.projection is not None:
        #    #TODO: Why should this ever be the case? --> Happens on Android when image path is invalid
        self.ids.projectionlabel.text=curmap.projection.description

        #calibration info

        # count the markers
        nmarkers = 0
        nactive  = 0
        if store.exists('markers'):
            for key in store.get('markers')['dict']:
                nmarkers +=1
                if store.get('markers')['dict'][key]['active']:
                    nactive+=1
            self.ids.nmarkerlabel.text = "{} ({} active)".format(nmarkers,nactive)
        else:
            self.ids.nmarkerlabel.text = "0 Markers"

        if store.exists('calibration'):
            ci = store.get('calibration')['information']

            projUnits = curmap.projection.unit_string()

            self.ids.caldatelabel.text = "{}".format(ci['time'])
            self.ids.resprelabel.text = "{} {}".format(ci['res_pre'],projUnits)
            self.ids.reslabel.text = "{} {}".format(ci['res_post'],projUnits)
            self.ids.iterlabel.text = "{}".format(ci['num_iter'])
            if ci['level']==0:
                self.ids.transformlabel.text = "euclidean+scale"
                if not locked:
                    self.ids.infolabel.text = 'Add 1 more marker for an affine transform'
            elif ci['level']==1:
                self.ids.transformlabel.text = "affine"
                if not locked:
                    self.ids.infolabel.text = 'Add 1 more marker for a perspective transform'
            elif ci['level']==2:
                self.ids.transformlabel.text = "perspective"
                if not locked:
                    self.ids.infolabel.text = ''
        else:
            self.ids.caldatelabel.text = ''
            self.ids.resprelabel.text = ''
            self.ids.reslabel.text = ''
            self.ids.iterlabel.text = ''
            self.ids.transformlabel.text = ''
            if nactive==0:
                if not locked:
                    self.ids.infolabel.text = 'Add 2 markers for a first estimate'
            elif nactive==1:
                if not locked:
                    self.ids.infolabel.text = 'Add 1 more marker for a first estimate'
        
    
    def back_button(self):
        screenManager.get_screen('main').info_button()
        
    def calibrate_button(self):
        screenManager.get_screen('main').get_current_map().calibrate()
        
    def lock_button(self):
        curmap = screenManager.get_screen('main').get_current_map()
        is_locked = curmap.is_locked
        if is_locked:
            curmap.unlock()
            screenManager.get_screen('main').unlock()
            self.ids.button_lock.source = 'data/images/icon_lock.png'
            self.ids.button_lock.labeltext = 'Lock'
            self.ids.infolabel.text = ''
        else:
            curmap.lock()
            screenManager.get_screen('main').lock()
            self.ids.button_lock.source = 'data/images/icon_lock_blue.png'
            self.ids.button_lock.labeltext = 'Unlock'
            self.ids.infolabel.text = 'Press Unlock to change the calibration'
        
    def trash_button(self):
        store = JsonStore(self.store_path)
        nameStr = store.get('info')['name'].encode('utf-8').strip()
        msgStr = "Are you sure you want to delete the map \"{}\"?".format(nameStr)
        popup = ConfirmPopup(msgStr,self.delete_map)
        popup.open()
        
    def rename_button(self):
        store = JsonStore(self.store_path)
        name = store.get('info')['name']
        popup = RenameMapPopup(name)
        popup.open()
    
    def delete_map(self,*largs):
        jsonpath=self.store_path
        store   = JsonStore(self.store_path)
        imagpath=store.get('info')['imagedata'].encode('utf-8').strip()
        mapName =store.get('info')['name']
        screenManager.get_screen('main').remove_map(deselect=True)
        # I don't care if imagpath or jsonpath are invalid
        try:
            remove(imagpath)
        except:
            pass
        try:
            remove(jsonpath)
        except:
            pass

        screenManager.get_screen('maps').mapsList.remove(mapName)



#========================================================================#
class MapsMenu(Screen):
#========================================================================#
    def __init__(self, **kwargs):
        super(MapsMenu, self).__init__(**kwargs)             

    def do_capture(self):
               
        filepath = join(getExternalDir(),'mapfix_tmp.jpg')
        #filepath = join(dirname(__file__),'mappyx_tmp.jpg')
        

        try:
            camera.take_picture(filename=filepath, 
                                on_complete=self.camera_callback)
        except NotImplementedError:
            popup = MsgPopup(msg="This feature has not yet been implemented for this platform.")
            popup.open()

    def camera_callback(self, filepath):
        if(exists(filepath)):
            popup = NewMapPopup(filepath)
            popup.open()
        else:
            popup = MsgPopup(msg="Could not save your picture!")
            popup.open()
            


#========================================================================#
class SettingsMenu(Screen):
#========================================================================#
    pass

#========================================================================#
class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
#========================================================================#
    ''' Adds selection and focus behaviour to the view. '''

#========================================================================#    
class SelectableLabel(RecycleDataViewBehavior, Label):
#========================================================================#
    global screenManager
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            ret = self.parent.select_with_touch(self.index, touch)
            if self.selected:
                App.get_running_app().switch_screen(current='main',direction='right',previous='maps')                
            return ret

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
            
        name = rv.data[index]['text']
        
        #print("apply_selection, index = {},selected = {}".format(index,is_selected))
        
        if is_selected:
            #App.get_running_app().switch_screen(current='main',direction='right',previous='maps')
            
            try:
                json = rv.data[index]['json']
                screenManager.get_screen('main').add_map(name,json)
            except:
                popup = MsgPopup("Cannot select map")
                popup.open()

        else:
            screenManager.get_screen('main').remove_map()
                     
    def select_without_touch(self):
        return self.parent.select_with_touch(self.index)
    
                     
        
            

#========================================================================#
class RV(RecycleView):
#========================================================================#
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs) 
        
        for curdir in [dirname(__file__),getExternalDir()]:
            for mapJson in glob(join(curdir, 'maps', '*.json')):
                try:
                    h.convert(mapJson,App.get_running_app().__version__)
                    store = JsonStore(mapJson)
                except Exception as e:
                    Logger.exception('MapFix: RV.__init__: Unable to load <%s>' % mapJson)
                    
                self.insert(mapJson) #take relevant fields from store and push to RV
        self.sort()
            
    def sort(self):
        self.data = sorted(self.data, key=lambda entry: entry['text'].lower())
            
    def insert(self,json):
        store = JsonStore(json)
        entry = store.get('info')
        self.data.append({'text':entry['name'],'json':json})
        
    def insert_and_sort(self,json):
        
        self.insert(json)
        self.sort()
        # I don't really understand what any of these do:
        self.refresh_from_data()
        self.refresh_from_layout()
        self.refresh_from_viewport()
            

    def deselect_all(self):
    #This is needed as a workaround to crappy RV behavior.
    #When a new map is added and the RV entries are sorted,
    #The indices of the entries after the new one shift. This
    #is not accounted for in th RecycleView Selection Behavior
    #apparently...
        index = 0
        for e in self.data:
            v = self.view_adapter.get_visible_view(index)
            if v and v.selected:
                v.select_without_touch()
            index += 1        
            
            
    def select_map(self,map):
        self.select_map_by_name(map.id)
        
    def select_map_by_name(self,name):
        index = 0
        for e in self.data:
            if e['text']==name:
                v = self.view_adapter.get_visible_view(index)
                #TODO if it is found at the last index, v=None.
                #That doesn't make much sense...
                if v:
                    v.select_without_touch()
                    return
            index += 1
                
    def remove(self,mapName):
        index=0
        for e in self.data:
            if e['text']==mapName:
                self.data.pop(index)
                break
            index+=1
        #self.refresh_from_data()
            
    def exists(self,nm):
        for e in self.data:
            if e['text']==nm:
                return True
        return False
    
    def rename(self,oldname,newname):
        for e in self.data:
            if e['text'] == oldname:
                e['text'] = newname
                self.sort()
                self.refresh_from_data()
                screenManager.get_screen('main').get_current_map().id = newname
                #screenManager.get_screen('main').add_map(newname,e['json'])
                self.refresh_from_viewport()
                self.refresh_from_layout()
                #self.select_map_by_name(newname)
                return
        
        

#========================================================================#
class MsgPopup(Popup):
#========================================================================#
    def __init__(self, msg):
        super(MsgPopup, self).__init__()
        self.ids.message_label.text = msg
        
#========================================================================#
class QuitPopup(Popup):
#========================================================================#
    def __init__(self):
        super(QuitPopup, self).__init__()
        
#========================================================================#
class ConfirmPopup(Popup):
#========================================================================#
    def __init__(self,msg,fun,*args,**kwargs):
        super(ConfirmPopup,self).__init__(**kwargs)
        self.title = msg
        self.ids.yes_button.bind(on_press=partial(fun, *args))
        self.ids.yes_button.bind(on_press=self.dismiss)
        
        
#========================================================================#
class NewMapPopup(Popup):
#========================================================================#
    filename   = StringProperty()
    labelText  = StringProperty("Enter Name")    
    
    def __init__(self, imagefile,labeltext="Enter Name"):
        super(NewMapPopup, self).__init__()
        self.filename = imagefile
        self.labelText = labeltext
        
    def save(self):
        global screenManager
        name = self.ids.map_name_input.text
        
        if screenManager.get_screen('maps').mapsList.exists(name):
            label = "A map named \"{}\" exists.\nChoose a different name.".format(name)
            popup = NewMapPopup(self.filename,label)
            popup.hint_text = name+" 2"
            popup.open()
            self.dismiss()
            return
        
        # strip special characters from name
        name_s = h.strip_string(name)
        
        # name_s should contain at least one ascii character.
        # If the string is empty after stripping, save it under
        # 'no_ascii'
        if len(name_s)==0:
            name_s = 'no_ascii'
        
        maps_dir = join(getExternalDir(), 'data/maps')
        imag_dir = join(getExternalDir(), 'data/maps','imagedata')
        
        # make maps and maps/imagedata directories, if they don't exist
        if not exists(maps_dir):
            os.makedirs(maps_dir)
            
        if not exists(imag_dir):
            os.makedirs(imag_dir)
            
        #create a .nomedia file if it doesn't exist
        if platform=='android' and not exists(join(imag_dir,'.nomedia')):
            try:
                open(join(imag_dir,'.nomedia'),'a').close()
            except:
                import traceback
                traceback.print_exc()
        
        
        # make sure json name is unique
        mapJson  =join(maps_dir, name_s+'.json')
        if exists(mapJson):
            mapJson  =join(maps_dir, name_s+'_.json')
        
        # make sure image name is unique
        mapImage = join(imag_dir,name_s+'.jpg')
        if exists(mapImage):
            mapImage = join(imag_dir,name_s+'_.jpg')
        
        shutil.copyfile(self.filename, mapImage)
        if self.filename == join(getExternalDir(),'mapfix_tmp.jpg'):
            os.remove(self.filename)
        
        tstr = h.date2string(datetime.datetime.now())
        v = App.get_running_app().__version__
        store = JsonStore(mapJson)
        store.put('info',name=name,imagedata=mapImage,time=tstr,version=v,is_locked=False)
        
        #default projection
        projectionsFile = join(dirname(__file__), 'projections.json')
        projectionDict  = JsonStore(projectionsFile)
        pname = projectionDict["default"]
        store.put('projection',
            projkey    =pname,
            description=projectionDict[pname]['description'],
            projparams =projectionDict[pname]['projparams'])
        
        # workaround for crappy RV behavior. First deselect any selected map,
        # then add the map to the RV and sort the entries, and then select 
        # the newly added map by its name
        screenManager.get_screen('maps').mapsList.deselect_all()
        screenManager.get_screen('maps').mapsList.insert_and_sort(mapJson)
        screenManager.get_screen('maps').mapsList.select_map_by_name(name)
        self.dismiss()
    
    def cancel(self):
        if self.filename == join(getExternalDir(),'mapfix_tmp.jpg'):
            os.remove(self.filename)
        self.dismiss()
        

#========================================================================#
class RenameMapPopup(Popup):
#========================================================================#
    def __init__(self, name):
        super(RenameMapPopup, self).__init__()
        self.ids.map_name_input.text = name
    
    def rename(self):
        #IMPORTANT: Only the name stored in the json is changed.
        #The filenames keep their names
        m=screenManager.get_screen('main').get_current_map()
        infoDict = m.store.get('info')
        oldname = infoDict['name']
        newname =  self.ids.map_name_input.text
        infoDict['name'] = newname
        m.store['info']=infoDict
        m.id = newname
        screenManager.get_screen('maps').mapsList.rename(oldname,newname)
        screenManager.get_screen('main').ids.map_info.update()
        self.dismiss()

#========================================================================#
class MapsLayout(FloatLayout):
#========================================================================#

    def remove_map(self,m):
        self.remove_widget(m)
        
    def remove_map_and_deselect(self,m):
        global screenManager
        screenManager.get_screen('maps').mapsList.select_map(m)
        self.remove_widget(m)

#========================================================================#
class Map(ScatterPlane):
#========================================================================#    

    init_scale = 1
    store = None
    source = StringProperty(None)
    init_rotation = 0
    is_locked = False
    
    projection = None
    homography = transform.homography()
    has_calibration = False
    
    def __init__(self,store, **kwargs):
        global screenManager
        super(Map, self).__init__(**kwargs)
        self.bind(pos=self.ids.markerSpace.update_child_position)
        self.bind(pos=self.update_location_pos)
        
        self.store = JsonStore(store)

        # initialize the projection
        projDict = self.store.get('projection')
        self.projection = transform.projection(**projDict)
        
        #open the image (make sure special characters in image path work)
        self.source = self.store.get('info')['imagedata'].encode('utf-8').strip()

        if not isfile(self.source):
            popup = MsgPopup(msg="The image file\n{}\ndoes not exist!".format(self.source))
            popup.open()
        else:
            try:
                # resize image if its dimension exceeds OpenGL's maximum texture size
                # TODO: At some point, cut original image and add enough textures for the image resolution?
                (width,height) = h.ImageSize(self.source)
                mwh = max(width,height)
                if mwh > h.maxTextureSize:
                    popupStr = "Image dimension {} exceeds maximum texture size {}. Decrease the resolution now?".format(mwh,h.maxTextureSize)
                    popup = ConfirmPopup(popupStr, h.resizeImage, self.source)
                    popup.size_hint_y = 0.25
                    popup.open()
            except:
                pass

            self.init_rotation = h.exif_rotation(self.source)

        #load calibration, or calibrate
        if self.store.exists('calibration'):
            self.homography.H = np.array(self.store.get('calibration')['parameters'])
            self.homography.H_inv = self.homography.inverse()
            self.has_calibration = True
        else:
            self.calibrate()

        if screenManager.get_screen('main').markers_visible:
            self.add_marker_widgets_from_json()

        if 'is_locked' in self.store.get('info'):
            self.is_locked = self.store.get('info')['is_locked']


    
    # animation for creation
    def fly_in(self,t):
        self.init_scale = min( self.parent.width/self.width, self.parent.height/self.height ) 
        
        btn = screenManager.get_screen('main').maps_button
        self.center = btn.center
        self.scale = 0.01
        self.rotation = self.init_rotation + 45
        
        anim = Animation(scale=self.init_scale,duration=t)
        anim&= Animation(center=self.parent.center,duration=t)
        anim&= Animation(rotation=self.init_rotation,duration=t)
        anim.start(self)
        
    # animation for removement
    def fly_out(self,t=1):
        rot = self.rotation + 45
        btn = screenManager.get_screen('main').maps_button
        anim = Animation(scale=0.01,duration=t)
        anim&= Animation(center=btn.center,duration=t)
        anim&= Animation(rotation=rot,duration=t)
        anim&= Animation(opacity=0,duration=t)
        anim.start(self)
        anim.bind(on_complete=self.remove_map_widget)
        
    def moveWithAnimation(self,displ,t):
        newPos = (self.pos[0] + displ[0],self.pos[1]+displ[1])
        anim= Animation(pos=newPos,duration=t,t='in_out_cubic')
        anim.start(self)
        
    def lock(self):
        self.is_locked = True
        infoDict = self.store.get('info')
        infoDict['is_locked'] = True
        self.store['info']=infoDict
        
    def unlock(self):
        self.is_locked = False
        infoDict = self.store.get('info')
        infoDict['is_locked'] = False
        self.store['info']=infoDict
        
    def remove_map_widget(self,animation,widget):
        if self.parent:
            self.parent.remove_map_and_deselect(widget)
    
    def update_current_location(self,GPS):
        if self.has_calibration:
            x,y = self.projection.proj([GPS['lon'],GPS['lat']])
            d = self.homography.x2d([x,y])
            p = (int(d[0]),int(d[1]))
            self.ids.projectionSpace.current_location.update(self.to_parent(p[0],p[1]),p)
        else:
            self.ids.projectionSpace.current_location.opacity=0
            
    def update_location_pos(self,obj,value): 
        if self.has_calibration:
            p = self.ids.projectionSpace.current_location.p
            self.ids.projectionSpace.current_location.pos = self.to_parent(p[0],p[1])
            
    def calibrate(self):
        if self.is_locked:
            return
        ds,Cs = self.markers_from_store()
        ret = self.homography.calibrate(ds,Cs)
        if ret == 1:
            # not enough markers
            if self.store.exists('calibration'):
                self.store.delete('calibration')
            self.has_calibration=False
        else:
            H = self.homography.H.tolist()
            ci= self.homography.calibration_info
            if bool(ci):
                self.store.put('calibration',parameters = H,information=ci)
                self.has_calibration = True
        screenManager.get_screen('main').ids.map_info.update()
    
    def markers_from_store(self,onlyActive=True):
        
        # get coords and points from markers stored in the json files
        if self.store.exists('markers'):
            markerDict = self.store.get('markers')['dict']
        

            cs = []
            ds = []
            for key in markerDict:
                
                m=markerDict[key]
                if m['active'] or onlyActive==False:
                    ds.append(m['p'][0])
                    ds.append(m['p'][1])
                    cs.append(m['lon'])
                    cs.append(m['lat'])
            
            if cs:
                self.projection.update_from_coordinates(cs,self.store)
                xs = self.projection.proj(cs)
            else:
                xs=[]
                
            return ds,xs
        else:
            return [],[]
            
    def add_marker_widgets_from_json(self):
        if self.store.exists('markers'):
            markerDict = self.store.get('markers')['dict']
        else:
            markerDict = {}
        
        for key in markerDict:
            m = Marker(key,markerDict[key])
            self.ids.markerSpace.add_marker_widget(m,anim_duration=0.2)
            
    def add_marker(self,p):
        
        if self.is_locked:
            return
        
        #get markers from json store
        if self.store.exists('markers'):
            markerDict = self.store.get('markers')['dict']
        else:
            markerDict = {}
        
        #append markers in json store      
        entry = App.get_running_app().gps_location
        entry['p'] = p
        entry['active']=True
        
        # generate sha1 hash of length 8 as key for this marker
        dt=datetime.datetime.now()
        nhex = 8
        # Collision probability for 8 hexadecimal digits:
        #
        #   #markers        Probabilitiy
        #         10        1.04773789644e-08
        #        100        1.15251168609e-06
        #       1000        0.000116298906505
        hash = hashlib.sha1()
        hash.update(dt.__str__().encode('utf-8'))
        key = hash.hexdigest()[:nhex]
        
        entry['time'] = h.date2string(dt)
        
        markerDict[key]=entry
        self.store.put('markers',dict=markerDict)
        
        #add as widget to main screen
        m = Marker(key,entry)
        self.ids.markerSpace.add_marker_widget(m)
        
        #recalibrate
        self.calibrate()
        
    def delete_marker_from_store(self,key):
        if self.is_locked:
            return
        markerDict = self.store.get('markers')['dict']
        markerDict.pop(key,None)
        self.store.put('markers',dict=markerDict)
        
    #register double tap to add marker
    def on_touch_down(self, touch):
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if self.ids.image.collide_point(*touch.pos):
            if touch.is_double_tap:
                #p = self.to_local(touch.pos[0],touch.pos[1])
                p = (touch.pos[0],touch.pos[1])
                self.add_marker(p)
        #ret = super(Map, self).on_touch_down(touch)
        touch.pop()
        return super(Map, self).on_touch_down(touch)
        #return ret
        
    
    # check if map is moved to "trash"
    def on_transform_with_touch(self,touch):
        if self.disabled:
            return True
        
        super(Map, self).on_transform_with_touch(touch)
        
        global screenManager
        
        #remove the map if it is dragged to the top right corner
        btn = screenManager.get_screen('main').maps_button
        if ((self.center_x > btn.x ) and
            (self.center_y > btn.y ) and
            (self.scale <= 2*self.init_scale)):
            if self.parent:
                self.disabled = True
                self.fly_out(0.5)
                return True
            
        return True

#========================================================================#
class MarkerLayout(FloatLayout):
#========================================================================#
    #
    # Children of this layout move with the parent's scatter's transform, # but keep their size and orientation
    #
    
    global screenManager
    
    bubbled_marker = None
    
    def update_child_position(self,obj,value):
        for m in self.children:
            m.pos = self.parent.to_parent(m.p[0],m.p[1])
            
    def add_marker_widget(self,marker,anim_duration=0):
        if screenManager.get_screen('main').markers_visible and anim_duration>0:
            anim = Animation(opacity=1,duration=anim_duration)
            anim.start(marker)
        else:
            marker.show()
        
        #draw the marker
        marker.pos = self.parent.to_parent(marker.p[0],marker.p[1])  #TODO why is this necessary?
        self.add_widget(marker)
        
        if not screenManager.get_screen('main').markers_visible:
            def rm_wd(animation,widget):
                self.remove_widget(widget)
            anim = Animation(opacity=0,duration=2.0)
            anim.start(marker)
            anim.bind(on_complete=rm_wd)
    
    def remove_marker_widgets(self):
        
        def rm_wd(animation,widget):
            self.remove_widget(widget)
        
        for marker in self.children:
            anim = Animation(opacity=0,duration=0.5)
            anim.start(marker)
            anim.bind(on_complete=rm_wd)
            
    def on_touch_down(self,touch):
        
        touch.push()
        touch.apply_transform_2d(self.parent.to_parent)

        for marker in self.children:
            if marker.ids.pin.collide_point(*touch.pos):
                if not marker.has_bubble:
                    #first, check if touch collides with a bubbled marker
                    if not (self.bubbled_marker and \
                            self.bubbled_marker.children[0].collide_point(*touch.pos)):
                        # bring marker to front on touch and start bubble mode
                        self.remove_widget(marker)
                        self.add_widget(marker)
                        marker.show_bubble()
                        if self.bubbled_marker:
                            self.bubbled_marker.remove_bubble()
                        self.bubbled_marker = marker
                        break
                #ret = super(MarkerLayout, self).on_touch_down(touch)
                #touch.pop()
                #return ret
            else:
                # click somewhere else is like Popups dismiss
                if marker.has_bubble:
                    if not marker.children[0].collide_point(*touch.pos):
                        marker.remove_bubble()
                        #self.bubbled_marker = None
                        #break
        ret = super(MarkerLayout, self).on_touch_down(touch)
        touch.pop()
        return ret
            
            
            
#========================================================================#
class Marker(FloatLayout):
#========================================================================#
    
    id = ''
    info={}
    
    p = (0,0)
    has_bubble = False
    
    def __init__(self,id,info, **kwargs):
        super(Marker, self).__init__(**kwargs)
        self.id = id
        self.p = info['p']
        self.pos = self.p
        self.info = info
        if not self.info['active']:
            self.ids.pin.source = 'data/images/pin_gray2.png'
        with self.canvas:
            self.opacity = 0
            
    def show(self):
        with self.canvas:
            self.opacity = 1
            
    def show_bubble(self):
        self.has_bubble = True
        self.add_widget(MarkerBubble(self.info))
        
        cs = [self.info['lon'],self.info['lat'] ]
        print(self.parent.parent.projection.proj(cs))
        
        #this is ugly:
        #   self.parent.parent        is map 
        #   self.parent.parent.parent is mapLayout
        start = self.parent.parent.to_parent(self.p[0],self.p[1])
        end   = self.parent.parent.parent.center
        displacement = (end[0]-start[0],end[1]-start[1])
        self.parent.parent.moveWithAnimation(displacement,0.15)
        
    def remove_bubble(self):
        self.remove_widget(self.children[0])
        self.has_bubble = False
        self.parent.bubbled_marker=None
        
    def deactivate(self):
        self.ids.pin.source = 'data/images/pin_gray2.png'
        self.info['active']=False
        self.parent.parent.calibrate()
        
        
    def activate(self):
        self.ids.pin.source = 'data/images/pin_blue2.png'
        self.info['active']=True
        self.parent.parent.calibrate()
        
    def delete(self,*largs):
        self.parent.parent.delete_marker_from_store(self.id)
        self.parent.parent.calibrate()
        self.remove_bubble()
        self.parent.remove_widget(self)
        
   
#========================================================================#
class MarkerBubble(Bubble):
#========================================================================#
    
    def __init__(self,info,**kwargs):
        super(MarkerBubble,self).__init__(**kwargs)
        self.ids.lolala.update(gps_location=info)
        if info['active']:
            self.ids.button_deactivate.source = 'data/images/icon_powerButton.png'
            self.ids.button_deactivate.labeltext = 'Deactivate'
        else:
            self.ids.button_deactivate.source = 'data/images/icon_powerButton_gray.png'
            self.ids.button_deactivate.labeltext = 'Activate'
            
       
    #def on_touch_down(self,touch):
        #if self.collide_point(*touch.pos):
            #print "collision"
            #if self.ids.button_trash.collide_point(*touch.pos):
                #print " with trash button"
            #if self.ids.button_deactivate.collide_point(*touch.pos):
                #print " with deactivate button"
            ##return True
        #return super(MarkerBubble,self).on_touch_down(touch)
        
    def trash_button(self):
        map = screenManager.get_screen('main').get_current_map()
        if map.is_locked:
            return
        popup = ConfirmPopup("Are you sure you want to delete this marker?", self.parent.delete)
        popup.open()
        
        
    def active_button(self):
        map = screenManager.get_screen('main').get_current_map()
        if map.is_locked:
            return
        if self.parent.info['active']:
            self.ids.button_deactivate.source = 'data/images/icon_powerButton_gray.png'
            self.ids.button_deactivate.labeltext = 'Activate'
            self.parent.deactivate()
            
        else:
            self.ids.button_deactivate.source = 'data/images/icon_powerButton.png'
            self.ids.button_deactivate.labeltext = 'Deactivate'
            self.parent.activate()

#========================================================================#
class Location(FloatLayout):
#========================================================================#
    p = (0,0)
    
    def __init__(self,pos=(0,0), **kwargs):
        super(Location, self).__init__(**kwargs)
        self.p = pos
        self.pos = self.p
        with self.canvas:
            self.opacity=0.0
            
    def update(self,pos,p):
        self.pos = pos
        self.p   = p

        with self.canvas:
            self.opacity=1.0
            
        

#========================================================================#
class MapFixApp(App):
#========================================================================#
    title = 'MapFix'
    __version__ = mapfix.__version__

    
    #this is the raw dict returend by "on_location"
    gps_location = {}
    
    # time of the last GPS fix
    gps_fix = datetime.datetime(1985, 10, 3, 18, 00)
    
    # 0 means no signal, 1 means ok signal, 2 means good signal
    gps_quality_level = 0
    
    #This is used to display coordinates in menu bar
    accuracy_string = StringProperty()
    
    # remember previous screen and transition for back button
    previous_screen = []
    next_transition = []
    
    #TODO not used, copy and paste from example
    gps_status = StringProperty()

    def build(self):
        global screenManager
        
        #screen manager for settings, map selection menu etc...
        screenManager.add_widget(MainScreen(name='main'))
        screenManager.add_widget(MapsMenu(name='maps'))
        screenManager.add_widget(SettingsMenu(name='settings'))
        
        # start at main screen
        screenManager.current = 'main'
        
        #configure gps
        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
            #gps.start(1000,0)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = 'GPS is not implemented for your platform'
            
        #Do stuff every second, e.g. check for age of gps_fix
        Clock.schedule_interval(self.check_gps_age,1.)
        Clock.schedule_interval(screenManager.get_screen('main').ids.info_bar.update,1.)
        
        #register keyboard events
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

        # get max texture size of opengl
        MAX_TEXTURE_SIZE = 0x0D33
        gl_register_get_size(MAX_TEXTURE_SIZE, 1)
        h.maxTextureSize = glGetIntegerv(MAX_TEXTURE_SIZE)[0]
                
        return screenManager
    
    @mainthread
    def on_location(self, **kwargs):
        global screenManager
        
        #remember all info from the GPS fix
        self.gps_location = kwargs
        
        # remember the time to check the age of the last fix
        self.gps_fix = datetime.datetime.now()
        
        #update the location on (all) currently opened map(s)
        for m in screenManager.get_screen('main').maps_layout.children:
            m.update_current_location(self.gps_location)
        
        #two levels for accuracy: ok, and good
        self.accuracy_string = "{:.0f} m".format(self.gps_location['accuracy'])
        if self.gps_location['accuracy']<10:
            self.gps_quality_level = 2
            screenManager.get_screen('main').ids.satellite_icon.source = 'data/images/icon_gps_green.png'
        else:
            self.gps_quality_level = 1
            screenManager.get_screen('main').ids.satellite_icon.source = 'data/images/icon_gps_orange.png'
        
        
        

    #TODO not used, copy and paste from example
    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)
        
    # no signal if the last GPS fix is older than one second
    def check_gps_age(self,dt):
        now =datetime.datetime.now()
        age = (now-self.gps_fix).total_seconds()
        if age>1.5:
            self.gps_quality_level = 0
            screenManager.get_screen('main').ids.satellite_icon.source = 'data/images/icon_gps_red.png'
            self.accuracy_string = "No Signal"
        
            
    def hook_keyboard(self, window, key, *largs):
        global screenManager
        if key == 27:
            if self.previous_screen:
                t = self.next_transition.pop()
                p = self.previous_screen.pop()
                screenManager.transition.direction = t
                screenManager.current = p
                return True
            #else:
                ##TODO This causes the app to crash when closing.
                ##workaround: simply return False when the previous_screen
                ## stack is empty and let the app close on the back button
                ## as usual
                #popup = ConfirmPopup("Are you sure you want to quit?",App.get_running_app().stop)
                #popup.open()
                #return True
        return False
    
    def switch_screen(self,current='main',direction='up',previous='main'):
        global screenManager
        if direction=='left':
            self.next_transition.append('right')
        elif direction == 'right':
            self.next_transition.append('left')
        elif direction == 'up':
            self.next_transition.append('down')
        elif direction == 'down':
            self.next_transition.append('up')
        else:
            self.next_transition.append('down')
        self.previous_screen.append(previous)
        screenManager.transition.direction = direction
        screenManager.current = current
        

    def on_start(self):
        return self.on_resume()

    def on_stop(self):
        return self.on_pause()

    def on_pause(self):
        try:
            gps.stop()
        except:
            print("GPS not implemented on this platform")
        return True

    def on_resume(self):
        try:
            gps.start(1000, 0)
        except:
            print("GPS not implemented on this platform")
        
