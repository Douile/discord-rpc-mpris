#!/usr/bin/env python3
"""
A simple Discord Rich Presence client that connects to MPRIS and shows your current song.
"""

import sys
import time
import base64

import gi
gi.require_version('Playerctl', '2.0')
from gi.repository import Playerctl, GLib
from pypresence import Presence
import pypresence.exceptions
import requests

manager = Playerctl.PlayerManager()
IPFS_API = "http://192.168.20.8:5001/api/v0"

print("Starting RPC client...")
RPC = Presence('440997014315204609')

def get_time():
    return time.time()*1000             # Get current timestamp (s)
last_switch = get_time()
last_image = None
last_image_link = "music"
last_track = None

def upload_ipfs(file):
    r = requests.post(IPFS_API+"/files/write?arg=/album-art.png&create=true",
            files={"file": open(file, "rb")})
    r.raise_for_status()
    r = requests.post(IPFS_API+"/files/stat?arg=/album-art.png")
    r.raise_for_status()
    return "https://ipfs.io/ipfs/"+r.json()["Hash"]

def remove_ipfs():
    r = requests.post(IPFS_API+"/files/rm?arg=/album-art.png")
    r.raise_for_status()

def connect_rpc():
    while True:
        try:
            RPC.connect()
            print("RPC client connected")
            break
        except ConnectionRefusedError as e:
            print("Failed to connect to RPC! Trying again in 10 seconds...")
            time.sleep(10)
        except (FileNotFoundError, AttributeError) as e:
            print("RPC failed to connect due to Discord not being opened yet. Please open it. Reconnecting in 10 seconds...")
            time.sleep(10)

def setup_player(name):
    player = Playerctl.Player.new_from_name(name)
    player.connect('playback-status::playing', on_play, manager)
    player.connect('playback-status::paused', on_pause, manager)
    player.connect('metadata', on_metadata, manager)
    player.connect('seeked', on_seeked, manager)
    manager.manage_player(player)
    update(player)

def get_song(player):
    return "%s - %s" % (player.get_title(), player.get_artist())

def get_buttons(player):
    track_id = str(player.print_metadata_prop("mpris:trackid"))
    if track_id.startswith("spotify:track:"):
        return [{
                "label": "Listen on spotify",
                "url": "https://open.spotify.com/track/{}".format(track_id[13:]),
            }]
    if track_id.startswith("/dev/alextren/Spot/Track/"):
        return [{
                "label": "Listen on spotify",
                "url": "https://open.spotify.co/track/{}".format(track_id[25:]),
            }]
    return None

def get_timestamps(player):
    now = get_time()
    # Get length of song (us)
    try:
        length = int(player.print_metadata_prop('mpris:length'))/1000
    except TypeError as e:
        length = None
    try:
        pos = player.get_position()/1000    # Get position (us)
    except gi.repository.GLib.Error as e:
        pos = None
    if pos is not None and length is not None:
        start = now-pos
        return (start, start+length)
    global last_switch, last_track
    cur_title = player.get_title()
    if cur_title != last_track:
        last_track = cur_title
        last_switch = now
    return (last_switch, None)

def get_image(player):
    art_url = str(player.print_metadata_prop("mpris:artUrl"))
    if art_url.startswith("https://") or art_url.startswith("http://"):
        return art_url
    global last_image, last_image_url
    if art_url.startswith("data:"):
        if last_image == art_url:
            return last_image_url
        last_image = art_url
        data_index = art_url.index(",")
        mime, data_type = art_url[5:data_index].split(";")
        data = art_url[data_index+1:]
        if data_type == "base64":
            data = base64.b64decode(data)
        with open("/tmp/album-art.png", "wb") as file:
            file.write(data)
        last_image_url = upload_ipfs("/tmp/album-art.png")
        return last_image_url
    if art_url.startswith("file://"):
        if last_image == art_url:
            return last_image_url
        last_image_url = upload_ipfs(art_url[7:])
        last_image = art_url
        return last_image_url
    return "music"

def update(player):
    status = player.get_property('status')
    try:
        if status == "":
            RPC.clear()
        elif status == "Playing":
            start, end = get_timestamps(player)
            artist = player.get_artist()
            if len(artist) == 0:
                artist = "No artist"
            RPC.update(
                details=player.get_title(),
                state=artist,
                large_image=get_image(player),
                large_text=get_song(player),
                small_image='play',
                start=start,
                end=end,
                buttons=get_buttons(player),
            )
        elif status == "Paused":
            RPC.update(state='Paused', large_image='music', small_image='pause')
    except pypresence.exceptions.InvalidID:
        print("Lost connection to Discord RPC! Attempting reconnection...")
        connect_rpc()

def on_play(player, status, manager):
    update(player)

def on_pause(player, status, manager):
    update(player)

def on_metadata(player, metadata, manager):
    update(player)

def on_seeked(player, pos, manager):
    update(player)

def on_player_add(manager, name):
    setup_player(name)

def on_player_remove(manager, player):
    if len(manager.props.players) < 1:
        try:
            RPC.clear()
        except pypresence.exceptions.InvalidID:
            if e == "Client ID is Invalid":
                print("Lost connection to Discord RPC! Attempting reconnection...")
                connect_rpc()
            else:
                raise
    else:
        update(manager.props.players[0])

def start():
    manager.connect('name-appeared', on_player_add)
    manager.connect('player-vanished', on_player_remove)

    # Start program, connect to Discord, setup existing players & hook into GLib's main loop
    connect_rpc()

    for name in manager.props.player_names:
        setup_player(name)

    GLib.MainLoop().run()

if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        print("Shutting down...")
        RPC.clear()
        RPC.close()
        remove_ipfs()

