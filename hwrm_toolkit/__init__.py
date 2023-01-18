# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

# Definining Add on propertiies
bl_info = {
	"name": "Homeworld Remastered Toolkit",
	"author": "David Lejeune, Dominic Cassidy & Dom2 , code-Raziel Updates",
	"version": (2, 0, 1),
	"blender": (3, 3, 0),
	"api": 38691,
	"location": "File > Import-Export",
	"description": ("A combined toolkit for creating content for Homeworld Remastered. Includes a modified version of the Better Collada Exporter, new create options to automate Joint creation and a DAE importer."),
	"warning": "",
	"wiki_url": (""),
	"tracker_url": "",
	"support": 'OFFICIAL',
	"category": "Import-Export"}

def cleanse_modules():
    """search for your plugin modules in blender python sys.modules and remove them"""
    import sys

    all_modules = sys.modules 
    all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
   
    for k,v in all_modules.items():
        if k.startswith(__name__):
            del sys.modules[k]

    return None 

	

import math


import bpy
import mathutils
import os
import bpy_extras
from pathlib import Path
from subprocess import Popen, PIPE

def get_hwrm_mod_dir():
    key= r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 244160'
    output = Popen(f'CMD /C Reg Query "{key}" /v InstallLocation',universal_newlines=True,stdout=PIPE,shell=True, text=True )
    output = output.stdout.read()
    if "InstallLocation" in output:
        mod_dir = Path( output[(88+34):-2] ).resolve() / 'HomeworldRM' / 'Data' 
        if not os.path.exists(mod_dir / 'ship') :
            #os.mkdir(mod_dir, mode = 0o777 )
            os.mkdir(mod_dir / 'ship', mode = 0o777 )
        return mod_dir
    else:
        output = 'Not Found'
        return output

from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    IntProperty,
    CollectionProperty,
	                    )

from bpy_extras.io_utils import (
    ImportHelper, # seb
    ExportHelper,
    orientation_helper,
    path_reference_mode,
    axis_conversion,
	                             )
#
# from . import joint_tools
#
class ExportDAE(bpy.types.Operator, ExportHelper):
    '''Selection to DAE'''
    bl_idname = "export_scene.dae"
    bl_label = "Export DAE"
    bl_options = {'PRESET'}

    filename_ext = ".dae"
    filter_glob = StringProperty(default="*.dae", options={'HIDDEN'})
    #filepath = str(Path(__file__).resolve().parent / 'HODOR' / 'models')
    #default_collada_path = StringProperty(subtype='DIR_PATH')"N:\001-J_Lab\101-Projects"
    # List of operator properties, the attributes will be assigned
# to the class instance from the operator settings before calling.
	
    object_types = EnumProperty(
            name="Object Types",
            options={'ENUM_FLAG'},
            items=(('EMPTY', "Empty", ""),
                    ('CAMERA', "Camera", ""),
                    ('LAMP', "Lamp", ""),
                    ('ARMATURE', "Armature", ""),
                    ('MESH', "Mesh", ""),
                    ('CURVE', "Curve", ""),
                    ),
            default={'EMPTY', 'CAMERA', 'LAMP', 'ARMATURE', 'MESH','CURVE'},
            )


    @property
    def check_extension(self):
        return True #return self.batch_mode == 'OFF'
    def check(self, context):
        return True
        """
        isretur_def_change = super().check(context)
        return (is_xna_change or is_def_change)
        """
    def execute(self, context):
        # print (str(Path(__file__).resolve().parent / 'HODOR' / 'models' / " "))
        if not self.filepath:
            raise Exception("filepath not set")
        """        global_matrix = Matrix()

                global_matrix[0][0] = \
                global_matrix[1][1] = \
                global_matrix[2][2] = self.global_scale
        """
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "global_scale",
                                            "check_existing",
                                            "filter_glob",
                                            "xna_validate",
                                            ))
        from . import newDaeExport
        return newDaeExport.save(self.filepath)

    def invoke(self, context, event):
        collection_name = bpy.data.collections[0].name # Filename based on collection name
        ship_dir = get_hwrm_mod_dir().resolve() / 'ship' / collection_name 
        if not os.path.exists(ship_dir) :
            os.mkdir(ship_dir, mode = 0o777 )
        self.filepath = str( ship_dir / collection_name / ( collection_name + ".dae" ) ) # Set Default Path
        wm = context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ImportDAE(bpy.types.Operator, ImportHelper):
    """Import HWRM DAE"""
    bl_idname = "import_scene.dae"
    bl_label = "Import HWRM DAE"
    bl_options = {'UNDO'}
    # All = must be converted in :
    # filename_ext = ".dae"
    files : CollectionProperty(
        name="File Path",
        description="File path used for importing the hwrm DAE file",
        type=bpy.types.OperatorFileListElement,
            )

    directory : StringProperty(
            subtype='DIR_PATH',
            )

    filename_ext = ".dae"

    filter_glob : StringProperty(
            default="*.dae",
            options={'HIDDEN'},
            )

    import_as_visual_mesh : BoolProperty(
            name="Import as visual mesh",
            description="Import LOD[0] only as visual mesh",
            default=False,
            )

    merge_goblins : BoolProperty(
            name="Merge goblins",
            description="Merge goblins into LOD[0] mesh",
            default=False,
            )

    use_smoothing : BoolProperty(
            name="Split normals",
            description="Sometimes splitting normals causes Crash To Desktop for unknown reasons. If you get CTD, try turning this off...",
            default=True,
            )

    dock_path_vis : EnumProperty(
        name="Display dock segments as ",
        items=(
                ('CONE', "Cone", ""),
                ('SPHERE', "Sphere", ""),
                ('CUBE', "Cube", ""),
                ('CIRCLE', "Circle", ""),
                ('SINGLE_ARROW', "Single Arrow", ""),
                ('ARROWS', "Arrows", ""),
                ('PLAIN_AXES', "Plain Axes", ""),
                ),
        default='SPHERE',
        )

    def execute(self, context):
        print("Executing HWRM DAE import")
        print(self.filepath)
        from . import import_dae # re-import, just in case!
        if self.import_as_visual_mesh:
            print("Importing visual mesh only...")
            import_dae.ImportLOD0(self.filepath, self.use_smoothing)
        else:
            import_dae.ImportDAE(self.filepath, self.use_smoothing, self.dock_path_vis, self.merge_goblins)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'import_as_visual_mesh')

# ###############################################################################
# class ImportLevel(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
# 	"""Import HWRM Level"""
# 	bl_idname = "import_scene.level"
# 	bl_label = "Import HWRM Level"
# 	bl_options = {'UNDO'}
#
# 	filename_ext = ".level"
#
# 	filter_glob = bpy.props.StringProperty(
# 			default="*.level",
# 			options={'HIDDEN'},
# 			)
# 	files = bpy.props.CollectionProperty(
# 			name="File Path",
# 			type=bpy.types.OperatorFileListElement,
# 			)
# 	directory = bpy.props.StringProperty(
# 			subtype='DIR_PATH',
# 			)
# 	def execute(self, context):
# 		print("Executing HWRM Level import")
# 		print(self.filepath)
# 		from . import import_level # re-import, just in case!
# 		import_level.ImportLevel(self.filepath)
# 		return {'FINISHED'}
###############################################################################
# def menu_func(self, context):
#     self.layout.operator(ExportDAE.bl_idname, text="HWRM Collada (.dae)")
#
# def menu_import(self, context):
# 	self.layout.operator(ImportDAE.bl_idname, text="HWRM DAE (.dae)")
# 	self.layout.operator(ImportLevel.bl_idname, text="HWRM Level (.level)")
#
# def register():
# 	bpy.utils.register_module(__name__)
# 	bpy.types.INFO_MT_file_export.append(menu_func)
# 	bpy.types.INFO_MT_file_import.append(menu_import)
#
#
# def unregister():
# 	bpy.utils.unregister_module(__name__)
# 	bpy.types.INFO_MT_file_export.remove(menu_func)
# 	bpy.types.INFO_MT_file_import.remove(menu_import)
#
# if __name__ == "__main__":
   # register()

# Start registering simple hwrm script

def menu_import(self, context):
 	self.layout.operator(ImportDAE.bl_idname, text="HWRM DAE (.dae)")

def menu_export(self, context):
	self.layout.operator(ExportDAE.bl_idname, text="HWRM DAE (.dae)")

def register():
	bpy.utils.register_class(ImportDAE)
	bpy.types.TOPBAR_MT_file_import.append(menu_import)
	bpy.utils.register_class(ExportDAE)
	bpy.types.TOPBAR_MT_file_export.append(menu_export)

def unregister():
	bpy.utils.unregister_class(ImportDAE)
	bpy.types.TOPBAR_MT_file_import.remove(menu_import)
	bpy.utils.unregister_class(ExportDAE)
	bpy.types.TOPBAR_MT_file_export.remove(menu_export)
	cleanse_modules()

if __name__ == "__main__":
	register()
