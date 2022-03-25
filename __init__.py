# Copyright (C) 2021 MMaker <mmaker@mmaker.moe>
# 
# This file is part of FCurveHandleCopy.
# 
# FCurveHandleCopy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# FCurveHandleCopy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with FCurveHandleCopy.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "FCurveHandleCopy",
    "author" : "MMaker",
    "description" : ":)",
    "blender" : (2, 83, 0),
    "version" : (0, 0, 1),
    "category" : "Animation"
}

import bpy
import mathutils
import bl_math

class G:
    selected_keys = []
    bezier = []

def inverse_lerp(minimum, maximum, val):
    return (val - minimum) / (maximum - minimum)
        
def convert_handles_to_bezier(keyframes):
    handles = [keyframes[0].handle_right, keyframes[1].handle_left]

    bezier = list(map(
        lambda x: list(map(
            lambda v, dimension: inverse_lerp(keyframes[0].co[dimension], keyframes[1].co[dimension], v),
            x,
            range(2)
        )),
        handles
    ))
    return bezier

def generate_new_handles(in_key, out_key):
    handles = list(map(
        lambda fac: list(map(
            lambda dimension: bl_math.lerp(in_key.co[dimension], out_key.co[dimension], fac[dimension]),
            range(2)
        )),
        G.bezier
    ))
        
    return [
        mathutils.Vector(
            (handles[0][0], handles[0][1])
        ),
        mathutils.Vector(
            (handles[1][0], handles[1][1])
        )
    ]

class FCurveHandleCopyValue(bpy.types.Operator):
    """Copy FCurve handle values"""
    bl_idname = "anim.mmaker_fcurve_handle_copy_values"
    bl_label = "Copy"

    def execute(self, context):
        if (context.selected_visible_fcurves):
            fcurves = context.selected_visible_fcurves
            G.selected_keys = []
            
            for fcurve in fcurves:
                for key in fcurve.keyframe_points:
                    if key.select_control_point:
                        G.selected_keys.append(key)
                        if (len(G.selected_keys) > 2):
                            self.report({"WARNING"}, "Please select exactly two keyframes when copying an ease.")
                            return {'CANCELLED'}
        
        if (len(G.selected_keys) != 2):
            self.report({"WARNING"}, "Please select exactly two keyframes when copying an ease.")
            return {'CANCELLED'}
        
        G.bezier = convert_handles_to_bezier(G.selected_keys)

        return {'FINISHED'}

class FCurveHandlePasteValue(bpy.types.Operator):
    """Paste FCurve handle values"""
    bl_idname = "anim.mmaker_fcurve_handle_paste_values"
    bl_label = "Paste"

    def execute(self, context):
        if (context.selected_visible_fcurves):
            fcurves = context.selected_visible_fcurves

            selected_keys = {}

            for fcurve in fcurves:
                keys = fcurve.keyframe_points
                for i in range(0, len(keys)):
                    if (keys[i].select_control_point):
                        if fcurve not in selected_keys:
                            selected_keys[fcurve] = []
                        selected_keys[fcurve].append(keys[i])

            for fcurve, keys in selected_keys.items():
                if (len(keys) == 0):
                    self.report({"WARNING"}, "Please select some keyframes to paste an ease to.")
                    return {'CANCELLED'}
                if (len(keys) == 1):
                    # TODO: Implement logic for this soon
                    pass
                else:
                    keys.pop() # TODO: Related to above, implement soon
                    for i, _ in enumerate(keys):
                        f_keys = fcurve.keyframe_points
                        if (i < len(f_keys) - 1):
                            new_handles = generate_new_handles(f_keys[i], f_keys[i + 1])
                            f_keys[i].interpolation = 'BEZIER'
                            f_keys[i + 1].interpolation = 'BEZIER'
                            f_keys[i].handle_right_type = 'FREE'
                            f_keys[i + 1].handle_left_type = 'FREE'
                            f_keys[i].handle_right    = new_handles[0]
                            f_keys[i + 1].handle_left = new_handles[1]

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(FCurveHandleCopyValue.bl_idname)
    self.layout.operator(FCurveHandlePasteValue.bl_idname)

classes = [
    FCurveHandleCopyValue,
    FCurveHandlePasteValue
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.GRAPH_HT_header.append(menu_func)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.GRAPH_HT_header.remove(menu_func)

if __name__ == "__main__":
    try:
        unregister()
    except:
        import sys
        print("Error:", sys.exc_info()[0])
        pass
    register()
