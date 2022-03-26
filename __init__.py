# Copyright (C) 2021-2022 MMaker <mmaker@mmaker.moe>
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
    "version" : (0, 0, 2),
    "category" : "Animation"
}

import bpy
import mathutils
import bl_math # type: ignore

class G:
    selected_keys = []
    bezier = []

def inverse_lerp(minimum, maximum, val):
    return (val - minimum) / (maximum - minimum)
    
def create_bezier(handles, co_left_side, co_right_side):
        return list(
            map(
                lambda x: list(map(
                    lambda v, dimension: inverse_lerp(co_left_side[dimension], co_right_side[dimension], v),
                    x,
                    range(2)
                )),
                handles
            )
        )
   
def convert_handles_to_bezier(keyframes):
    # TODO(mmaker): Some of the logic here, particularly when selecting one key,
    # is likely not the correct way to calculate the bezier.
    # Should do a second pass over this and see if it could be cleaned up to be more accurate.
    # (I'm not very math pilled, sorry)
    # 
    # This at minimum should handle any types of user selections though.
    # (Two keys, a single key, several keys across different fcurves)
    
    beziers = []
    for fcurve, key_indexes in keyframes.items():
        f_keys = fcurve.keyframe_points
        
        # Case when only one key is selected
        # TODO(mmaker): Clean up this logic
        if len(key_indexes) == 1:
            key = f_keys[key_indexes[0]]
            beziers.append(create_bezier([
                key.handle_left, key.handle_right
            ], key.co, [0.0, 0.0]))
        
        for i in key_indexes[:-1]:
            # NOTE(mmaker): This naming could probably be better, lol
            handle_left_side = f_keys[i].handle_right
            co_left_side = f_keys[i].co
            if i >= len(f_keys):
                # Case when selected key is the last in the fcurve
                handle_right_side = [0.0, 0.0]
                co_right_side = f_keys[i].co
            else:
                handle_right_side = f_keys[i + 1].handle_left
                co_right_side = f_keys[i + 1].co
                
            handles = [handle_left_side, handle_right_side]
            beziers.append(create_bezier(handles, co_left_side, co_right_side))
            
    # Average beziers
    # NOTE(mmaker): I'm sure there is a way to vectorize this, but until then, B)
    bezier = [
        [
            sum([x[0] for x in list(zip(*beziers))[0]]) / len(beziers),
            sum([x[1] for x in list(zip(*beziers))[0]]) / len(beziers)
        ],
        [
            sum([x[0] for x in list(zip(*beziers))[1]]) / len(beziers),
            sum([x[1] for x in list(zip(*beziers))[1]]) / len(beziers)
        ]
    ]

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
            G.selected_keys = {}
            
            for fcurve in fcurves:
                for key_index, key in enumerate(fcurve.keyframe_points):
                    if key.select_control_point:
                        if fcurve not in G.selected_keys:
                            G.selected_keys[fcurve] = []
                        G.selected_keys[fcurve].append(key_index)
        
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
                f_keys = fcurve.keyframe_points
                for i in range(0, len(f_keys)):
                    if (f_keys[i].select_control_point):
                        if fcurve not in selected_keys:
                            selected_keys[fcurve] = []
                        selected_keys[fcurve].append(i)

            for fcurve, key_indexes in selected_keys.items():
                if (len(key_indexes) == 0):
                    self.report({"WARNING"}, "Please select some keyframes to paste an ease to.")
                    return {'CANCELLED'}
                if (len(key_indexes) == 1):
                    # TODO: Implement logic for this soon
                    pass
                else:
                    key_indexes.pop() # TODO: Related to above, implement soon
                    for i in key_indexes:
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
