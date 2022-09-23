#!/usr/bin/python
# make_geojson_v2.py
# Created: 9/22/2022 Will Shatford
#__author__ = "Will Shatford"
#__copyright__ = "Copyright 2022"
#__credits__ = ["Will Shatford"]
#__license__ = "GPL"
#__version__ = "2.0"
#__maintainer__ = "Will Shatford"
#__email__ = "willshatford@gmail.com"
#__status__ = "Production"
#
#Python 3.6

from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import range
from past.utils import old_div
import datetime
import getopt
import os
import sys
import time
import png
import urllib.request, urllib.parse, urllib.error
import numpy
import itertools
from rdp import rdp
import math

output_path=""
m_skipthin = False

# provided as parameters
m_geom = ""

m_latc=0.0  # Estimated center of geom.  Used to show map on website
m_lngc=0.0

m_lat1=0.0 # from google map, upper right corner
m_lng1=0.0

m_lat2=0.0 # # from google map, lower left corner
m_lng2=0.0

# constants
#Radius of earth in Miles
#m_R = 3958.7558657440545
#Radius of earth in Feet
m_R = 3958.7558657440545 * 5280

# used in calculations
m_x1=0  # from png file, upper right corner, pixel
m_y1=0
m_x2=0  # from png file, lower left corner, pixel
m_y2=0
m_newlng = 0.0
m_newlat = 0.0
m_pointx = 0
m_pointy = 0
m_scale = 0.0

m_goodopts = True

#####################
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#####################
# get any passed arguments
def p_getopts(argv):
    global m_geom
    global m_latc # Estimated center of geom.  Used to show map on website
    global m_lngc
    global m_lat1 # from google map, upper right corner
    global m_lng1
    global m_lat2 # from google map, lower left corner
    global m_lng2
    global m_goodopts
    global m_skipthin

    try:
        opts, args = getopt.getopt(argv, "hpf:i:s:e:c:")
    except getopt.GetoptError:
        arg_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            arg_help()
            sys.exit()
        elif opt == '-s':
            m_latlng = arg
            m_pos = m_latlng.find(",")
            if m_pos<0 or m_pos==1 or m_pos==len(m_latlng)-1:
                m_goodopts = False
            elif not is_number(m_latlng[:m_pos]):
                m_goodopts = False
            elif not is_number(m_latlng[m_pos+1:]):
                m_goodopts = False
            else:
                m_lng1 = float(m_latlng[m_pos+1:])
                m_lat1 = float(m_latlng[:m_pos])
        elif opt == '-e':
            m_latlng = arg
            m_pos = m_latlng.find(",")
            if m_pos<0 or m_pos==1 or m_pos==len(m_latlng)-1:
                m_goodopts = False
            elif not is_number(m_latlng[:m_pos]):
                m_goodopts = False
            elif not is_number(m_latlng[m_pos+1:]):
                m_goodopts = False
            else:
                m_lng2 = float(m_latlng[m_pos+1:])
                m_lat2 = float(m_latlng[:m_pos])
        elif opt == '-c':
            m_latlng = arg
            m_pos = m_latlng.find(",")
            if m_pos<0 or m_pos==1 or m_pos==len(m_latlng)-1:
                m_goodopts = False
            elif not is_number(m_latlng[:m_pos]):
                m_goodopts = False
            elif not is_number(m_latlng[m_pos+1:]):
                m_goodopts = False
            else:
                m_lngc = float(m_latlng[m_pos+1:])
                m_latc = float(m_latlng[:m_pos])
        elif opt == '-f':
            print('geom', arg)
            m_geom = "".join(x for x in arg if (x.isalnum() or x == '-' or x == '_'))
        elif opt == '-p':
            m_skipthin = True

##########
def arg_help():
        print(' -f the name of the geom, for example:  -f "Hobart"')
        print('    expects to find an image file with this name:  Hobart.png')
        print(' -s the lat/lng for the highest point in the image file, usually upper-right corner')
        print(' -e the lat/lng for the lowest point in the image, usually lower-left corner')
        print(' -c the preferred center lat/lng of the geom.')
        print('    lat/lng data entered as "lat,lng":   -s "-42.8823389,147.3110419"')
        print(' -p special processing to skip the thinning and prunning step.')
        time.sleep(1)


#####################
def p_getlatlng():
    global m_x1  # The origin location (pixels) in the image
    global m_y1
    global m_lat1  # The new point is an offset from the origin lat/lng
    global m_lng1
    global m_pointx  # The new point (pixels) for which we need lat/lng
    global m_pointy
    global m_newlng  # The returned lat/lng for m_pointx,m_pointy
    global m_newlat
    global m_R
    global m_scale

    # first get the offset to the new point, in feet
    m_newx = (m_pointx - m_x1) * m_scale  # A higher value for pointx will decrease lat
    m_newy = (m_y1 - m_pointy) * m_scale  # A higher value for pointy will increase lng

    # calculate the lat/lng at this point
    m_newlat = m_lat1 + (old_div(m_newy,m_R)) * (old_div(180,math.pi))
    m_newlng = m_lng1 + old_div((old_div(m_newx,m_R)) * (old_div(180,math.pi)), math.cos(math.radians(m_lat1)))
    if m_newlng > 360:
        m_newlng -= 360

    return (0)

#####################
def p_writegeomfile():
    global a_p2
    global m_geom
    global m_newlng
    global m_newlat
    global m_pointx
    global m_pointy
    global m_latc
    global m_lngc
    global output_path

    m_file = m_geom + ".geom"
    output_fullpath_txt = output_path + m_file
    print("Output file: ", output_fullpath_txt)
    with open(output_fullpath_txt, 'w') as f:
        f.write("INSERT INTO geoms (name, geom_pt, geom)\n")
        f.write("VALUES (")
        f.write("'"+ m_geom +"',")
        f.write("ST_GeomFromText('POINT(" + '{0:.15f}'.format(float(m_lngc)) + " " + '{0:.15f}'.format(float(m_latc)) + ")', 4326),\n")
        f.write("ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(ST_Multi(ST_GeomFromGeoJSON ('{" + '"type": "MultiPolygon", "coordinates": [ [ [\n')

        m_first = True
        m_points = len(a_p2)
        m_pointer = 0
        while m_pointer < m_points:
            if m_first:
                m_first = False
            else:
                f.write(",")
            m_point = a_p2[m_pointer]
            #print m_point[0],m_point[1]
            m_pointx = m_point[1]
            m_pointy = m_point[0]
            m_ok = p_getlatlng()
            f.write("[" + '{0:.15f}'.format(float(m_newlng)) + "," + '{0:.15f}'.format(float(m_newlat)) + "]\n")
            m_pointer += 1

        f.write("] ] ],\n")
        f.write('"crs":{"type":"name","properties":{"name":"EPSG:4326"}}')
        f.write("}'")
        f.write(")),.0001)), 3))")
        f.write(")\n")

    m_file = m_geom + "_geom.geom"
    output_fullpath_txt = output_path + m_file
    print("Output file: ", output_fullpath_txt)
    with open(output_fullpath_txt, 'w') as f:
        f.write("ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(ST_Multi(ST_GeomFromGeoJSON ('{" + '"type": "MultiPolygon", "coordinates": [ [ [\n')

        m_first = True
        m_points = len(a_p2)
        m_pointer = 0
        while m_pointer < m_points:
            if m_first:
                m_first = False
            else:
                f.write(",")
            m_point = a_p2[m_pointer]
            #print m_point[0],m_point[1]
            m_pointx = m_point[1]
            m_pointy = m_point[0]
            m_ok = p_getlatlng()
            f.write("[" + '{0:.15f}'.format(float(m_newlng)) + "," + '{0:.15f}'.format(float(m_newlat)) + "]\n")
            m_pointer += 1

        f.write("] ] ],\n")
        f.write('"crs":{"type":"name","properties":{"name":"EPSG:4326"}}')
        f.write("}'")
        f.write(")),.0001)), 3))")

    return (0)

###################
def p_writegeojsonfile():
    global a_p2
    global m_geom
    global m_lat1
    global m_lng1
    global m_pointx
    global m_pointy
    global output_path

    m_lat = 0
    m_lng = 0

    m_file = m_geom + ".geojson"
    output_fullpath_txt = output_path + m_file
    print("Output file: ", output_fullpath_txt)
    with open(output_fullpath_txt, 'w') as f:
        f.write('{"type": "FeatureCollection",')
        f.write('"features":[{"type":"Feature","geometry":')
        f.write('{"type":"MultiPolygon","coordinates":[[[\n')

        m_first = True
        m_points = len(a_p2)
        m_pointer = 0
        while m_pointer < m_points:
            if m_first:
                m_first = False
            else:
                f.write(",")
            m_point = a_p2[m_pointer]
            m_pointx = m_point[1]
            m_pointy = m_point[0]
            m_ok = p_getlatlng()
            m_pointx = m_point[0],m_point[1]," => ",m_newlng,m_newlat
            f.write("[" + '{0:.15f}'.format(float(m_newlng)) + "," + '{0:.15f}'.format(float(m_newlat)) + "]\n")
            m_pointer += 1

        f.write(']]]}')
        f.write(',"properties": {"prop0": "value0","prop1": {"this": "that"}}}')
        f.write(']}\n')

    return (0)

##########
def p_hunt():
    global m_x1
    global m_y1
    global last_y
    global last_x
    global m_from_dir
    global image_3d

    m_alldone = False
    m_ok = 1

    m_loop = 1
    while m_loop<100:
        m_change_angle = old_div(90,m_loop)
        #while m_change_angle < (360 - m_change_angle/2):
        #while m_change_angle < 315:
        while m_change_angle < 337:
            m_new_angle = m_from_dir - m_change_angle
            if m_new_angle<0:
                m_new_angle += 360

            m_chg_x = int(round(m_loop*math.cos(math.radians(m_new_angle)),0))
            m_chg_y = -int(round(m_loop*math.sin(math.radians(m_new_angle)),0))
            print(m_loop,m_new_angle,m_chg_y,m_chg_x,last_y+m_chg_y,last_x+m_chg_x)
            #time.sleep(0.5)

            if last_y+m_chg_y < m_y1:
                m_alldone = True
            elif image_3d[last_y+m_chg_y,last_x+m_chg_x,0]==255:
                #print "done"
                last_y += m_chg_y
                last_x += m_chg_x
                m_from_dir = 45*int(round(old_div(m_new_angle,45),0)) - 180
                if m_from_dir == 360:
                    m_from_dir = 0
                if m_from_dir < 0:
                    m_from_dir += 360

                m_ok = 0
                break

            if m_loop < 45:
                m_change_angle += old_div(45,m_loop)
            else:
                m_change_angle += 1

        if m_alldone or m_ok==0:
            break

        m_loop += 1

    return (m_ok)

##########
def p_findnext():
    global m_y1
    global last_y
    global last_x
    global m_from_dir
    global image_3d
    global m_huntloops
    global m_maxhuntloops

    m_alldone = False
    m_ok = 1

    m_change_angle = 90
    while m_change_angle < 315:
        m_new_angle = m_from_dir - m_change_angle
        if m_new_angle<0:
            m_new_angle += 360

        m_chg_x = int(round(math.cos(math.radians(m_new_angle)),0))
        m_chg_y = -int(round(math.sin(math.radians(m_new_angle)),0))
        #print m_new_angle,m_chg_y,m_chg_x
        #time.sleep(1)

        if last_y+m_chg_y < m_y1:
            m_alldone = True
        elif image_3d[last_y+m_chg_y,last_x+m_chg_x,0]==255:
            #print "done"
            last_y += m_chg_y
            last_x += m_chg_x
            m_from_dir = m_new_angle - 180
            if m_from_dir == 360:
                m_from_dir = 0
            if m_from_dir < 0:
                 m_from_dir += 360

            m_ok = 0
            break

        m_change_angle += 45

    if not m_alldone and m_ok == 1:
        if m_huntloops<m_maxhuntloops:
            print("hunting...")
            m_ok = p_hunt()
            m_huntloops += 1

    return (m_ok)

################
def savefile():
        global image_3d

        m_changed = False

        # copy results back to original
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]!=image_3d[y,x,1]:
                    image_3d[y,x,0]=image_3d[y,x,1]
                    m_changed = True
                image_3d[y,x,1]=0
        if m_changed:
            return (1)
        else:
            return (0)

################
def thinning():
        global image_3d

        m_allok = 0

        # thinning a1
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y-1,x,0]==0 and image_3d[y-1,x+1,0]==0 and image_3d[y+1,x-1,0]==255 and image_3d[y+1,x,0]==255 and image_3d[y+1,x+1,0]==255:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_allok = savefile()

        # thinning b1
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x,0]==0 and image_3d[y-1,x+1,0]==0 and image_3d[y,x-1,0]==255 and image_3d[y,x+1,0]==0 and image_3d[y+1,x,0]==255:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # thinning a2
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y-1,x+1,0]==255 and image_3d[y,x-1,0]==0 and image_3d[y,x+1,0]==255 and image_3d[y+1,x-1,0]==0 and image_3d[y+1,x+1,0]==255:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # thinning b2
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y-1,x,0]==0 and image_3d[y,x-1,0]==0 and image_3d[y,x+1,0]==255 and image_3d[y+1,x,0]==255:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # thinning a3
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==255 and image_3d[y-1,x,0]==255 and image_3d[y-1,x+1,0]==255 and image_3d[y+1,x-1,0]==0 and image_3d[y+1,x,0]==0 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # thinning b3
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x,0]==255 and image_3d[y,x-1,0]==0 and image_3d[y,x+1,0]==255 and image_3d[y+1,x-1,0]==0 and image_3d[y+1,x,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # thinning a4
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==255 and image_3d[y-1,x+1,0]==0 and image_3d[y,x-1,0]==255 and image_3d[y,x+1,0]==0 and image_3d[y+1,x-1,0]==255 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # thinning b4
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x,0]==255 and image_3d[y,x-1,0]==255 and image_3d[y,x+1,0]==0 and image_3d[y+1,x,0]==0 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        return(m_allok)

################
def pruning():
        global image_3d

        m_allok = 0

        # a1
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y-1,x,0]==0 and image_3d[y-1,x+1,0]==0 and image_3d[y,x-1,0]==0 and image_3d[y,x+1,0]==0 and image_3d[y+1,x-1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_allok = savefile()

        # b1
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y-1,x,0]==0 and image_3d[y-1,x+1,0]==0 and image_3d[y,x-1,0]==0 and image_3d[y,x+1,0]==0 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # a2
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y-1,x,0]==0 and image_3d[y,x-1,0]==0 and image_3d[y+1,x-1,0]==0 and image_3d[y+1,x,0]==0 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # b2
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y-1,x,0]==0 and image_3d[y-1,x+1,0]==0 and image_3d[y,x-1,0]==0 and image_3d[y+1,x-1,0]==0 and image_3d[y+1,x,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # a3
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x+1,0]==0 and image_3d[y,x-1,0]==0 and image_3d[y,x+1,0]==0 and image_3d[y+1,x-1,0]==0 and image_3d[y+1,x,0]==0 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # b3
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y,x-1,0]==0 and image_3d[y,x+1,0]==0 and image_3d[y+1,x-1,0]==0 and image_3d[y+1,x,0]==0 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # a4
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x-1,0]==0 and image_3d[y-1,x,0]==0 and image_3d[y-1,x+1,0]==0 and image_3d[y,x+1,0]==0 and image_3d[y+1,x,0]==0 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        # b4
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255 and image_3d[y-1,x,0]==0 and image_3d[y-1,x+1,0]==0 and image_3d[y,x+1,0]==0 and image_3d[y+1,x-1,0]==0 and image_3d[y+1,x,0]==0 and image_3d[y+1,x+1,0]==0:
                    image_3d[y,x,1]=0
                else:
                    image_3d[y,x,1]=image_3d[y,x,0]

        m_ok = savefile()
        if m_ok==1:
            m_allok = 1

        return(m_allok)

################################
if __name__ == '__main__':
    print("-----------------------------")
    print(" Geojson Generator ")
    print("-----------------------------")

    if len(sys.argv) > 1:
        p_getopts(sys.argv[1:])
    else:
        m_goodopts = False


    #m_red_threshold = 190
    #m_green_threshold = 80
    #m_blue_threshold = 80
    m_red_threshold = 200
    m_green_threshold = 150
    m_blue_threshold = 150
    #2018-01-19
    m_red_threshold = 210
    m_green_threshold = 170
    m_blue_threshold = 170

    print(m_geom)
    print(m_lat1,m_lng1)
    print(m_lat2,m_lng2)
    print(m_latc,m_lngc)
    #time.sleep(30)

    if not m_goodopts:
        sys.exit(0)

    # calculate distance in feet
    # used later to calculate scale between the screenshot image and real lat/lng
    m_Lat = math.radians(m_lat2) - math.radians(m_lat1)
    m_Lon = math.radians(m_lng2) - math.radians(m_lng1)
    m_A = math.sin(old_div(m_Lat,2)) * math.sin(old_div(m_Lat,2)) + math.cos(math.radians(m_lat1)) * math.cos(math.radians(m_lat2)) * math.sin(old_div(m_Lon,2)) * math.sin(old_div(m_Lon,2))
    m_C = 2 * math.atan2(math.sqrt(m_A), math.sqrt(1 - m_A))
    m_C = m_R * m_C

    m_workingfile = m_geom + ".png"
    # to skip all the line detection and thinning/pruning stuf
    # use this if put some red lines in the pruned file to help with very large gaps
    if m_skipthin:
        m_workingfile = m_geom + '_pruned.png'

    with open(m_workingfile, 'rb') as f:
        r = png.Reader(f)
        print(r)
        columnCount, rowCount, pngData, metaData = r.asDirect()
        print("Columns:",columnCount)
        print("Rows:",rowCount)
        bitDepth=metaData['bitdepth']
        planeCount = metaData['planes']
        print("BitDepth:", bitDepth)
        print("planeCount:", planeCount)

        # These files are (column, row) => (y,x)
        # With +y left-to-right and +x is top-to-bottom

        image_2d = numpy.vstack(map(numpy.uint8, pngData))
        # for easier referencing you could make the image into 3d like so
        image_3d = numpy.reshape(image_2d, (rowCount, columnCount, planeCount))

        if not m_skipthin:
            # first reduce to binary image
            for y in range(image_3d.shape[0]):
                for x in range(image_3d.shape[1]):
                    if image_3d[y,x,0]>m_red_threshold and image_3d[y,x,1]<m_green_threshold and image_3d[y,x,2]<m_blue_threshold:
                        image_3d[y,x,0]=255
                        image_3d[y,x,1]=0
                        image_3d[y,x,2]=0
                    else:
                        image_3d[y,x,0]=0
                        image_3d[y,x,1]=0
                        image_3d[y,x,2]=0

            m_loop=1
            while True:
                print("Thin cycle ",m_loop," ...")
                m_test = thinning()
                if m_test == 0:
                    print("No thinning required during this loop... done")
                    break
                m_loop += 1

            m_loop=1
            while True:
                print("Pruning cycle ",m_loop," ...")
                m_test = pruning()
                if m_test == 0:
                    break
                m_loop += 1
                if m_loop>1:
                    break

            #save the result
            print("Saving pruned file...")
            with open(m_geom + '_pruned.png', 'wb') as f_out:
                pngWriter = png.Writer(columnCount, rowCount, greyscale=False,planes=4,alpha=True,bitdepth=8)
                pngWriter.write(f_out,numpy.reshape(image_3d, (-1, columnCount*planeCount)))
            print("Saved pruned file.")

        # find top most, right most, pixel and set to m_x1, m_y1
        m_x1 = 0
        m_y1 = 0
        for y in range(1,image_3d.shape[0]-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255:
                    m_y1 = y
                    m_x1 = x
                    x_new = x
                    while x_new < image_3d.shape[1]-1:
                        if image_3d[y,x_new,0]==255:
                            m_x1 = x_new
                            x_new += 1
                        else:
                            break
                    break
            if m_y1!=0 or m_x1!=0:
                break

        print("Top Pixel:",m_y1,",",m_x1)
        time.sleep(1)

        # find lowest, left most, pixel and set to m_x2, m_y2
        m_x2 = 0
        m_y2 = 0
        for y in range(image_3d.shape[0]-1,0,-1):
            for x in range(1,image_3d.shape[1]-1):
                if image_3d[y,x,0]==255:
                    m_y2 = y
                    m_x2 = x
                    break
            if m_y2!=0 or m_x2!=0:
                break

        print("Low Pixel:",m_y2,",",m_x2)
        time.sleep(1)

        # Have lat/lng for these two points in parameters
        # and can now determine the scale between pixels and lat/lng
        # distance in pixels
        m_distancexy = math.sqrt(((m_y2 - m_y1)**2) + ((m_x2 - m_x1)**2))
        # scale = feet per pixel
        m_scale = old_div(m_C, m_distancexy)
        #m_scale *= 1.48
        print("distance feet:",m_C," distance pixels:",m_distancexy)
        print(" scale:",m_scale," feet/pixel")

        # test... should get lat2/lng2
        print("entered lat1/lng1:",m_lat1,m_lng1)
        print("entered lat2/lng2:",m_lat2,m_lng2)
        m_pointx = m_x2
        m_pointy = m_y2
        m_ok = p_getlatlng()
        print("scale   test gave:",m_newlat,m_newlng)
        time.sleep(10)

        # list to hold points
        a_p=[]
        p_coords = tuple([m_y1,m_x1])
        a_p.append(p_coords)

        # transverse
        last_y = m_y1
        last_x = m_x1
        image_3d[y,x,0]=0
        image_3d[y,x,1]=255
        m_from_dir = 180
        m_huntloops = 0
        m_maxhuntloops = 10

        while last_y < image_3d.shape[0]-1:
            m_test = p_findnext()
            if m_test == 1:
                break
            else:
                #print last_y,last_x
                image_3d[last_y,last_x,0]=0
                image_3d[last_y,last_x,1]=255
                p_coords = tuple([last_y,last_x])
                a_p.append(p_coords)

        #save the result
        print("Saving transversed file...")
        with open(m_geom + '_transversed.png', 'wb') as f_out:
            pngWriter = png.Writer(columnCount, rowCount, greyscale=False,planes=4,alpha=True,bitdepth=8)
            pngWriter.write(f_out,numpy.reshape(image_3d, (-1, columnCount*planeCount)))

        if len(a_p)>0:
            m_points = len(a_p)
            m_pointer = 0
            while m_pointer < m_points:
                m_point = a_p[m_pointer]
                #print m_point[0],m_point[1]
                m_pointer += 1

        print("RDP to remove unnecessary points...")
        # I didn't have to write this :-)
        a_p2 = rdp(a_p,2)
        if len(a_p2)>0:
            m_points = len(a_p2)
            m_pointer = 0
            while m_pointer < m_points:
                m_point = a_p2[m_pointer]
                #print m_point[0],m_point[1]
                image_3d[m_point[0],m_point[1],2]=255
                m_pointer += 1

        print("Stopped at:",last_y,last_x)
        print("len a_p",len(a_p))
        print("len a_p2",len(a_p2))

        #print "Saving transverse, with RDP overlay of blue dots..."
        #with open(m_geom + '_RDP.png', 'wb') as f_out:
        #    pngWriter = png.Writer(columnCount, rowCount, greyscale=False,planes=4,alpha=True,bitdepth=8)
        #    pngWriter.write(f_out,numpy.reshape(image_3d, (-1, columnCount*planeCount)))

        if len(a_p2)>0:
            print("Saving geom file...")
            m_ok = p_writegeomfile()
            m_ok = p_writegeojsonfile()

    print("")
    print("I think it is OK...  open the .geojson file at geojson.io.")
    print("")
    print("If it looks weird, look at the ...RDP.png file.")
    print("If not all green the process broke somewhere.")
    print("")
    print("Open the .png file and fill in some of the long gap with pure 255 red.")
    print("")
    print("Or, it is sometimes easier to fix the .pruned.png file and fill in some of the long gap with pure 255 red.")
    print("In this case, run the program again with parameter -p")
