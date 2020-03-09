bl_info = {
    "name": "ikeacad",
    "author": "Rigoletto",
    "version": (0, 5),
    "blender": (2, 80, 0),
    "location": "F3: Ikeacad",
    "description": "Create simple meshes from csv file",
    "warning": "BETA",
    "support": "COMMUNITY", 
    "wiki_url": "",
    "category": "Add Mesh",
}

import bpy

from . ikeacad import IkeaCad_OT_Operator

def register():
	bpy.utils.register_class(IkeaCad_OT_Operator)

def unregister():
	bpy.utils.unregister_class(IkeaCad_OT_Operator)
