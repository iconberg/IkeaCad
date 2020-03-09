import bpy
import csv
import re
import os
import subprocess
import tempfile
import platform
from shutil import copyfile
from math import pi, cos, sin, radians


ikea_colors = {
    'white': (1,1,1,1),
    'black': (0,0,0,1),
    'red': (1,0,0,1),
    'green': (0,1,0,1),
    'blue': (0,0,1,1),
    'yellow': (1,1,0,1),
    'purple': (1,0,1,1),
    'cyan': (0,1,1,1),
    'grey': (.5,.5,.5,1),
}

dim_factor = .01

ext_data_sep = ':'
cell_parts_sep = '(r|p)'
xyz_re_str = '(?:x(?P<x>\d+))?(?:y(?P<y>\d+))?(?:z(?P<z>\d+))?'
cmd_re_str = '(?:\*)(?P<command>.+)(\()(?P<parameter>.+)(\))'

object_list = []
command_list = []
modifier_active = []


def solidify(mod, mod_para):
    paras = mod_para.split(':')
    for para in paras:
        k, v = para.split('=')
        if k == 'thickness':
            mod.thickness = float(v)
            continue
        if k == 'use_rim':
            mod.use_rim = True if v.lower() == 'true' else False
            continue
        if k == 'use_rim_only':
            mod.use_rim_only = True if v.lower() == 'true' else False
            continue
        if k == 'use_even_offset':
            mod.use_even_offset = True if v.lower() == 'true' else False
            continue

modifier_list = {'solidify': solidify}


def exec_commands(celldata):
    "execute commands, manage modifiers"
    cmd_para = re.match(cmd_re_str, celldata).groupdict()
    if cmd_para['command'] in modifier_list:
        if cmd_para['parameter'] == 'remove':
            for modifier in modifier_active:
                if modifier['command'] == cmd_para['command']:
                    modifier_active.remove(modifier)
        else:
            modifier_active.append(cmd_para)
    return


def add_modifier(obj):
    for pos, modifier in enumerate(modifier_active):
        mod_name = modifier['command']
        mod_para = modifier['parameter']
        mod_func = modifier_list[mod_name]
        mod_id = '{} {}'.format(mod_name, pos + 1)
        mod = obj.modifiers.new(mod_id, mod_name.upper())
        mod_func(mod, mod_para)
    

def parse_cell(celladdr, celldata):
    """parse cell data
    <dimension, rotation, location>:<extension data>"""
    if ext_data_sep in celldata:
        cellparts, ext_data = celldata.split(ext_data_sep)
    else:
        cellparts = celldata
        ext_data = ''
    cellparts = re.split(cell_parts_sep, cellparts)
    cellparts.append(ext_data_sep)
    cellparts.append(ext_data)
    
    obj_data = {}
    obj_data['name'] = chr(65 + celladdr[0]) + str(celladdr[1] + 1)
    for partpos in range(0, len(cellparts)):
        part = cellparts[partpos]

        "First part is dimenson"
        if partpos == 0:
            obj_data['dimension'] = parse_dimension(part)
            continue

        "r otation"
        if part == 'r':
            obj_data['rotation'] = parse_rotation(cellparts[partpos+1])
            continue

        "p location" # p is better readable in sheet data
        if part == 'p':
            obj_data['location'] = parse_location(cellparts[partpos+1])
            continue
        
        "; ext_data, currently color only"
        if ext_data:
            obj_data['color'] = ext_data
            continue
        
    return obj_data


def parse_dimension(dimension):
    "parse string '1x1x1' to list of float"
    return [float(d) * dim_factor for d in dimension.split('x')]


def parse_location(location):
    "parse string 'y1z1x1' to list of float, sort xyz and fill missing coordinates"
    default_location = {'x': .0, 'y': .0, 'z': .0}
    matches = re.finditer(xyz_re_str, location)
    for match in matches:
        for k, v in match.groupdict().items():
            if v:
                default_location[k] = float(v)
    return list(default_location.values())


def parse_rotation(rotation):
    "parse string to dict of float, keep given order"
    rotation_dict = {}
    matches = re.finditer(xyz_re_str, rotation)
    for match in matches:
        for k, v in match.groupdict().items():
            if v:
                rotation_dict[k] = float(v)
    return rotation_dict


def create_plane(dimension=None, rotation=None, location=None, name='plane', color=None):
    x, y = dimension
    vertices = [(0,0,0),(x,0,0),(x,y,0),(0,y,0)]
    faces = [(0,1,2,3)]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(vertices, [], faces)
    bpy.ops.object.select_all(action='DESELECT')
    if ikea_colors.get(color, None):
        obj.color = ikea_colors.get(color)
    if location:
        obj.location = location
    else:        
        bpy.context.scene.cursor.location = (0,0,0)
    if rotation:
        for axis, r in rotation.items():
            angle = pi*2/360*int(r)
            obj.rotation_euler[ord(axis) - 120] = angle
    if modifier_active:
        add_modifier(obj)


def create_objects(obj_data):
    c = len(obj_data.get('dimension'))
        
    if c == 1:
        pass
    if c == 2:
        create_plane(**obj_data)
    if c == 3:
        pass


def do_ikeacad(filename):
    print(filename)
    with open(filename, newline='') as cadfile:
        cadreader = csv.reader(cadfile, delimiter='\t', quotechar=None)
        for row_number, row in enumerate(cadreader):
            if not row or row[0][0] == '#':
                continue
            for col_number, cell in enumerate(row):
                if cell:
                    if cell[0] == '#':
                        continue
                    elif cell[0] == '*':
                        print(cell)
                        exec_commands(cell)
                    else:
                        celladdr = (col_number, row_number)
                        obj_data = parse_cell(celladdr, cell)                
                        print(obj_data)
                        create_objects(obj_data)
                        object_list.append(obj_data)
    
    without_location_obj = [obj for obj in object_list if not 'location' in obj]
    circle_size = max(object_list[0]['dimension']) * 2
    steps = radians(180 / (len(without_location_obj)))
    for i, obj_data in enumerate(without_location_obj):
        if i == 0: # skip first object as origin
            continue
        x = cos(steps * i) * circle_size
        z = sin(steps * i) * circle_size
        bpy.data.objects[obj_data['name']].location = location=(x, 0, z)
                                

def open_ikeacad_txt(filename):
    my_os = platform.system()
    if my_os == 'Linux':
        start_cmd = 'xdg-open'
    elif my_os == 'Windows':
        start_cmd = 'start'
    else:
        start_cmd = 'open'

    if not filename:
        addonpath = os.path.dirname(os.path.abspath(__file__))
        example = os.path.join(addonpath, 'ikeacad.txt')
        filename = os.path.join(tempfile.gettempdir(), 'ikeacad.txt')
        copyfile(example, filename)
    else:
        filename = filename.replace('.blend', '_ikeacad.txt')
    open(filename, 'a').close()
    process = subprocess.check_output([start_cmd, filename])
    return filename


class IkeaCad_OT_Operator(bpy.types.Operator):
    bl_idname = "mesh.ikeacad"
    bl_label = "IkeaCad"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        object_list.clear()
        modifier_active.clear()        
        filename = bpy.data.filepath
        filename = open_ikeacad_txt(filename)
        do_ikeacad(filename)
        bpy.context.space_data.shading.color_type = 'OBJECT'
        bpy.context.scene.tool_settings.snap_elements = {'VERTEX', 'EDGE'}
        bpy.context.scene.tool_settings.use_snap = True
        return {'FINISHED'}


def register():
    bpy.utils.register_class(IkeaCad_OT_Operator)


def unregister():
    bpy.utils.unregister_class(IkeaCad_OT_Operator)


if __name__ == '__main__':
    register()
