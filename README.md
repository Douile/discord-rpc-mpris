# Discord RPC - MPRIS

<p align="center"><img alt="Example image" src="img/example.png"></p>

> A Discord Rich Presence client that connects to MPRIS music players

This is a super simple RPC client that connects to any MPRIS music player and shows your current song, as well as a nifty little image. Forked from [rayzr](https://github.com/RayzrDev/discord-rpc-mpris)

## Installation

This project requires Python to be installed, and is only functional on Unix operating systems due to the nature of MPRIS.

1. Clone this repository:

```bash
git clone https://github.com/Douile/discord-rpc-mpris.git
cd discord-rpc-mpris
```

2. Install the requirements:

PyGObject is in official repos of some repos, if you have it install it with something like
```bash
sudo pacman -S python-gobject
```
or if not uncomment the line PythonGObject (remove #) and run the continue to next command

```bash
pip install -r requirements.txt
```

## Usage

Just `cd` into the `dicord-rpc-mpris` folder and run the following:

```bash
./discord-rpc-mpris
```

The client will connect to your account.

