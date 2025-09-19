import bpy

from MeshLint.addons.MeshLint.meshLint.MeshLintContinuousChecker import meshlint_gbl_continuous_check
from MeshLint.addons.MeshLint.meshLint.utilities import has_active_mesh, is_edit_mode


class MeshLintVitalizer(bpy.types.Operator):
    """Toggle the real-time execution of the checks (Edit Mode only)"""
    bl_idname = 'meshlint.live_toggle'
    bl_label = 'MeshLint Live Toggle'
    bl_options = {'REGISTER', 'UNDO'}

    is_live = False
    text = 'Continuous Check!!'
    play_pause = 'PLAY'

    @classmethod
    def poll(cls, context):
        return has_active_mesh(context) and is_edit_mode()

    def execute(self, context):
        if MeshLintVitalizer.is_live:
            bpy.app.handlers.depsgraph_update_post.remove(meshlint_gbl_continuous_check)
            MeshLintVitalizer.is_live = False
            MeshLintVitalizer.text = 'Continuous Check!'
            MeshLintVitalizer.play_pause = 'PLAY'
            for area in bpy.context.screen.areas:
                if area.type == 'INFO':
                    area.header_text_set(None)
        else:
            bpy.app.handlers.depsgraph_update_post.append(meshlint_gbl_continuous_check)
            MeshLintVitalizer.is_live = True
            MeshLintVitalizer.text = 'Pause Checking...'
            MeshLintVitalizer.play_pause = 'PAUSE'

        return {'FINISHED'}