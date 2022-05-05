import os
from ocfl import Store
import re
import shutil
import json
from ocfl.dispositor import Dispositor

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
    def new_object(self,id):
        # Get a normalized id, i.e. without problematic special characters
        normalized_id = self.encode_id(id)
        # Check if object already exists, either in store ...
        if id in list_objects():
               raise OCFLException("Object already exists in store")
        # ... or in staging
        staging_object = os.path.join(self.staging_dir,normalized_id)
        if os.path.exists(staging_object):
               raise OCFLException("Object already exists in staging")
        # Create folder in staging area
        os.mkdir(staging_object)
        self.staging_objects[id] = normalized_id

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
            # Create folder
            if not os.path.exists(staging_object):
                os.mkdir(staging_object)
            # Copy files
            object_path=self.get_object_path(id)
            object_inventory=self.get_object_inventory(id)
            #object_head_content=os.path.join(os.path.join(object_path,object_inventory['head']),"content")
            #print("Copytree from " + object_head_content + " to " + staging_object)
            #shutil.copytree(object_head_content,staging_object)
            current_version=object_inventory['head']
            for hash in object_inventory['versions'][current_version]['state']:
                src_file = os.path.join(object_path,object_inventory['manifest'][hash][0])
                tgt_file = os.path.join(staging_object,object_inventory['versions'][current_version]['state'][hash][0])
                # Split target into path and file name
                split_tgt = os.path.split(tgt_file)
                # If the path doesn't exist create it
                if not os.path.exists(split_tgt[0]):
                    os.mkdir(split_tgt[0])
                shutil.copy(src_file,tgt_file)
            # Add to list of staged objects
            self.staging_objects[id] = normalized_id

    # Commit an object creating a new version
    def commit_object(self,id):
        return 0
    
    # Revert a staged object
    def revert_object(self,id):
        # Check if the object is actually staged
        if id in self.staging_objects:
            # Just remove the complete folder from staging
            shutil.rmtree(self.get_staging_object_path(id))
        return 0
