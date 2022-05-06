# ocfl-fuse

The aim of this project is to explore the means of managing data stored in an
OCFL store. It uses FUSE (filesystem in user space) for the user interaction.
The structure is the following:

     _______        _________        _________________        ______________        ______        ______
    |       |      |         |      |                 |      |              |      |      |      |      |
    | OCFL  | <--> | ocfl-py | <--> | ocfl_wrapper.py | <--> | ocfl-fuse.py | <--> | FUSE | <--> | User |
    | store |      |         |      |                 |      |              |      |      |      |      |
    |_______|      |_________|      |_________________|      |______________|      |______|      |______|

## How to use it

- Install dependencies, see [README.md](../README.md)
- Run `python ocfl-fuse.py -o ocfl_root=<ocfl-store> -o staging_directory=<staging-directory> <mount-point> [-f|-d]`
- Access objects via `<mount-point>`

If `<ocfl-store>` and/or `<staging-directory>` are missing they are created.
The parameters `-f` does not detach the process into the background and `-d`
enables debug output (implies `-f`).

## Transactions

OCFL itself only provides means of storing and retrieving data. Building on this
storing mechachanism `ocfl_wrapper.py` builds a simple transaction mechanism.
Objects can only be updated when they are in a staging area. The most recent
version of an object can be extracted from the store and put into the staging
area. Afterwards changes to the object can either be commited back into the
OCFL store resulting in a new version or reverted, i.e. the changes are
discarded. New objects are created as staged objects and only put into the OCFL
store when committed.

```
 ________           ________          ______
|        |         |        |        |      |
| Stored | extract | Staged | update | User |
| object |   -->   | object |  <--   |      |
|________|   <--   |________|        |______|
           commit
                     /\  \/ 
                 create  discard
                   __________
                  |          |
                  | The void |
                  |__________|
```

## File system interface

The objects from the OCFL store are mapped in the following directory structure:

```
objects/
objects/<object1>/
objects/<object1>/<file1>
objects/<object1>/...
objects/<object1>/<file_n>
objects/<object1>/commit
objects/...
objects/<object_n>/
objects/<object_n>/<file1>
objects/<object_n>/...
objects/<object_n>/<file_n>
objects/<object_n>/commit
```

The folder `objects` contains all object identifiers for objects in the store.
Changing into one of the subdirectories puts the most recent version of the
corresponding object into the storage area and the user can modify its content.
Each object directory contains a virtual file `commit` which, when accessed
commits all changes back into the store. If the user instead leaves the
directory all uncommitted changes are discarded.

When creating a new subfolder in `objects` a new empty object is created in the
staging area. When committed it is added to the store as the initial version of
an object.

## Data storage and metadata

The user does not have direct access to the OCFL store avoiding problems
corrupting the store. Many details are hidden from the user, e.g. the way the
files are actually stored on disk as well as the content of previous versions.

OCFL can use various disposition strategies, i.e. the way the objects are stored
on disk in the directory structure of the file system. Ocfl-fuse currently uses
pairtrees based on the object identifiers. So if we have the three objects `object1`,
`object2` and `object3` we have the following directory structure on the disk:

```
<store>/
<store>/ob/
<store>/ob/je
<store>/ob/je/ct/
<store>/ob/je/ct/1/object1/...
<store>/ob/je/ct/2/object2/...
<store>/ob/je/ct/3/object3/...
```


It should be safe to use ocfl-fuse on OCFL stores created by ocfl-fuse because
it uses one specific disposition strategy. When using ocfl-fuse on a store
created by other means it is possible to have inconsistencies concerning
disposition strategies. It should be possible to access a store that
mixes disposition strategies. However, this could be problematic when trying to
understand the stored data without the relevant software.

OCFL stores a minimal set of metadata in addition to the content of the objects.
Besides a hash value to guarantee for the consistency of the stored files it
also stores the name and contact details of the creator of a version as well as
a message and the creation time. Most of this information is also hidden from
the user. Only the creation date is also recovered when extracting a version
from the store into the staging area.

When creating a version of an object the metadata is created in the following
way:

- creator name: can be an arbitrary string, we use the UNIX user name
- creator contact: has to be a URI or a mail address with the prefix `mailto:`, we use `username@hostname` as a mail address
- message: can be arbitrary string, we use either `Created object` or `Updated object` followed by the object id
- creation time: timestamp in ISO-8601 format, we use the current timestamp

