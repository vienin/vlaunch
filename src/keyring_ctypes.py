from ctypes import *
import glob
import ctypes

glib=cdll.LoadLibrary(glob.glob("/usr/lib/libglib-2*.so*")[0])
glib.g_set_application_name("UFO")

keyring=cdll.LoadLibrary(glob.glob("/usr/lib/libgnome-keyring*.so*")[0])
keyring.gnome_keyring_find_network_password_sync.argtypes = \
    [ c_char_p, c_char_p,
      c_char_p, c_char_p,
      c_char_p, c_char_p,
      c_int, c_void_p ]
keyring.gnome_keyring_set_network_password_sync.argtypes = \
    [ c_char_p, c_char_p,
      c_char_p, c_char_p,
      c_char_p, c_char_p,
      c_char_p, c_int,
      c_char_p, POINTER(c_int) ]
    
class GnomeKeyringNetworkPasswordData(Structure):
  _fields_ = [("keyring", c_char_p),
              ("item_id", c_int),
              ("protocol", c_char_p),
              ("server", c_char_p),
              ("object", c_char_p),
              ("authtyp", c_char_p),
              ("port", c_int),
              ("user", c_char_p),
              ("domain", c_char_p),
              ("password", c_char_p) ]

glib.g_list_nth_data.restype = POINTER(GnomeKeyringNetworkPasswordData)

def get_password(domain, key):
    glist = c_void_p()
    keyring.gnome_keyring_find_network_password_sync(key, domain, None, None, None, None, 0, byref(glist))

    item = glib.g_list_nth_data(glist, 0)
    if item:
        return item.contents.password
    else:
        return ""

def set_password(domain, key, password):
    keyring.gnome_keyring_set_network_password_sync(
        None, key, domain, None,
        None, None, None, 0, password, byref(c_int()))

if __name__ == "__main__":
    print "Get password", get_password("UFO", "password")
    set_password("UFO", "password", "password")
    app = keyring.gnome_keyring_application_ref_new()
    control = keyring.gnome_keyring_access_control_new(app, 1)
    keyring.gnome_keyring_item_ac_set_path_name(control, "/tmp/toto")
    keyring.gnome_keyring_item_ac_set_access_type(control, 1)
