import bpy

from MeshLint.addons.MeshLint.meshLint.MeshLintObjectLooper import MeshLintObjectLooper
from MeshLint.addons.MeshLint.meshLint.utilities import is_edit_mode


class MeshLintObjectDeselector(MeshLintObjectLooper, bpy.types.Operator):
    """Uncheck boxes below to prevent from running (Object Mode only)"""
    bl_idname = "meshlint.objects_deselect"
    bl_label = "Mesh Lint Deselect"
    bl_options = {'REGISTER', 'UNDO'}
    text = "Deselect all Lint-free Objects"

    @classmethod
    def poll(cls, context):
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        return len(selected_meshes) > 1 and not is_edit_mode()

    def execute(self, context):
        if not self.examine_all_selected_meshes():
            self.report({'WARNING'}, "All Lint-free objects are deselected.")
        else:
            self.report({'INFO'}, "All meshes are clean!")
        return {'FINISHED'}