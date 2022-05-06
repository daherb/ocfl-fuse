#!/usr/bin/env python

#    Based on hello world example by:
#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    Almost completely rewritten by:
#    Copyright (C) 2022  Herbert Lange <lange@ids-mannheim.de>
#

import os, stat, errno
import fuse
from fuse import Fuse
from ocfl_wrapper import OCFLPY
import shutil
import logging

if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")

fuse.fuse_python_api = (0, 2)

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class OCFLFS(Fuse):

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.root = "."
        # The main folder
        self.object_path = "/objects"
        # Keep track of the current project id
        self.current_object_id = ""
        self.new_objects = []

    # FUSE methods
    
    # int(* 	getattr )(const char *, struct stat *, struct fuse_file_info *fi)
    def getattr(self, path):
        logging.info("GETATTR: " + path)
        st = MyStat()
        # Split the path
        split_path=os.path.split(path)
        # Root of our OCFL store
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        # The object path
        elif path == self.object_path:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        # Path of a staged object
        elif split_path[0] == self.object_path and self.ocflpy.decode_id(split_path[1]) in self.ocflpy.list_object_ids() + self.new_objects:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        # Folders in the current object
        elif self.is_staged_object_dir(path):
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
            st.st_size = os.path.getsize(self.get_staged_object_path(path))
            st.st_mtime= os.path.getmtime(self.get_staged_object_path(path))
        # Files in the current object
        elif self.is_staged_object_file(path):
            st.st_mode = stat.S_IFREG | 0o755
            st.st_nlink = 1
            st.st_size = os.path.getsize(self.get_staged_object_path(path))
            st.st_mtime= os.path.getmtime(self.get_staged_object_path(path))
        # Virtual file for commit
        elif path.endswith("commit"):
            st.st_mode = stat.S_IFREG | 0o755
            st.st_nlink = 1
            st.st_size = 255
            st.st_mtime = 0
        else:
            return -errno.ENOENT
        return st
    
    # # int(* 	readlink )(const char *, char *, size_t)
    # def readlink(self, path):
    #     logging.info("READLINK: " + path)
    #     return 0
    
    # # int(* 	mknod )(const char *, mode_t, dev_t)
    # def mknod(self, path, mode, dev):
    #     logging.info("MKNOD: " + path)
    #     return 0

    # int(* 	mkdir )(const char *, mode_t)
    def mkdir(self, path,mode):
        logging.info("MKDIR: " + path)
        # Not in object directory or any subdirectories
        if not path.startswith(self.object_path):
            return -errno.EROFS
        else:
            split_path = os.path.split(path)
            # New object
            if split_path[0] == self.object_path and split_path[1] != "":
                object_id=self.ocflpy.decode_id(split_path[1])
                self.new_objects.append(object_id)
                self.ocflpy.create_object(object_id)
            # New folder in staged object
            elif self.current_object_id != "" \
                 and self.is_staged_object_path(path) and \
                 not os.path.exists(self.get_staged_object_path(path)):
                os.mkdir(self.get_staged_object_path(path))
            else:
                return -errno.ENOENT
        return 0
    
    # int(* 	unlink )(const char *)
    def unlink(self, path):
        logging.info("UNLINK: " + path)
        split_path=os.path.split(path)
        if path.startswith(self.object_path) and split_path[0] != self.object_path:
            os.remove(self.get_staged_object_path(path))
        return 0
    
    # int(* 	rmdir )(const char *)
    def rmdir(self, path):
        logging.info("RMDIR: " + path)
        split_path=os.path.split(path)
        if path.startswith(self.object_path) and split_path[0] != self.object_path:
            os.removedirs(self.get_staged_object_path(path))
        return 0
    
    # # int(* 	symlink )(const char *, const char *)
    # def symlink(self, target, path):
    #     logging.info("SYMLINK: " + path)
    #     return 0
    
    # int(* 	rename )(const char *, const char *, unsigned int flags)
    def rename(self, oldpath, path):
        logging.info("RENAME: " + oldpath + " TO " + path + " BY RENAMING " + self.get_staged_object_path(oldpath) + " INTO " + self.get_staged_object_path(path))
        os.rename(self.get_staged_object_path(oldpath),self.get_staged_object_path(path))
        return 0
    
    # # int(* 	link )(const char *, const char *)
    # def link(self, oldpath, path):
    #     logging.info("LINK: " + path)
    #     return 0
    
    # int(* 	chmod )(const char *, mode_t, struct fuse_file_info *fi)
    def chmod(self, path, mode):
        logging.info("CHMOD: " + path)
        return 0
    
    # int(* 	chown )(const char *, uid_t, gid_t, struct fuse_file_info *fi)
    def chown(self, path, user, group):
        logging.info("CHOWN: " + path)
        return 0
    
    # int(* 	truncate )(const char *, off_t, struct fuse_file_info *fi)
    def truncate(self, path, length):
        logging.info("TRUNCATE: " + path)
        object_file_path=self.get_staged_object_path(path)
        f = open(object_file_path,'wb')
        f.truncate(length)
        f.close()
        return 0
    
    # int(* 	open )(const char *, struct fuse_file_info *)
    def open(self, path, flags):
        logging.info("OPEN: " + path)
        # Object path or 
        # One of the objects or
        # One of the folders in the current objects or
        # One of the files in the current object
        if path.endswith("/commit"):
            object_id=self.current_object_id
            self.ocflpy.commit_object(object_id)
            if object_id in self.new_objects:
                self.new_objects.remove(object_id)
            return 0
        elif path == self.object_path or \
            os.path.split(path)[0] == self.object_path or \
            self.is_staged_object_file(path) or \
            self.is_staged_object_dir(path):
            return 0
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    # int(* 	read )(const char *, char *, size_t, off_t, struct fuse_file_info *)
    def read(self, path, size, offset):
        logging.info("READ: " + path + " SIZE: " + str(size) + " OFFSET: " + str(offset))
        # Read one of the project files
        if self.is_staged_object_file(path):
            object_file_path=self.get_staged_object_path(path)
            f = open(object_file_path, 'rb')
            f.seek(offset)
            data = f.read(size)
            f.close()
            return data
        elif path.endswith("/commit"):
            return b'Committing object ' + bytes(self.current_object_id + "\n",'utf-8')
        return -errno.ENOENT
    
    # int(* 	write )(const char *, const char *, size_t, off_t, struct fuse_file_info *)
    def write(self, path, data, offset): # length):
        logging.info("WRITE: " + path)
        object_file_path=self.get_staged_object_path(path)
        f = open(object_file_path, 'wb')
        # f.seek(offset)
        len = f.write(data)
        f.close()
        return len
    
    # # int(* 	statfs )(const char *, struct statvfs *)
    # def statfs(self, path):
    #     logging.info("STATFS: " + path)
    #     return 0
    
    # int(* 	flush )(const char *, struct fuse_file_info *)
    def flush(self, path):
        logging.info("FLUSH: " + path)
        return 0
        
    # int(* 	release )(const char *, struct fuse_file_info *)
    def release(self, path,file_info):
        logging.info("RELEASE: " + path)
        return 0
    
    # # int(* 	fsync )(const char *, int, struct fuse_file_info *)
    # def fsync(self, path):
    #     logging.info("FSYNC: " + path)
    #     return 0
    
    # # int(* 	setxattr )(const char *, const char *, const char *, size_t, int)
    # def setxattr(self, path):
    #     logging.info("SETXATTR: " + path)
    #     return 0
    
    # # int(* 	getxattr )(const char *, const char *, char *, size_t)
    # def getxattr(self, path,x,y):
    #     logging.info("GETXATTR: " + path)
    #     return 0
    
    # # int(* 	listxattr )(const char *, char *, size_t)
    # def listxattr(self, path):
    #     logging.info("LISTXATTR: " + path)
    #     return 0
    
    # # int(* 	removexattr )(const char *, const char *)
    # def removexattr(self, path):
    #     logging.info("REMOVEXATTR: " + path)
    #     return 0
    
    # # int(* 	opendir )(const char *, struct fuse_file_info *)
    # def opendir(self, path):
    #     logging.info("OPENDIR: " + path)
    #     return 0
    
    # int(* 	readdir )(const char *, void *, fuse_fill_dir_t, off_t, struct fuse_file_info *, enum fuse_readdir_flags)
    def readdir(self, path, offset):
        logging.info("READDIR: " + path)
        for r in '.', '..':
            yield fuse.Direntry(r)
        # Root of our OCFL store
        if path == '/':
            for r in  [self.object_path[1:]]:
                yield fuse.Direntry(r)
        # The object list
        elif path == self.object_path:
            for oid in self.ocflpy.list_object_ids() + self.new_objects:
                normalized_id=self.ocflpy.encode_id(oid)
                yield fuse.Direntry(normalized_id)
        # Listing the content of an unstaged object
        elif path.startswith(self.object_path) and self.current_object_id == "":
            split_path=os.path.split(path)
            # get object id
            object_id=split_path[1]
            self.current_object_id=self.ocflpy.decode_id(object_id)
            # Virtual file to trigger commit
            yield fuse.Direntry("commit")
            for file in os.listdir(self.ocflpy.get_staging_object_path(self.current_object_id)):
                yield fuse.Direntry(file)
        # Listing the content of a staged object
        elif path == os.path.join(self.object_path,self.ocflpy.encode_id(self.current_object_id)):
            # Virtual file to trigger commit
            yield fuse.Direntry("commit")
            for file in os.listdir(self.ocflpy.get_staging_object_path(self.current_object_id)):
                yield fuse.Direntry(file)
        elif path.startswith(os.path.join(self.object_path,self.ocflpy.encode_id(self.current_object_id))):
            for file in os.listdir(self.get_staged_object_path(path)):
                yield fuse.Direntry(file)
                
    # # int(* 	releasedir )(const char *, struct fuse_file_info *)
    # def releasedir(self, path):
    #     logging.info("RELEASEDIR: " + path)
    #     return 0
    
    # # int(* 	fsyncdir )(const char *, int, struct fuse_file_info *)
    # def fsyncdir(self, path):
    #     logging.info("FSYNCDIR: " + path)
    #     return 0
    
    # void *(* 	init )(struct fuse_conn_info *conn, struct fuse_config *cfg)
    # void(* 	destroy )(void *private_data)
    # int(* 	access )(const char *, int)
    def access(self, path, x):
        logging.info("ACCESS: " + path)
        if path == self.object_path:
            # Revert if we change back into the object path
            if self.current_object_id != "":
                self.ocflpy.revert_object(self.current_object_id)
                if self.current_object_id in self.new_objects:
                    self.new_objects.remove(self.current_object_id)
                self.current_object_id = ""
        split_path=os.path.split(path)
        # We access an (unstaged) object
        if split_path[0] == self.object_path and split_path[1] != "":
            object_id=split_path[1]
            id=self.ocflpy.decode_id(object_id)
            # Stage unstaged object if necessary
            if self.current_object_id == "":
                if id in self.ocflpy.list_object_ids():
                    self.ocflpy.open_object(id)
                self.current_object_id=self.ocflpy.decode_id(object_id)
        return 0
    
    # int(* 	create )(const char *, mode_t, struct fuse_file_info *)
    def create(self, path, mode ,file_info):
        logging.info("CREATE: " + path + " - Mode: " + str(mode) + " - File Info: " + str(file_info))
        if self.current_object_id != "":
            logging.info("ADDING " + path)
            # Check if file exists and otherwise create it
            object_file_path=self.get_staged_object_path(path)
            if not os.path.exists(object_file_path):
                open(object_file_path,'wb').close()
        return 0
    
    # # int(* 	lock )(const char *, struct fuse_file_info *, int cmd, struct flock *)
    # #    def lock(self, cmd,owner,**kw):
    # def lock(self, path, cmd, owner, **kw):
    #     logging.info("LOCK: " + path)
    #     return 0
    
    # int(* 	utimens )(const char *, const struct timespec tv[2], struct fuse_file_info *fi)
    def utimens(self, path,timespec,file_info):
        logging.info("UTIMENS: " + path)
        return 0
    
    # # int(* 	bmap )(const char *, size_t blocksize, uint64_t *idx)
    # def bmap(self, path):
    #     logging.info("BMAP: " + path)
    #     return 0
    
    # # int(* 	ioctl )(const char *, unsigned int cmd, void *arg, struct fuse_file_info *, unsigned int flags, void *data)
    # def ioctl(self, path, cmd, arg, flags):
    #     logging.info("IOCTL: " + path)
    #     return 0
    
    # # int(* 	poll )(const char *, struct fuse_file_info *, struct fuse_pollhandle *ph, unsigned *reventsp)
    # def poll(self, path):
    #     logging.info("POLL: " + path)
    #     return 0
    
    # # int(* 	write_buf )(const char *, struct fuse_bufvec *buf, off_t off, struct fuse_file_info *)
    # def write_buf(self, path):
    #     logging.info("WRITE_BUF: " + path)
    #     return 0
    
    # # int(* 	read_buf )(const char *, struct fuse_bufvec **bufp, size_t size, off_t off, struct fuse_file_info *)
    # def read_buf(self, path):
    #     logging.info("READ_BUF: " + path)
    #     return 0
    
    # # int(* 	flock )(const char *, struct fuse_file_info *, int op)
    # def flock(self, path):
    #     logging.info("FLOCK: " + path)
    #     return 0
    
    # # int(* 	fallocate )(const char *, int, off_t, off_t, struct fuse_file_info *)
    # def fallocate(self, path):
    #     logging.info("FALLOCATE: " + path)
    #     return 0
    
    # # ssize_t(* 	copy_file_range )(const char *path_in, struct fuse_file_info *fi_in, off_t offset_in, const char *path_out, struct fuse_file_info *fi_out, off_t offset_out, size_t size, int flags)
    # # off_t(* 	lseek )(const char *, off_t off, int whence, struct fuse_file_info *)
    # def lseek(self, path):
    #     logging.info("LSEEK: " + path)
    #     return 0    

    # Helper functions

    # Gets the staging file name for an object file
    def get_staged_object_path(self,path):
        # Get the path of file in staging and read it
        oid=self.current_object_id
        file_path=path.replace(os.path.join(self.object_path,self.ocflpy.encode_id(oid)) + "/","")
        return os.path.join(self.ocflpy.get_staging_object_path(oid),file_path)
    
    # Checks if a path is to a staged file/directory
    def is_staged_object_path(self,path):
        oid=self.current_object_id
        return oid != "" and path.startswith(os.path.join(self.object_path,self.ocflpy.encode_id(oid)))

    # Check if a path is a staged file
    def is_staged_object_file(self,path):
        return self.is_staged_object_path(path) and os.path.isfile(self.get_staged_object_path(path))

    # Check if a path is a staged directory
    def is_staged_object_dir(self,path):
        return self.is_staged_object_path(path) and os.path.isdir(self.get_staged_object_path(path))

def main():
    usage="""
Userspace ocfl client

""" + Fuse.fusage
    logging.basicConfig(level=logging.INFO)
    server = OCFLFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='whine')
    server.parser.add_option(mountopt="ocfl_root", metavar="PATH",
                             help="load OCFL root from PATH")
    server.parser.add_option(mountopt="staging_directory", metavar="PATH",
                             help="use PATH as staging directory")
    server.parse(values=server,errex=1)
    # Create staging directory if missing
    if not os.path.exists(server.staging_directory):
        os.mkdir(server.staging_directory)
    # Check if we already got the ocfl root or use one additional parameter
    if len(server.cmdline[1]) == 1 and not hasattr(server, "ocfl_root"):
        server.ocfl_root=server.cmdline[1][0];
    try:
        # server.store=Store(server.ocfl_root)
        server.ocflpy = OCFLPY(server.ocfl_root,server.staging_directory,'pairtree')
        # server.store.validate()
    except AttributeError as e:
        print("No OCFL root or staging directory given")
        exit(-1)
    server.main()
    # Cleanup staging directory
    shutil.rmtree(server.staging_directory)

if __name__ == '__main__':
    main()
