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
# from ocfl.store import Store
from ocflpy import OCFLPY
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
        # Keep track of the files in the current object
        self.current_object_files=[]
        # Keep track of the directories in the current object
        self.current_object_dirs=[]
        # Mapping normalized object ids back to the original ones
        # self.id_map={}

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
        # Path containing all objects
        elif split_path[0] == self.object_path:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        # Folders in the current object
        elif path in self.current_object_dirs:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        # Files in the current object
        elif path in self.current_object_files:
            st.st_mode = stat.S_IFREG | 0o755
            st.st_nlink = 1
            st.st_size = 42
            st.st_mtime=1648052817
        elif path.endswith("commit"):
            st.st_mode = stat.S_IFREG | 0o755
            st.st_nlink = 1
            st.st_size = 0
            st.st_mtime=0
        # elif path.endswith(hello_path):
        #     st.st_mode = stat.S_IFREG | 0o444
        #     st.st_nlink = 1
        #     st.st_size = len(hello_str)
        #     st.st_mtime=1648052817
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

    # # int(* 	mkdir )(const char *, mode_t)
    # def mkdir(self, path,mode):
    #     logging.info("MKDIR: " + path)
    #     return 0
    
    # # int(* 	unlink )(const char *)
    # def unlink(self, path):
    #     logging.info("UNLINK: " + path)
    #     return 0
    
    # # int(* 	rmdir )(const char *)
    # def rmdir(self, path):
    #     logging.info("RMDIR: " + path)
    #     return 0
    
    # # int(* 	symlink )(const char *, const char *)
    # def symlink(self, target, path):
    #     logging.info("SYMLINK: " + path)
    #     return 0
    
    # # int(* 	rename )(const char *, const char *, unsigned int flags)
    # def rename(self, oldpath, path, flags):
    #     logging.info("RENAME: " + path)
    #     return 0
    
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
        object_file_path=self.get_object_file_path(path)
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
        if path == self.object_path or \
            os.path.split(path)[0] == self.object_path or \
            path in self.current_object_dirs or \
            path in self.current_object_files:
            return 0
        # if not(path.endswith(hello_path)):
        #     return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    # int(* 	read )(const char *, char *, size_t, off_t, struct fuse_file_info *)
    def read(self, path, size, offset):
        logging.info("READ: " + path + " SIZE: " + str(size) + " OFFSET: " + str(offset))
        # Read one of the project files
        if path in self.current_object_files:
            object_file_path=self.get_object_file_path(path)
            f = open(object_file_path, 'rb')
            f.seek(offset)
            data = f.read(size)
            f.close()
            return data
        return -errno.ENOENT
    #     if not(path.endswith(hello_path)):
    #         return -errno.ENOENT
    #     slen = len(hello_str)
    #     if offset < slen:
    #         if offset + size > slen:
    #             size = slen - offset
    #         buf = hello_str[offset:offset+size]
    #     else:
    #         buf = b''
    #     return buf

    # int(* 	write )(const char *, const char *, size_t, off_t, struct fuse_file_info *)
    def write(self, path, data, offset): # length):
        logging.info("WRITE: " + path)
        object_file_path=self.get_object_file_path(path)
        f = open(object_file_path, 'wb')
        # f.seek(offset)
        len = f.write(data)
        f.close()
        # if path in self.current_object_files:
        #     # Get the path of file in staging and read it
        #     oid = self.current_object_id
        #     file_path=path.replace(os.path.join(self.object_path,self.ocflpy.encode_id(oid)) + "/","")
        #     object_file_path=os.path.join(self.ocflpy.get_staging_object_path(oid),file_path)
        #     f = open(object_file_path, 'rb')
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
        # The object path
        elif path == self.object_path:
            for oid in self.ocflpy.list_object_ids():
                normalized_id=self.ocflpy.encode_id(oid)
                yield fuse.Direntry(normalized_id)
        # A folder somewhere deeper in the object
        elif path in self.current_object_dirs:
            for file in self.ocflpy.list_object_files(self.current_object_id):
                object_id = self.ocflpy.encode_id(self.current_object_id)
                object_folder=path.replace(os.path.join(self.object_path,object_id)+ "/","")
                if file.startswith(object_folder):
                    stripped_file = file.replace(object_folder+"/","")
                    if "/" in stripped_file:
                        # Handle next level of folders
                        path_split=stripped_file.split("/")
                        self.current_object_dirs.append(os.path.join(path,path_split[0]))
                        yield fuse.Direntry(path_split[0])
                    else:
                        # Plain file
                        self.current_object_files.append(os.path.join(path,stripped_file))
                        yield fuse.Direntry(stripped_file)
        split_path=os.path.split(path)
        # Files in one of the objects
        if split_path[0] == self.object_path:
            # get object id
            object_id=split_path[1]
            self.current_object_id=self.ocflpy.decode_id(object_id)
            # Check if we already have the file list in memory
            if self.current_object_files != [] and self.current_object_dirs != []:
                for file in self.current_object_files + self.current_object_dirs:
                    file_name=file.replace(os.path.join(self.object_path,object_id) + "/","")
                    # TODO should we handle slashes?
                    yield fuse.Direntry(file_name)
            # otherwise read from the store
            else:
                # get file list for id
                for file in self.ocflpy.list_object_files(self.current_object_id):
                    if "/" in file:
                        # Handle first level of folders
                        path_split=file.split("/")
                        self.current_object_dirs.append(os.path.join(path,path_split[0]))
                        yield fuse.Direntry(path_split[0])
                    else:
                        # Plain file
                        self.current_object_files.append(os.path.join(path,file))
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
                self.current_object_id = ""
                self.current_object_files=[]
                self.current_object_dirs=[]
        split_path=os.path.split(path)
        if split_path[0] == self.object_path and split_path[1] != "":
            object_id=split_path[1]
            id=self.ocflpy.decode_id(object_id)
            self.ocflpy.open_object(id)
        return 0
    
    # int(* 	create )(const char *, mode_t, struct fuse_file_info *)
    def create(self, path, mode ,file_info):
        logging.info("CREATE: " + path + " - Mode: " + str(mode) + " - File Info: " + str(file_info))
        if path.endswith("/commit"):
            object_id=self.current_object_id
            self.ocflpy.commit_object(object_id)
        else:
            if self.current_object_id != "":
                logging.info("ADDING " + path)
                # Check if file exists and otherwise create it
                object_file_path=self.get_object_file_path(path)
                if not os.path.exists(object_file_path):
                    open(object_file_path,'wb').close()
                self.current_object_files.append(path)
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

    # Gets the staging file name for an object file
    def get_object_file_path(self,path):
        # Get the path of file in staging and read it
        oid=self.current_object_id
        file_path=path.replace(os.path.join(self.object_path,self.ocflpy.encode_id(oid)) + "/","")
        return os.path.join(self.ocflpy.get_staging_object_path(oid),file_path)
    
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
