import os
from typing import Any

from UGConnProfile import *


class UGUserProfile:
    """ User Profile that stores all opened session and user settings
    >>> user_profile = UGUserProfile()
    >>> # this class is a singleton
    >>> UGUserProfile()
    Traceback (most recent call last):
        ...
    ValueError: class UGUserProfile has been instantiated. Misuse of constructor.
    >>> user_profile["version"]
    1
    >>> user_profile.add_new_session("EECG1","UG")
    Traceback (most recent call last):
        ...
    ValueError: UGUserProfile: add_new_session: Invalid conn_profile=UG
    >>> user_profile.add_new_session("EECG1","eecg")
    >>> user_profile.modify_session(1,"liaojunh", "")
    Traceback (most recent call last):
        ...
    IndexError: UGUserProfile: modify_session: Invalid session_idx=1
    >>> user_profile.modify_session(0, "liaojunh", "non-existing-server")
    Traceback (most recent call last):
        ...
    ValueError: UGUserProfile: modify_session: Invalid last_server=non-existing-server
    >>> user_profile.modify_session(0, "liaojunh", "ug250.eecg.toronto.edu", private_key_path="../profile/id_rsa",
    ...     vnc_passwd_path="../profile/passwd")
    >>> user_profile["sessions"][0]
    {'name': 'EECG1', 'conn_profile': 'eecg', 'last_server': 'ug250.eecg.toronto.edu', 'username': 'liaojunh', \
'private_key_path': '../profile/id_rsa', 'vnc_passwd_path': '../profile/passwd'}
    >>> user_profile.add_new_session("ECF1","ecf")
    >>> user_profile.modify_session(1, "liaojunh", "remote.ecf.utoronto.ca")
    >>> user_profile["sessions"][1]
    {'name': 'ECF1', 'conn_profile': 'ecf', 'last_server': 'remote.ecf.utoronto.ca', 'username': 'liaojunh', \
'private_key_path': '', 'vnc_passwd_path': ''}
    >>> user_profile.save_profile("../profile/user_profile.json")
    >>> user_profile.load_profile("non_existing_path") # the profile should be reset after this call
    UGUserProfile loading...
    UGUserProfile: load_profile: [Errno 2] No such file or directory: 'non_existing_path'
    Unable to load the user profile. Using the default profile instead.
    >>> user_profile["non-existing-key"]
    Traceback (most recent call last):
        ...
    KeyError: 'non-existing-key'
    >>> user_profile["viewer"]
    'TigerVNC'
    >>> user_profile.change_viewer("non-existing-viewer")
    Traceback (most recent call last):
        ...
    NotImplementedError: UGUserProfile: change_viewer: non-existing-viewer not supported.
    >>> user_profile.change_viewer("RealVNC")
    >>> user_profile["viewer"]
    'RealVNC'
    >>> user_profile["last_session"]
    -1
    >>> user_profile["sessions"]
    []
    >>> user_profile.load_profile("../profile/user_profile.json")
    UGUserProfile loading...
    >>> user_profile["viewer"]
    'TigerVNC'
    >>> user_profile["last_session"]
    1
    >>> user_profile["sessions"]
    [{'name': 'EECG1', 'conn_profile': 'eecg', 'last_server': 'ug250.eecg.toronto.edu', 'username': 'liaojunh', \
'private_key_path': '../profile/id_rsa', 'vnc_passwd_path': '../profile/passwd'}, \
{'name': 'ECF1', 'conn_profile': 'ecf', 'last_server': 'remote.ecf.utoronto.ca', 'username': 'liaojunh', \
'private_key_path': '', 'vnc_passwd_path': ''}]
    >>> user_profile.query_sessions() # doctest:+ELLIPSIS
    [{'name': 'EECG1', 'servers': ['ug51.eecg.toronto.edu', ..., 'ug251.eecg.toronto.edu'], \
'last_server': 'ug250.eecg.toronto.edu', 'username': 'liaojunh', 'passwd': True, 'vnc_manual': True, \
'vnc_passwd': True}, {'name': 'ECF1', 'servers': ['remote.ecf.utoronto.ca', ...], \
'last_server': 'remote.ecf.utoronto.ca', 'username': 'liaojunh', 'passwd': False, 'vnc_manual': False, \
'vnc_passwd': False}]
    """
    # TODO: may think again: all the sessions should support indexing by names
    #  therefore self["session"] can be a dictionary instead
    version = 1  # in case the schema changes in the future
    instantiated = False

    _supported_viewers = ["TigerVNC", "RealVNC"]

    _empty_session = {
        "name": "",
        "conn_profile": "",
        "last_server": "",
        "username": "",
        "private_key_path": "",
        "vnc_passwd_path": ""
    }

    _empty_user_profile = {
        "version": version,
        "viewer": "TigerVNC",
        "last_session": -1,
        "sessions": []
    }

    def __new__(cls, *args, **kwargs):
        # to prevent misuse of the class
        if cls.instantiated:
            raise ValueError("class %s has been instantiated. Misuse of constructor." % cls.__name__)

        return super(UGUserProfile, cls).__new__(cls, *args, **kwargs)

    def __init__(self):
        self._profile = copy.deepcopy(UGUserProfile._empty_user_profile)

        self._conn_profiles = {}
        for file_name in os.listdir("../profile"):
            if file_name.endswith(".json"):
                conn_profile = UGConnProfile()
                conn_profile.load_profile("../profile/" + file_name)
                self._conn_profiles[file_name[:-5]] = conn_profile

        UGUserProfile.instantiated = True

    def __setitem__(self, key, value):
        self._profile[key] = value

    def __getitem__(self, key):
        return self._profile[key]

    def load_session(self, session):
        """
         _empty_session = {
            "name": "",
            "conn_profile": "",
            "last_server": "",
            "username": "",
            "private_key_path": "",
            "vnc_passwd_path": ""
        }
        """
        loaded_session = copy.deepcopy(UGUserProfile._empty_session)

        # load user profile name
        # TODO: check for duplicated names
        loaded_session["name"] = session["name"]

        # load the connection profile
        # TODO: recheck whether we should handle this gracefully
        loaded_session["conn_profile"] = session["conn_profile"]
        conn_profile = self._conn_profiles[session["conn_profile"]]

        # load the last used server
        # TODO: recheck whether we should handle this gracefully
        if session["last_server"] not in conn_profile["servers"]:
            loaded_session["last_server"] = ""
        else:
            loaded_session["last_server"] = session["last_server"]

        # load the username
        loaded_session["username"] = session["username"]

        # load the SSH private key path
        if not os.path.exists(session["private_key_path"]):
            # TODO: recheck whether we should handle this gracefully
            # raise FileNotFoundError(f"UGUserProfile: Unable to find private_key_path="
            #                         f"{session['private_key_path']}")
            loaded_session["private_key_path"] = ""
        else:
            loaded_session["private_key_path"] = session["private_key_path"]

            # load the VNC passwd file path
            if not os.path.exists(session["vnc_passwd_path"]):
                # TODO: recheck whether we should handle this gracefully
                # raise FileNotFoundError(f"UGUserProfile: Unable to find vnc_passwd_path="
                #                         f"{session['vnc_passwd_path']}")
                loaded_session["vnc_passwd_path"] = ""
            else:
                loaded_session["vnc_passwd_path"] = session["vnc_passwd_path"]
        return loaded_session

    def load_profile(self, file_path):
        print("UGUserProfile loading...")
        self._profile = copy.deepcopy(UGUserProfile._empty_user_profile)
        # self.eecg_vnc_passwd_exist = os.path.exists(VNC_PASSWD_PATH)

        try:
            with open(file_path, "r") as infile:
                json_data = json.load(infile)

                # TODO: might attempt profile recovery even if some of the parameters are incorrect
                # if the version doesn't match then stop loading
                if "version" not in json_data or json_data["version"] != UGUserProfile.version:
                    raise ValueError("UGUserProfile: Version info not found or mismatch in the profile.")

                # make sure the profile file is not modified in an attempt to crash the script
                if json_data["viewer"] not in UGUserProfile._supported_viewers:
                    raise ValueError(f"UGUserProfile: Viewer {json_data['viewer']} not supported.")
                self["viewer"] = json_data["viewer"]

                if json_data["last_session"] < 0 or json_data["last_session"] >= len(json_data["sessions"]):
                    raise ValueError(f"UGUserProfile: Invalid last_session={json_data['last_session']}")
                self["last_session"] = json_data["last_session"]

                for session in json_data["sessions"]:
                    # TODO: should definitely attempt recovery here
                    loaded_session = self.load_session(session)
                    self["sessions"].append(loaded_session)

        except Exception as e:
            self._profile = copy.deepcopy(UGUserProfile._empty_user_profile)
            print("UGUserProfile: load_profile:", e)
            # raise e
            # TODO: print the profile path for debugging
            print("Unable to load the user profile. Using the default profile instead.")

    def add_new_session(self, name, conn_profile):
        # TODO: should support renaming the sessions later
        """
         _empty_session = {
            "name": "",
            "conn_profile": "",
            "last_server": "",
            "username": "",
            "private_key_path": "",
            "vnc_passwd_path": ""
        }
        """
        new_session = copy.deepcopy(UGUserProfile._empty_session)
        # TODO: check for duplicated session names
        new_session["name"] = name

        if conn_profile not in self._conn_profiles:
            raise ValueError(f"UGUserProfile: add_new_session: Invalid conn_profile={conn_profile}")
        new_session["conn_profile"] = conn_profile

        self["sessions"].append(new_session)

    # TODO: support removing a session

    def modify_session(self, session_idx, username, last_server, private_key_path=None, vnc_passwd_path=None):
        if session_idx < 0 or session_idx >= len(self["sessions"]):
            raise IndexError(f"UGUserProfile: modify_session: Invalid session_idx={session_idx}")

        # TODO: check whether we should have a dedicated function to update the last session
        self["last_session"] = session_idx

        session: Any = self["sessions"][session_idx]
        session["username"] = username

        if last_server not in self._conn_profiles[session["conn_profile"]]["servers"]:
            raise ValueError(f"UGUserProfile: modify_session: Invalid last_server={last_server}")
        session["last_server"] = last_server

        # the private key should be optional
        if private_key_path is not None:
            # TODO: check whether the private_key_path is valid
            session["private_key_path"] = private_key_path

        # the vnc_passwd_path key should be optional
        if vnc_passwd_path is not None:
            # TODO: check whether the conn_profile supports vnc_manual
            # TODO: check whether the vnc_passwd_path is valid
            session["vnc_passwd_path"] = vnc_passwd_path

    def change_viewer(self, viewer):
        if viewer not in UGUserProfile._supported_viewers:
            raise NotImplementedError(f"UGUserProfile: change_viewer: {viewer} not supported.")
        self["viewer"] = viewer

    def save_profile(self, file_path):
        try:
            with open(file_path, 'w') as outfile:
                json_data = json.dumps(self._profile, indent=4)
                outfile.write(json_data)
        except Exception:
            # need to handle any write permission issues, once observed
            raise Exception

    def query_sessions(self):
        """
        {
            “name”: “EECG1”,
            “servers”:[
                “ug250.eecg.toronto.edu”,
                “ug251.eecg.toronto.edu”,
                ...
            ],
            “last_server”:  “ug250.eecg.toronto.edu”,
            “username”:””,
            “passwd”:false,
            “vnc_manual”: true,
            “vnc_passwd”: false
        }
        """
        queried_sessions_list = []
        for session in self["sessions"]:
            session: Dict
            queried_session = {
                "name": session["name"],
                "servers": self._conn_profiles[session["conn_profile"]]["servers"],
                "last_server": session["last_server"],
                "username": session["username"],
                "passwd": (session["private_key_path"] != ""),
                "vnc_manual": self._conn_profiles[session["conn_profile"]]["vnc_manual"],
                "vnc_passwd": (session["vnc_passwd_path"] != "")
            }
            queried_sessions_list.append(queried_session)

        return queried_sessions_list
