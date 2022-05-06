#    Copyright (C) 2022  Herbert Lange <lange@ids-mannheim.de>
#
# Wrapper module to implement basic transcations for an OCFL store
#

import os
from ocfl import Store
from ocfl import Object
from ocfl import VersionMetadata
from ocfl.dispositor import Dispositor
import re
import shutil
import json
import datetime
import logging

# Custom exception for OCFL-related problems
class OCFLException(Exception):
    def __init__(self,msg):
        super().__init__(msg)

# Wrapper class around the ocfl reference implementation to add basic transactions
class OCFLPY():

    # Quote special characters
    def encode_id(self,id):
        return self.dispositor.encode(id)

    # Quote special characters
    def decode_id(self,id):
        return self.dispositor.decode(id)

    def __init__(self,root,staging_dir,disposition):
        # The store root
        self.root = root
        # Load the store
        self.store = Store(root,disposition=disposition)
        # Initialize if the root does not exist
        if not os.path.exists(root):
            self.store.initialize()
        # The staging dir
        self.staging_dir = staging_dir
        # create if missing
        if not(os.path.exists(staging_dir)):
               os.mkdir(staging_dir)
        # Keep track of staging objects
        self.staging_objects = {}
        # Local dispositor to access the methods
        self.dispositor=Dispositor()

    # Returns the list of all object ids
    def list_object_ids(self):
        # Get the list from the store
        return [o["id"] for o in self.store.list()]

    # Returns the list of all objects
    def list_objects(self):
        # Get the list from the store
        return self.store.list()

    # Returns the path of the staging version of an object
    def get_staging_object_path(self,id):
        return os.path.join(self.staging_dir,self.staging_objects[id])

    # Get the path for an object id
    def get_object_path(self,id):
        return os.path.join(self.root,self.store.object_path(id));

    # Get the inventory for an object id
    def get_object_inventory(self,id):
        return json.load(open(os.path.join(self.get_object_path(id),"inventory.json"),"r"))

    # List the files in the most recent version of an object given by its id
    def list_object_files(self,id):
        inventory=self.get_object_inventory(id)
        version_state=inventory['versions'][inventory['head']]['state']
        file_list=[]
        for hash in version_state.keys():
            file_list=file_list+version_state[hash]
        return file_list

    # Creates a new object, i.e. a new folder in staging
    def create_object(self,id):
        # Get a normalized id, i.e. without problematic special characters
        normalized_id = self.encode_id(id)
        self.staging_objects[id] = normalized_id
        os.mkdir(self.get_staging_object_path(id))
        new_object = Object(identifier=id,path=self.get_staging_object_path(id))
        return 0
    #     # Get a normalized id, i.e. without problematic special characters
    #     normalized_id = self.encode_id(id)
    #     # Check if object already exists, either in store ...
    #     if id in list_objects():
    #            raise OCFLException("Object already exists in store")
    #     # ... or in staging
    #     staging_object = os.path.join(self.staging_dir,normalized_id)
    #     if os.path.exists(staging_object):
    #            raise OCFLException("Object already exists in staging")
    #     # Create folder in staging area
    #     os.mkdir(staging_object)
    #     self.staging_objects[id] = normalized_id

    # Opens an existing object from the store and makes it available in staging
    def open_object(self,id):
        # Check if object id is in store
        if not(id in self.list_object_ids()):
            raise OCFLException("Object not in store " + id)
        # Get a normalized id, i.e. without problematic special characters
        normalized_id = self.encode_id(id)
        # Check if object is already in staging
        staging_object = os.path.join(self.staging_dir,normalized_id)
        if not(id in self.staging_objects.keys()) and os.path.exists(staging_object):
               raise OCFLException("Object folder already exists in staging")
        else:
            # Extract files
            object_path=self.get_object_path(id)
            object_inventory=self.get_object_inventory(id)
            current_version=object_inventory['head']
            current_object = Object(path=object_path)
            current_object.extract(object_path,current_version,staging_object)
            # Convert stored creation time and remove the timezone Z marking UTC
            creation_time = datetime.datetime.fromisoformat(object_inventory['versions'][current_version]['created'].replace("Z","")).timestamp()
            # Update mtime
            for root, dirs, files in os.walk(staging_object):
                for f in dirs + files:
                    file_name = os.path.join(root,f)
                    stat = os.stat(file_name)
                    os.utime(file_name, times=(stat.st_atime, creation_time))
            # Add to list of staged objects            
            self.staging_objects[id] = normalized_id

    # Commit an object creating a new version
    def commit_object(self,id):
        logging.info("OCFL COMMIT: " + id)
        src_dir = self.get_staging_object_path(id)
        # Create object from staging
        object = Object(identifier=id)
        # Check if the ID is already in the store and create a new object if it is not yet in the store
        if id not in self.list_object_ids():
            # Convert the files in src_dir into an OCFL object in new_object
            new_object = src_dir + "_obj"
            username = os.getlogin()
            hostname = os.uname()[1] # Probably problematic on windows
            creation_time = datetime.datetime.utcnow().isoformat()+"Z"
            metadata = VersionMetadata(created=creation_time,name=username,address=username + "@" + hostname, message="Created object " + id)
            object.create(src_dir,metadata=metadata,objdir=new_object)
            # Add the new object 
            self.store.add(new_object)
            shutil.rmtree(new_object)
        # Update an object that is already in the store
        else:
            stored_object = self.store.object_path(id)
            # Update object in store
            object.update(stored_object,src_dir)
        return 0
    
    # Revert a staged object
    def revert_object(self,id):
        # Check if the object is actually staged
        if id in self.staging_objects:
            # Just remove the complete folder from staging
            shutil.rmtree(self.get_staging_object_path(id))
            # Also remove the ide from staging objects
            self.staging_objects.pop(id)
        return 0
