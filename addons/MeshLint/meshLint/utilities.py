import bpy

# Constants

COMPLAINT_TIMEOUT = 3 # seconds
ELEM_TYPES = ['verts', 'edges', 'faces']

N_A_STR = '(N/A - disabled)'
TBD_STR = '...'

# Blender Utilities

def is_edit_mode():
    """Test if the context is edit mode"""
    # return bpy.context.mode.startswith("EDIT")
    return bpy.context.mode == 'EDIT_MESH'

def ensure_edit_mode():
    """Force the context to be edit mode"""
    if not is_edit_mode():
        bpy.ops.object.editmode_toggle()

def ensure_not_edit_mode():
    """If in edit mode, switch to object mode"""
    if is_edit_mode():
        bpy.ops.object.editmode_toggle()

def has_active_mesh(context):
    """Return a bool of the active object being a mesh"""
    obj = context.active_object
    return obj and obj.type == 'MESH'

def activate(obj):
    """Set the given object as the active object in the current view layer."""
    bpy.context.view_layer.objects.active = obj

# Python Utilities

def depluralize(**args):
    """Singular of things is thing, this just knocks off the s at the end of a string."""
    if args['count'] == 1:
        return args['string'].rstrip('s')
    return args['string']