import os, sys, time, subprocess, signal
from gi.repository import Gio, GLib
OUT = sys.argv[1]; APPS = sys.argv[2].split(",") if len(sys.argv) > 2 else []
os.makedirs(OUT, exist_ok=True)
rt = os.environ["XDG_RUNTIME_DIR"]; disp = "wayland-fluent"
env = dict(os.environ); env.pop("WAYLAND_DISPLAY", None); env["XDG_SESSION_TYPE"] = "wayland"
shell = subprocess.Popen(["gnome-shell", "--headless", "--wayland", f"--wayland-display={disp}", "--virtual-monitor", "1600x900"],
                         env=env, stdout=open(OUT + "/shell.log", "w"), stderr=subprocess.STDOUT)
bus = Gio.bus_get_sync(Gio.BusType.SESSION)
def owned(n):
    return bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "NameHasOwner",
                         GLib.Variant("(s)", (n,)), None, Gio.DBusCallFlags.NONE, -1).unpack()[0]
for _ in range(60):
    if os.path.exists(f"{rt}/{disp}") and owned("org.gnome.Mutter.ScreenCast"): break
    time.sleep(0.5)
else:
    print("shell não subiu"); shell.kill(); sys.exit(1)
time.sleep(4)
aenv = dict(env); aenv.update({k.replace("APPENV_",""):v for k,v in os.environ.items() if k.startswith("APPENV_")}); aenv["WAYLAND_DISPLAY"] = disp; aenv["GDK_BACKEND"] = "wayland"
if os.environ.get("APP_XDG_CONFIG"): aenv["XDG_CONFIG_HOME"] = os.environ["APP_XDG_CONFIG"]; aenv.pop("GTK_THEME", None)
procs = [subprocess.Popen(a.split(), env=aenv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for a in APPS]
time.sleep(7)
def call(dest, path, iface, method, args=None, sig=None):
    return bus.call_sync(dest, path, iface, method, GLib.Variant(sig, args) if sig else None, None, Gio.DBusCallFlags.NONE, -1)
cfg = call("org.gnome.Mutter.DisplayConfig", "/org/gnome/Mutter/DisplayConfig", "org.gnome.Mutter.DisplayConfig", "GetCurrentState").unpack()
connector = cfg[1][0][0][0]
sess = call("org.gnome.Mutter.ScreenCast", "/org/gnome/Mutter/ScreenCast", "org.gnome.Mutter.ScreenCast", "CreateSession", ({},), "(a{sv})").unpack()[0]
stream = call("org.gnome.Mutter.ScreenCast", sess, "org.gnome.Mutter.ScreenCast.Session", "RecordMonitor", (connector, {}), "(sa{sv})").unpack()[0]
node = {}
loop = GLib.MainLoop()
def added(c, s, p, i, sig, params):
    node["id"] = params.unpack()[0]; loop.quit()
bus.signal_subscribe("org.gnome.Mutter.ScreenCast", "org.gnome.Mutter.ScreenCast.Stream", "PipeWireStreamAdded", stream, None, Gio.DBusSignalFlags.NONE, added)
call("org.gnome.Mutter.ScreenCast", sess, "org.gnome.Mutter.ScreenCast.Session", "Start")
GLib.timeout_add_seconds(15, loop.quit); loop.run()
print("node", node)
if "id" in node:
    r = subprocess.run(["gst-launch-1.0", "-q", "pipewiresrc", f"path={node['id']}", "num-buffers=5", "!", "videoconvert", "!", "pngenc", "snapshot=true", "!", "filesink", f"location={OUT}/shot.png"],
                       capture_output=True, text=True, timeout=40)
    print(r.returncode, r.stderr[-300:])
for p in procs: p.terminate()
shell.terminate()
