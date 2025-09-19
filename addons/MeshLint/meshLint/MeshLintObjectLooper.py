import bpy, bmesh

from MeshLint.addons.MeshLint.meshLint.MeshLintAnalyzer import MeshLintAnalyzer
from MeshLint.addons.MeshLint.meshLint.MeshLintStore import MeshLintStore
from MeshLint.addons.MeshLint.meshLint.utilities import ELEM_TYPES, activate, ensure_not_edit_mode, is_edit_mode

def deselect_all_elements(obj):
    """
    Deselect all vertices/edges/faces of a mesh object in Edit Mode,
    using bmesh API (works even in multi-object edit mode).
    """
    if obj.type != "MESH":
        return

    bm = bmesh.from_edit_mesh(obj.data)

    for v in bm.verts:
        v.select = False
    for e in bm.edges:
        e.select = False
    for f in bm.faces:
        f.select = False

    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)


class MeshLintObjectLooper:
    """Class providing methods to run lint checks on active and selected mesh objects in the scene."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) # For blender 4.4 onwards
        self.original_active = bpy.context.active_object
        self.troubled_meshes = []

    @staticmethod
    def examine_single_object(obj=None):
        """Conduct lint analysis of the selected object,return True if the mesh is clean."""
        if obj:
            analyzer = MeshLintAnalyzer(obj = obj)
        else:
            analyzer = MeshLintAnalyzer()
        analyzer.enable_anything_select_mode()
        deselect_all_elements(analyzer.obj)
        analysis = analyzer.find_problems()
        for lint in analysis:
            for elemtype in ELEM_TYPES:
                indices = lint[elemtype]
                analyzer.enable_anything_select_mode()
                analyzer.select_indices(elemtype, indices)
        print('select all the issues')
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # Headless Blender does not have a VIEW_3D for a redraw event.
                area.tag_redraw()       # 'NoneType' object has no attribute 'tag_redraw' when headless
        check = MeshLintAnalyzer.CHECKS
        return check, analyzer.found_zero_problems()

    def examine_all_selected_meshes(self):
        """For the current object plus all selected objects do lint analysis."""
        store = MeshLintStore()
        store.clear()
        clean = False
        if self.original_active and self.original_active not in bpy.context.selected_objects:
           examinees = [self.original_active] + bpy.context.selected_objects
        else:
            examinees = bpy.context.selected_objects
        for obj in examinees:
            if obj.type != "MESH":
                continue
            activate(obj)
            check, good = self.examine_single_object()
            store.add_counts(check)
            ensure_not_edit_mode()
            if not good:
                self.troubled_meshes.append(obj)
        priorities = examinees
        for obj in priorities:
            if obj.select_get:
                activate(obj)
                break
        if self.troubled_meshes:
            self.handle_troubled_meshes()
            clean = False
        else:
            self.handle_clean_meshes()
            clean = True
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # Headless Blender does not have a VIEW_3D for a redraw event.
                area.tag_redraw()       # 'NoneType' object has no attribute 'tag_redraw' when headless

        return clean

    def examine_all_edit_meshes(self):
        """For the all edit objects do lint analysis."""
        store = MeshLintStore()
        store.clear()
        examinees = bpy.context.objects_in_mode_unique_data
        for obj in examinees:
            if obj.type != "MESH":
                continue
            check, _ = self.examine_single_object(obj)
            store.add_counts(check)

    def handle_troubled_meshes(self):
        """Do the deselection of the troubled mesh list."""
        print('deselction happening')
        for obj in bpy.context.selected_objects:
            if obj not in self.troubled_meshes:
                obj.select_set(False)

        active = bpy.context.view_layer.objects.active
        if active not in self.troubled_meshes:
            bpy.context.view_layer.objects.active = self.troubled_meshes[0]

    def handle_clean_meshes(self):
        """Deselect all meshes."""
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
