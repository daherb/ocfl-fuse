import os
from ocfl import Store
import re
import shutil
from ocfl.dispositor import Dispositor

class OCFLException(Exception):
    def __init__(self,msg):
        super().__init__(msg)
        
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
        # Dictionary to keep track of staging objects
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
            os.mkdir(staging_object)
            # Copy files
            object_path=self.store.object_path(id);
            shutil.copytree(object_path,staging_object)
            # Add to list of staged objects
            self.staging_objects[id] = normalized_id
        
    # Commit an object creating a new cersion
    def commit_object(self,id):
        return 0
    
    # Revert a staged object
    def revert_object(self,id):
        # Just remove the complete folder from staging
        shutil.rmtree(get_staging_object_path(id))
        return 0    
