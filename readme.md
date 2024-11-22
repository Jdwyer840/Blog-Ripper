TODOS

1) rebuild migrations
2) re test refactored code
3) finish the command
4) FTP access
5) chat with boss about this
6) figure out plan for the main blog file, do we download the file and write to it? can we just write bytes directly to the file instead? im not sure if that is something we wana do or if it is normal.

save blogs to the database


ensure blogs dont get written twice


error reporting system

add an id field to the html content things and this will be the id that we can reference to ensure that data was actually put into the main blog..

a system to clean up old html files from the media folder.

command for cron runner to use


minimum
need ftp access
test the cron runner
work on front end.
 
TypeVar eh
T = TypeVar('T')  # Any type.
KT = TypeVar('KT')  # Key type.
VT = TypeVar('VT')  # Value type.
T_co = TypeVar('T_co', covariant=True)  # Any type covariant containers.
V_co = TypeVar('V_co', covariant=True)  # Any type covariant containers.
VT_co = TypeVar('VT_co', covariant=True)  # Value type covariant containers.
T_contra = TypeVar('T_contra', contravariant=True)  # Ditto contravariant.
# Internal type variable used for Type[].
CT_co = TypeVar('CT_co', covariant=True, bound=type)

# A useful type variable with constraints.  This represents string types.
# (This one *is* for export!)
AnyStr = TypeVar('AnyStr', bytes, str)