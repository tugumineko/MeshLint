from .addons.MeshLint import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": 'MeshLint',
    "author": 'Community',
    "blender": (4, 2, 0),
    "version": (0, 1, 0),
    "description": 'MeshLint is like spell-checking for your Meshes',
    "doc_url": 'https://github.com/tugumineko/MeshLint',
    "support": 'COMMUNITY',
    "category": 'Mesh'
}

def register():
    addon_register()

def unregister():
    addon_unregister()

    