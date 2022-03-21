#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import pandas as pd
import os
from matplotlib.lines import Line2D
import random
import random
import shutil

FAIL = "\033[91m"
ENDC = "\033[0m"


class FleeVisualization:
    def __init__(self, df, scenario):
        self.df = df
        self.scenario = scenario.capitalize()
        self.cmap, self.legend_elements = self.generate_colors()
        self.process_data()
        self.marker_scalar = (
            5000 / self.df.Result.max()
        )  # 5000 is hardcoded to best fit for the figure/frame
        self.fig, self.ax = self.generate_plt()

    def generate_colors(self):
        colors = [
            "#a6cee3",
            "#1f78b4",
            "#b2df8a",
            "#33a02c",
            "#fb9a99",
            "#e31a1c",
            "#fdbf6f",
            "#ff7f00",
            "#cab2d6",
            "#6a3d9a",
            "#ffff99",
            "#b15928",
        ]
        cmap = {}
        legend_elements = []
        chosen = set()
        for c in self.df.camp.unique():

            # use for truly random color map
            if len(self.df.camp.unique()) > 12:
                cmap[c] = "#" + "".join(
                    [random.choice("ABCDEF0123456789") for i in range(6)]
                )
            else:
                # if 12 choices or fewer use pre-baked one
                choice = random.choice(colors)
                while choice in chosen:
                    choice = random.choice(colors)
                else:
                    chosen.add(choice)
                    cmap[c] = choice

            legend_elements.append(
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color=cmap[c],
                    label=c.replace("_", " "),
                    markerfacecolor=cmap[c],
                    markersize=15,
                    linestyle="None",
                )
            )
        return cmap, legend_elements

    def process_data(self):
        self.df["Date"] = pd.to_datetime(self.df["Date"])
        self.df["Result"] = self.df.groupby("camp")["median"].cumsum()
        self.df["color"] = self.df["camp"].apply(lambda x: self.cmap[x])
        return self.df

    def generate_plt(self):
        extent = [
            self.df.Longitude.min() - 5,
            self.df.Longitude.max() + 5,
            self.df.Latitude.min() - 5,
            self.df.Latitude.max() + 5,
        ]

        request = cimgt.GoogleTiles(
            url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
        )
        request = cimgt.OSM()

        fig = plt.figure(figsize=(19.2, 10.8))
        ax = plt.axes(projection=request.crs)
        gl = ax.gridlines(draw_labels=True, alpha=0.2)
        gl.top_labels = gl.right_labels = False
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER

        ax.set_extent(extent)
        ax.add_image(request, 7)
        return fig, ax

    def gen_map(self, df):
        """
        Uses its own daily dataframe to generate a map
        """
        scatter = self.ax.scatter(
            df.Longitude,
            df.Latitude,
            s=df.Result * self.marker_scalar,
            alpha=0.8,
            c=df.color,
            label=df.Result,
            transform=ccrs.PlateCarree(),
        )

        # Dynamically update legend
        legend_elements = []
        for camp, data in df.iterrows():
            legend_elements.append(
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color=self.cmap[data.camp],
                    label=f"{data.camp.replace('_',' ')}: {round(data.Result):,}",
                    markerfacecolor=self.cmap[data.camp],
                    markersize=15,
                    linestyle="None",
                )
            )

        # Add a text annotation for date
        date = pd.to_datetime(df.Date.unique()[0])
        text = AnchoredText(f"{date.strftime('%b %d, %Y')}", loc=1, prop={"size": 22})
        self.ax.add_artist(text)

        # Add Title
        text = AnchoredText(
            f"Flee Model Results: {self.scenario}", loc="upper left", prop={"size": 22}
        )
        self.ax.add_artist(text)

        legend1 = self.ax.legend(
            title="Total Refugees",
            handles=legend_elements,
            loc="lower right",
            labelspacing=1.5,
            borderpad=1.5,
        )
        legend1.set_title("Total Refugees", prop={"size": 15})
        self.ax.add_artist(legend1)

        self.fig.tight_layout(pad=2.5)

        # triple 0 pad the frame number
        self.fig.savefig(f"frames/frame_{str(self.count).zfill(3)}.png", dpi=100)

        # remove figures but keep background
        scatter.remove()
        while len(self.ax.artists) > 0:
            for art in self.ax.artists:
                art.remove()
        return

    def create_movie(self):
        if os.path.exists("frames") and os.path.isdir("frames"):
            shutil.rmtree("frames")
            os.mkdir("frames")
        else:
            os.mkdir("frames")

        self.count = 1
        for d in self.df.Date.unique():
            df_ = self.df[self.df["Date"] == d]
            self.gen_map(df_)
            self.count += 1
            if self.count % 10 == 0:
                print(f"Completed plotting for days through {self.count}.")

        import subprocess

        try:
            cmd = "ffmpeg -start_number 1 -r 4 -i frames/frame_%03d.png -c:v h264 -r 30 -s 1920x1080 -vcodec libx264 -s 1920x1080 -pix_fmt yuv420p run/media/flee_movie.mp4 -y"
            subprocess.run([cmd], shell=True, check=True)
        except subprocess.CalledProcessError:
            print(
                f"{FAIL}ERROR: FFmpeg does not exist, please install it to create the movie.{ENDC}"
            )

        shutil.rmtree("frames")
        return
