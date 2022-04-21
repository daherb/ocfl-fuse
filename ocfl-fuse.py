#!/usr/bin/env python

#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#    Copyright (C) 2022  Herbert Lange <lange@ids-mannheim.de>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.
#

import os, stat, errno
import fuse
from fuse import Fuse
# from ocfl.store import Store
from ocflpy import OCFLPY
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

object_path = "/objects"

class OCFLFS(Fuse):

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.root = "."
        self.folders=[]

    # int(* 	getattr )(const char *, struct stat *, struct fuse_file_info *fi)
    def getattr(self, path):
        logging.info("GETATTR: " + path)
        st = MyStat()
        # Root of our OCFL store
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        # The object path
        elif path == object_path:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        elif path in self.folders:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        elif path.startswith(object_path):
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
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
    
    # # int(* 	chmod )(const char *, mode_t, struct fuse_file_info *fi)
    # def chmod(self, path, mode):
    #     logging.info("CHMOD: " + path)
    #     return 0
    
    # # int(* 	chown )(const char *, uid_t, gid_t, struct fuse_file_info *fi)
    # def chown(self, path, user, group):
    #     logging.info("CHOWN: " + path)
    #     return 0
    
    # # int(* 	truncate )(const char *, off_t, struct fuse_file_info *fi)
    # def truncate(self, path, length):
    #     logging.info("TRUNCATE: " + path)
    #     return 0
    
    # int(* 	open )(const char *, struct fuse_file_info *)
    def open(self, path, flags):
        logging.info("OPEN: " + path)
        if path == object_path:
            return 0
        # if not(path.endswith(hello_path)):
        #     return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    # int(* 	read )(const char *, char *, size_t, off_t, struct fuse_file_info *)
    def read(self, path, size, offset):
        logging.info("READ: " + path)
        if path == object_path:
            return 0
        else:
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

    # # int(* 	write )(const char *, const char *, size_t, off_t, struct fuse_file_info *)
    # def write(self, path):
    #     logging.info("WRITE: " + path)
    #     return 0
    
    # # int(* 	statfs )(const char *, struct statvfs *)
    # def statfs(self, path):
    #     logging.info("STATFS: " + path)
    #     return 0
    
    # # int(* 	flush )(const char *, struct fuse_file_info *)
    # def flush(self, path):
    #     logging.info("FLUSH: " + path)
    #     return 0
        
    # # int(* 	release )(const char *, struct fuse_file_info *)
    # def release(self, path,file_info):
    #     logging.info("RELEASE: " + path)
    #     return 0
    
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
        # Root of our OCFL store
        if path == '/':
            for r in  (['.', '..', object_path[1:]] + [folder[1:] for folder in self.folders]):
                yield fuse.Direntry(r)
        # The object path
        elif path == object_path:
            for oid in (['.', '..'] + self.ocflpy.list_object_ids()):
                yield fuse.Direntry(oid)
        # Somewhere in one of the objects
        # elif path.startswith(object_path):
            # Try to find the path
            # Find the most recent version
            # List inventory
        # Otherwise just give . and ..
        else:
            for r in '.', '..':
                yield fuse.Direntry(r)
                
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
        if path.startswith(object_path) and path != object_path:
            object_id=path[len(object_path)+1:]
            self.ocflpy.open_object(object_id)
        return 0
    
    # int(* 	create )(const char *, mode_t, struct fuse_file_info *)
    def create(self, path):
        logging.info("CREATE: " + path)
        return 0
    
    # # int(* 	lock )(const char *, struct fuse_file_info *, int cmd, struct flock *)
    # #    def lock(self, cmd,owner,**kw):
    # def lock(self, path, cmd, owner, **kw):
    #     logging.info("LOCK: " + path)
    #     return 0
    
    # # int(* 	utimens )(const char *, const struct timespec tv[2], struct fuse_file_info *fi)
    # def utimens(self, path):
    #     logging.info("UTIMENS: " + path)
    #     return 0
    
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
    # Check if we already got the ocfl root or use one additional parameter
    if len(server.cmdline[1]) == 1 and not hasattr(server, "ocfl_root"):
        server.ocfl_root=server.cmdline[1][0];
    try:
        # server.store=Store(server.ocfl_root)
        server.ocflpy = OCFLPY(server.ocfl_root,server.staging_directory)
        # server.store.validate()
    except AttributeError as e:
        print("No OCFL root or staging directory given")
        exit(-1)
    server.main()

if __name__ == '__main__':
    main()
