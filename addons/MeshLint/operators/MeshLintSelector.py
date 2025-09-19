import bpy

from MeshLint.addons.MeshLint.meshLint.MeshLintObjectLooper import MeshLintObjectLooper
from MeshLint.addons.MeshLint.meshLint.utilities import has_active_mesh, is_edit_mode, ensure_edit_mode, \
    ensure_not_edit_mode


class MeshLintSelector(MeshLintObjectLooper, bpy.types.Operator):
    """Uncheck boxes below to prevent those checks form running"""
    bl_idname = "meshlint.select"
    bl_label = "MeshLint Select"
    bl_options = {'REGISTER', 'UNDO'}
    text = "Select Lint"

    @classmethod
    def poll(cls, context):
        return has_active_mesh(context)

    def execute(self, context):
        original_mode = bpy.context.mode
        if is_edit_mode():
            self.examine_all_edit_meshes()
        else:
            self.examine_all_selected_meshes()
            if self.troubled_meshes:
                ensure_edit_mode()
            elif not original_mode == 'EDIT_MESH':
                ensure_not_edit_mode()
        return {"FINISHED"}



