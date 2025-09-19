import bpy
import re

from MeshLint.addons.MeshLint.meshLint.MeshLintAnalyzer import MeshLintAnalyzer
from MeshLint.addons.MeshLint.meshLint.MeshLintStore import MeshLintStore
from MeshLint.addons.MeshLint.meshLint.utilities import has_active_mesh, TBD_STR, N_A_STR, depluralize
from MeshLint.addons.MeshLint.operators.MeshLintObjectDeselector import MeshLintObjectDeselector
from MeshLint.addons.MeshLint.operators.MeshLintSelector import MeshLintSelector
from MeshLint.addons.MeshLint.operators.MeshLintVitalizer import MeshLintVitalizer
from MeshLint.common.types.framework import reg_order

class BasePanel:
    # bl_space_type = 'PROPERTIES'
    # bl_region_type = 'WINDOW'
    # bl_context = "data"

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MeshLint'

    @classmethod
    def poll(cls, context):
        return has_active_mesh(context)

@reg_order(0)
class MeshLintControlPanel(BasePanel, bpy.types.Panel):
    bl_label = "Mesh Lint"
    bl_idname = "MESH_PT_MeshLintControl"

    def draw(self, context: bpy.types.Context):
        """Pull together the three components in the side panel.
        [ The buttons ]
        [ The report result aka criticism ]
        [ The lint tick boxes for test options to enable ]
        """
        layout = self.layout
        self.add_main_buttons(layout)
        self.add_criticism(layout, context)
        self.add_toggle_buttons(layout, context)

    @staticmethod
    def add_main_buttons(layout):
        """Put the three buttons onto the side panel
        [  Select Lint  ]  [  Continuous Check  ]
        [    Deselect all Lint-free Objects     ]
        """
        split = layout.split()
        left = split.column()
        right = split.column()
        left.operator(MeshLintSelector.bl_idname, text = MeshLintSelector.text, icon = "EDITMODE_HLT")
        right.operator(MeshLintVitalizer.bl_idname, text = MeshLintVitalizer.text, icon = MeshLintVitalizer.play_pause)
        layout.split().operator(MeshLintObjectDeselector.bl_idname, text = MeshLintObjectDeselector.text, icon = "UV_ISLANDSEL")

    @staticmethod
    def add_criticism(layout, context):
        """Build the lint numerical result for each test"""
        col = layout.column()
        if not has_active_mesh(context):
            return
        total_problems = 0
        store = MeshLintStore()
        for lint in store.results:
            count = lint['count']
            if count in (TBD_STR, N_A_STR):
                label = str(count) + ' ' + f"{lint['label']}"
                reward = 'SOLO_OFF'
            elif count == 0:
                label = f'Zero {lint["label"]}!'
                reward = 'SOLO_ON'
            else:
                total_problems += count
                label = str(count) + 'x ' + f"{lint['label']}"
                label = depluralize(count = count, string = label)
                reward = 'ERROR'
            col.row().label(text = label, icon = reward)
        name_crits = MeshLintControlPanel.build_object_criticism(bpy.context.selected_objects, total_problems)
        for crit in name_crits:
            col.row().label(text = crit)

    @staticmethod
    def add_toggle_buttons(layout, context):
        """Build the tick boxes for the GUI"""
        col = layout.column()
        col.row().label(text = "MeshLint rules to include:")
        for lint in MeshLintAnalyzer.CHECKS:
            prop_name = lint['check_prop']
            label = 'Check ' + f"{lint['label']}"
            col.row().prop(context.scene, prop_name, text=label)

    @staticmethod
    def build_object_criticism(objects, total_problems):
        """Generate the criticism text for the side panel"""
        already_complained = total_problems > 0
        criticisms = []

        def add_crit(crit):
            if already_complained:
                conjunction = "and also"
            else:
                conjunction = "but"
            criticisms.append(f'...{conjunction} "{obj.name}" {crit}.')

        for obj in objects:
            if MeshLintControlPanel.has_unapplied_scale(obj.scale):
                add_crit('has an unapplied scale')
                already_complained = True
            if MeshLintControlPanel.is_bad_name(obj.name):
                add_crit('is not a great name')
                already_complained = True

        return criticisms

    @staticmethod
    def has_unapplied_scale(scale):
        """Where an object has no outstanding scale to be applied the values will be 1.0.
        This Looks at the scale of an object and determines if it is ==1.0."""
        return len([c for c in scale if c == 1.0]) != 3

    @staticmethod
    def is_bad_name(name):
        """A list of names that are default."""
        default_names = [
            'BezierCircle',
            'BezierCurve',
            'Circle',
            'Cone',
            'Cube',
            'CurvePath',
            'Cylinder',
            'Grid',
            'Icosphere',
            'Mball',
            'Monkey',
            'NurbsCircle',
            'NurbsCurve',
            'NurbsPath',
            'Plane',
            'Sphere',
            'Surface',
            'SurfCircle',
            'SurfCurve',
            'SurfCylinder',
            'SurfPatch',
            'SurfSphere',
            'SurfTorus',
            'Text',
            'Torus',
        ]
        pat = rf"{'|'.join(default_names)}\.?\d*$"
        return re.match(pat, name) is not None



