import math
import os, json
import lgdo.lh5_store as lh5
import numpy as np
from legendmeta import LegendMetadata
from legendmeta.catalog import Props
from matplotlib.colors import LogNorm
import pandas as pd
import glob
import sys

import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.patches as mpatches

from utils import *

sto=lh5.LH5Store()

def is_coax(d):
    return d['type'] == 'coax'

def is_taper(f):
    return f != {'angle_in_deg': 0, 'height_in_mm': 0} and f != {'radius_in_mm': 0, 'height_in_mm': 0}

def is_bulletized(f):
    return 'bulletization' in f and f['bulletization'] != {'top_radius_in_mm': 0, 'bottom_radius_in_mm': 0, 'borehole_radius_in_mm': 0, 'contact_radius_in_mm': 0}

def has_groove(f):
    return 'groove' in f and f['groove'] != {'outer_radius_in_mm': 0, 'depth_in_mm': 0, 'width_in_mm': 0}

def has_borehole(f):
    return 'borehole' in f and f['borehole'] != {'gap_in_mm': 0, 'radius_in_mm': 0}

def plot_geometry(d, R, H):
    
    coax = is_coax(d)
    
    g = d['geometry']
    
    DH = g['height_in_mm']
    DR = g['radius_in_mm']

    xbot = []
    ybot = []

    # botout = g['taper']['bottom']['outer']
    botout = g['taper']['bottom']
    if is_taper(botout):
        TH = botout['height_in_mm']
        TR = botout['radius_in_mm'] if 'radius_in_mm' in botout else TH * math.sin(botout['angle_in_deg'] * math.pi/180)
        xbot.extend([DR, DR-TR])
        ybot.extend([H-DH+TH,H-DH])
    else:
        xbot.append(DR)
        ybot.append(H-DH)

    if has_groove(g):
        # GR = g['groove']['outer_radius_in_mm']
        GR = g['groove']['radius_in_mm']['outer']
        GH = g['groove']['depth_in_mm']
        # GW = g['groove']['width_in_mm']
        GW = g['groove']['radius_in_mm']['outer'] - g['groove']['radius_in_mm']['inner']
        xbot.extend([GR,GR,GR-GW,GR-GW])
        ybot.extend([H-DH,H-DH+GH,H-DH+GH,H-DH])
        
    if coax:
        BG = g['borehole']['depth_in_mm']
        BR = g['borehole']['radius_in_mm']
        xbot.extend([BR, BR])
        ybot.extend([H-DH, H-DH+BG])
        

    xtop = []
    ytop = []

    # topout = g['taper']['top']['outer']
    topout = g['taper']['top']
    if is_taper(topout):
        TH = topout['height_in_mm']
        TR = TH * math.sin(topout['angle_in_deg'] * math.pi/180)
        xtop.extend([DR, DR-TR])
        ytop.extend([H-TH, H])
    else:
        xtop.append(DR)
        ytop.append(H)

    if has_borehole(g) and not coax:
        BG = g['borehole']['depth_in_mm']
        BR = g['borehole']['radius_in_mm']

        # topin  = g['taper']['top']['inner']
        topin  = g['taper']['top']
        if is_taper(topin):
            TH = topin['height_in_mm']
            TR = TH * math.sin(topin['angle_in_deg'] * math.pi/180)
            xtop.extend([BR+TR,BR,BR])
            ytop.extend([H, H-TH, H-DH+BG])     
        else:
            xtop.extend([BR, BR])
            ytop.extend([H, H-DH+BG])


    x = np.hstack(([-x+R for x in xbot], [x+R for x in xbot[::-1]],[x + R for x in xtop],[-x+R for x in xtop[::-1]]))  
    y = np.hstack((ybot, ybot[::-1],ytop,ytop[::-1]))  
    return x, y


def get_plot_source_and_xlabels(chan_dict, channel_map, strings_dict, ΔR = 160, ΔH = 40):

    xs = []
    ys = []
    ch = []
    hw = []
    sw = []
    dn = []
    st = []
    pos = []
    ax = []
    ay = []

    maxH = 0
    R = 0
    H = 0

    xlabels = dict()

    for (name, string) in strings_dict.items():

        xlabels[R] = name

        for channel_no in string:
            ch.append(channel_no)
            status = chan_dict[channel_map[channel_no]['name']]
            hw.append(status['usability'])
            sw.append(status['processable'])
            channel = channel_map[channel_no]
            dn.append(channel['name'])
            st.append(channel['location']['string'])
            pos.append(channel['location']['position'])
            x,y = plot_geometry(channel, R, H)
            xs.append(x)
            ys.append(y)
            H -= channel['geometry']['height_in_mm'] + ΔH
            ax.append(R)
            ay.append(H+10)
        R += ΔR
        maxH = min(H, maxH)
        H = 0
    return xs, ys  

def plt_detector_plot(fig, axes, patches, display_dict, 
                         ctitle = "", plot_title = "LEGEND event view" 
                        ):
    
    minvalue = 25; maxvalue = 6000

    cNorm = mpl.colors.Normalize(vmin=25, vmax=4000)
    vir = mpl.colormaps['viridis']
    vir.set_under("grey")
    vir.set_bad("white")
    
    cNorm = mpl.colors.Normalize(vmin=25, vmax=4000)
    
    p = PatchCollection(patches, cmap = vir)
    p.set_array(np.array(list(map(lambda v : np.nan if v is None or math.isnan(v)  else v, display_dict.values()))))
    p.set_ec("black")
    p.set_norm(cNorm)
    
    axes.add_collection(p)
    axes.spines['top'].set_visible(False)
    axes.spines['bottom'].set_visible(False)
    axes.spines['right'].set_visible(False)
    axes.spines['left'].set_visible(False)

    # if fig.first_call == True:    
    plt.colorbar(p, ax=axes, label= ctitle)
    axes.set_xlim([-100,1500])
    axes.set_ylim([-1200,30])
    axes.set_title(plot_title)
    axes.set_yticks([])
    axes.set_xticks([])
    



class event_viewer():
    
        
    def __init__(self, fig):
        self.fig=fig
        self.prod_cycle = f"/data2/public/prodenv/prod-blind/ref/v01.06"#os.cwd()
        self.config = Props.read_from(os.path.join(self.prod_cycle,"config.json"), 
                subst_pathvar={"$":self.prod_cycle})["setups"]["l200"]["paths"]
        self.meta = LegendMetadata(self.config["metadata"])
        self.raw_file, self.dsp_file, self.hit_file = (None, None, None)
        self.strings_dict = {}
        self.events_per_file_cache={}
        self.baseline_channels={}

    
    def get_phy_event_position(self, period, run, file_tstamp, idx):
    
        file_path = os.path.join(self.config["tier_hit"],
                                 f"phy/{period}/{run}/l200-{period}-{run}-phy-{file_tstamp}-tier_hit.lh5")
        files = sorted(glob.glob(file_path))
        events_per_file = [] 
        for file in files:
            if file in list(self.events_per_file_cache):
                events_per_file.append(self.events_per_file_cache[file]) 
            else:
                _,per,_,_,tstamp,_ = os.path.basename(file).split("-")
                if per not in list(self.baseline_channels):
                    self.baseline_channels[per] = self.meta.channelmap(tstamp)["BSLN01"].daq.rawid
                    
                baseline_channel = self.baseline_channels[per]
                n_events = sto.read_n_rows(f"ch{baseline_channel}/raw/baseline", 
                                           file.replace(self.config["tier_hit"], 
                                                        self.config["tier_raw"]).replace("hit", "raw"))
                events_per_file.append(n_events)
                self.events_per_file_cache[file] = n_events
            if np.cumsum(events_per_file)[-1]>idx:
                break
        cum_events = np.cumsum(events_per_file)
        file_n = np.argmin(np.where((cum_events-idx)>0, cum_events, np.inf))
        if file_n >0:
            start_r = idx-cum_events[file_n-1]
        else:
            start_r = idx
        file = files[file_n]
        return (file.replace(self.config["tier_hit"], self.config["tier_raw"]).replace("hit", "raw"), 
                file.replace(self.config["tier_hit"], self.config["tier_dsp"]).replace("hit", "dsp"), 
                file, start_r)
    
    def _get_event(self, period, run, file_tstamp, idx):
        self.raw_file, self.dsp_file, self.hit_file, self.index = self.get_phy_event_position(period, run, file_tstamp, idx)
        self.chmap = self.meta.channelmap(os.path.basename(self.hit_file).split("-")[4])
        self.dets = self.chmap.map("system", unique=False).geds.map("name")
        self.working_dets = [det for det in self.dets if self.chmap[det]["analysis"]["processable"] == True]
        self.energy_dict = {det : sto.read_object(f'ch{self.chmap[det].daq.rawid}/hit/cuspEmax_ctc_cal', 
                                            self.hit_file, start_row = self.index, n_rows=1)[0].nda[0] 
                                            if det in self.working_dets else None 
                                            for det in self.dets }
        for key, item in self.energy_dict.items():
            if item is None:
                pass
            elif np.isnan(item):
                self.energy_dict[key] = 0 

    def plot_event(self, period, run, file_tstamp, idx):
        self._get_event(period, run, file_tstamp, idx)
        
        strings_dict, chan_dict, channel_map  = sorter(self.prod_cycle, os.path.basename(self.hit_file).split("-")[4])
        if strings_dict == self.strings_dict:
            self.p.set_array(np.array(list(map(lambda v : np.nan if v is None or math.isnan(v)  else v, self.energy_dict.values()))))
            self.axes.set_title(f'file:{os.path.basename(self.hit_file).split("-tier")[0]} idx:{self.index}')
        else:
            self.strings_dict = strings_dict
            xs,ys = get_plot_source_and_xlabels(chan_dict, channel_map, self.strings_dict, ΔR = 160, ΔH = 40)
            patches = []
            for x,y in zip(xs,ys):
                coords = []
                for i in range(len(x)):
                    coords.append([x[i],y[i]])
                polygon = plt.Polygon(coords, True, edgecolor="black")
                patches.append(polygon)
            self.fig.clf()
            self.axes = self.fig.add_subplot(111)
            self.plt_detector_plot(patches, ctitle = "energy (keV)", plot_title = f'file:{os.path.basename(self.hit_file).split("-tier")[0]} idx:{self.index}')
        self.fig.canvas.draw()
            
    def plt_detector_plot(self, patches, 
                         ctitle = "", plot_title = "LEGEND event view" 
                        ):
    
        minvalue = 25; maxvalue = 6000

        cNorm = mpl.colors.Normalize(vmin=25, vmax=4000)
        vir = mpl.colormaps['viridis']
        vir.set_under("grey")
        vir.set_bad("white")

        cNorm = mpl.colors.Normalize(vmin=25, vmax=4000)

        self.p = PatchCollection(patches, cmap = vir)
        self.p.set_array(np.array(list(map(lambda v : np.nan if v is None or math.isnan(v)  else v, self.energy_dict.values()))))
        self.p.set_ec("black")
        self.p.set_norm(cNorm)

        self.axes.add_collection(self.p)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['bottom'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['left'].set_visible(False)

        # if fig.first_call == True:    
        self.fig.colorbar(self.p, ax=self.axes, label= ctitle)
        self.axes.set_xlim([-100,1500])
        self.axes.set_ylim([-1200,30])
        self.axes.set_title(plot_title)
        self.axes.set_yticks([])
        self.axes.set_xticks([])
        