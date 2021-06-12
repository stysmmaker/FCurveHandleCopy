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
	"description" : "",
	"blender" : (2, 83, 0),
	"version" : (0, 0, 1),
	"location" : "",
	"warning" : "",
	"category" : "Animation"
}

"""
if "bpy" in locals():
	import importlib
	importlib.reload(ui)
else:
	from . import ui
"""

import bpy
import mathutils

class G:
	pass

def convert_handles_to_bezier(keyframes):
	bezier = []

	in_key = keyframes[0]
	out_key = keyframes[1]

	in_handle = in_key.handle_right
	out_handle = out_key.handle_left

	bezier.append(in_handle[0]  / (abs(in_key.co[0] - out_key.co[0]))) # x1
	bezier.append(in_handle[1]  / (abs(in_key.co[1] - out_key.co[1]))) # y1
	bezier.append(out_handle[0] / (abs(in_key.co[0] - out_key.co[0]))) # x2
	bezier.append(out_handle[1] / (abs(in_key.co[1] - out_key.co[1]))) # y2

	return bezier

def generate_new_handles(in_key, out_key):
	x_diff = abs(in_key.co[0] - out_key.co[0])
	y_diff = abs(in_key.co[1] - out_key.co[1])

	y_direction = (1 if (in_key.co[1] - out_key.co[1]) < 0 else -1)

	new_in_handle = mathutils.Vector((
		in_key.co[0] + (G.bezier[0] * x_diff),
		in_key.co[1] + (G.bezier[1] * y_diff * y_direction)
	))

	new_out_handle = mathutils.Vector((
		in_key.co[0] + (G.bezier[2] * x_diff),
		in_key.co[1] + (G.bezier[3] * y_diff * y_direction)
	))

	return [new_in_handle, new_out_handle]

class FCurveHandleCopyValue(bpy.types.Operator):
	"""Copy FCurve handle values"""
	bl_idname = "anim.mmaker_fcurve_handle_copy_values"
	bl_label = "Copy"

	def execute(self, context):
		if (context.selected_visible_fcurves):
			fcurves = context.selected_visible_fcurves
			G.selected_keys = []

			if (len(fcurves) > 1):
				self.report({"WARNING"}, "Please only select one curve when copying an ease.")
				return {'CANCELLED'}
			
			for keyframe in fcurves[0].keyframe_points:
				if (len(G.selected_keys) > 2):
					self.report({"WARNING"}, "Please select exactly two keyframes when copying an ease.")
					return {'CANCELLED'}
				
				if (keyframe.select_control_point):
					G.selected_keys.append(keyframe)
		
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

			for fcurve in fcurves:
				keys = fcurve.keyframe_points
				selected_keys = []
				for i in range(0, len(keys)):
					if (keys[i].select_control_point):
						selected_keys.append(i)

				if (len(selected_keys) == 0):
					self.report({"WARNING"}, "Please select some keyframes to paste an ease to.")
					return {'CANCELLED'}
				if (len(selected_keys) == 1):
					# TODO: Implement logic for this soon
					pass
				else:
					selected_keys.pop() # TODO: Related to above, implement soon
					for i in selected_keys:
						if (i < len(keys) - 1):
							new_handles = generate_new_handles(keys[i], keys[i + 1])
							keys[i].handle_right_type = 'FREE'
							keys[i + 1].handle_left_type = 'FREE'
							keys[i].handle_right    = new_handles[0]
							keys[i + 1].handle_left = new_handles[1]

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