import bmesh
import bpy

from MeshLint.addons.MeshLint.meshLint.utilities import ensure_edit_mode, N_A_STR, ELEM_TYPES, TBD_STR

class MeshLintAnalyzer:
    """The main branch of the application: Find the problems and define the checks"""
    CHECKS = []
    obj : bpy.types.Object
    b : bmesh.types.BMesh
    num_problems_found : int | None

    def __init__(self, *args, obj = None, **kwargs):
        super().__init__(*args, **kwargs)      #For blender 4.4 onwards
        ensure_edit_mode()
        if obj is None:
            self.obj = bpy.context.active_object
        else:
            self.obj = obj
        self.b = bmesh.from_edit_mesh(self.obj.data)
        self.num_problems_found = None

    def find_problems(self):
        """Find problems and count how many geometry elements need fixing"""
        analysis = []
        self.num_problems_found = 0
        for lint in MeshLintAnalyzer.CHECKS:
            should_check = getattr(bpy.context.scene, f"{lint['check_prop']}")
            if not should_check:
                lint['count'] = N_A_STR
                continue
            lint['count'] = 0
            check_method_name = 'check_' + f"{lint['symbol']}"
            check_method = getattr(type(self), check_method_name)
            bad = check_method(self)
            report = {'lint' : lint}
            for elemtype in ELEM_TYPES :
                indices = bad.get(elemtype, [])
                report[elemtype] = indices
                lint['count'] += len(indices)
                self.num_problems_found += len(indices)
            analysis.append(report)
        return analysis

    def found_zero_problems(self):
        return self.num_problems_found == 0

    @classmethod
    def none_analysis(cls):
        """Build an empty analysis list"""
        analysis = []
        for lint in cls.CHECKS:
            row = {elemtype : [] for elemtype in ELEM_TYPES}
            row['lint'] = lint
            analysis.append(row)
        return analysis

    CHECKS.append({
        'symbol' : 'tris',
        'label' : 'Tris',
        'definition' : 'A face with 3 edges. Often bad for modelling because it stops edge loops ' +
                       'and does not deform well around bent areas. A mesh might look good until you animate, so beware!',
        'default' : True
    })

    def check_tris(self):
        bad = {'faces' : []}
        for fff in self.b.faces:
            if len(fff.verts) == 3:
                bad['faces'].append(fff.index)
        return bad

    CHECKS.append({
        'symbol' : 'ngons',
        'label' : 'Ngons',
        'definition' : 'A face with >4 edges. Is generally bad in exactly the same way as Tris',
        'default' : True
    })

    def check_ngons(self):
        bad = {'faces' : []}
        for fff in self.b.faces:
            if len(fff.verts) > 4:
                bad['faces'].append(fff.index)
        return bad

    CHECKS.append({
        'symbol' : 'nonmanifold',
        'label' : 'Nonmanifold Elements',
        'definition' : 'Simply, shapes that won\'t hold water. ' +
                       'More precisely, non-manifold edges are those ' +
                       'that do not have exactly 2 faces attached to them (either more or less). ' +
                       'Non-manifold verts are more complicated -- you can see ' +
                       'their definition in BM_vert_is_manifold() in bmesh_queries.c',
        'default' : True
    })

    def check_nonmanifold(self):
        bad = {'faces' : []}
        for elemtype in 'verts', 'edges' :
            bad[elemtype] = []
            for elem in getattr(self.b, elemtype):
                if not elem.is_manifold:
                    bad[elemtype].append(elem.index)
        # Exempt mirror-plane verts would go in here.
        # Plus: ...anybody wanna tackle Mirrors with an Object Offset?
        return bad

    CHECKS.append({
        'symbol' : 'interior_faces',
        'label' : 'Interior Faces',
        'definition' : 'This confuses people. It is very specific: A face whose edges ALL have >2 faces attached. ' +
                       'The simplest way to see this is to Ctrl+r a Default Cube and hit \'f\'',
        'default' : True
    })

    def check_interior_faces(self):
        bad = {'faces' : []}
        for fff in self.b.faces:
            if not any(len(eee.link_faces) < 3 for eee in fff.edges):
                bad['faces'].append(fff.index)
        # geometry interior faces would not go in here.
        return bad

    CHECKS.append({
        'symbol' : 'three_poles',
        'label' : '3-edge Poles',
        'definition' : 'A vertex with 3 edges connected to it. Also known as an N-Pole',
        'default' : False
    })

    def check_three_poles(self):
        bad = {'verts' : []}
        for vvv in self.b.verts:
            if len(vvv.link_edges) == 3 :
                bad['verts'].append(vvv.index)
        return bad

    CHECKS.append({
        'symbol' : 'five_poles',
        'label' : '5-edge Poles',
        'definition' : 'A vertex with 5 edges connected to it. Also known as an E-Pole',
        'default' : False
    })

    def check_five_poles(self):
        bad = {'verts' : []}
        for vvv in self.b.verts:
            if len(vvv.link_edges) == 5 :
                bad['verts'].append(vvv.index)
        return bad

    CHECKS.append({
        'symbol' : 'sixplus_poles',
        'label' : '6+-edge Poles',
        'definition' : 'A vertex with 6 or more edges connected to it. ' +
                       'Generally this is not something you want, but since ' +
                       'some kinds of extrusions will legitimately cause such a pole ' +
                       '(imagine extruding each face of a Cube outward, ' +
                       'the inner corners are rightful 6+-poles). ' +
                       'Still, if you do not know for sure that you want them, i wart is good to enable this ',
        'default' : False
    })

    def check_sixplus_poles(self):
        bad = {'verts' : []}
        for vvv in self.b.verts:
            if len(vvv.link_edges) >= 6 :
                bad['verts'].append(vvv.index)
        return bad

    # ...any other great idea

    def  enable_anything_select_mode(self):
        """Ensure that vertex, edge, and face selection modes are all enabled."""
        self.b.select_mode = {"VERT", "EDGE", 'FACE'}

    def select_indices(self, elemtype, indices):
        """For a given element ('VERT', 'EDGE', 'FACE') then select that index """
        for inc in indices:
            match elemtype:
                case 'verts':
                    self.select_vert(inc)
                case 'edges':
                    self.select_edge(inc)
                case 'faces':
                    self.select_face(inc)
                case _:
                    print(f"MeshLint says: Huh?? → elemtype of {elemtype}.")

    # The following select methods use both self.b and temporary bm, may cause wrong...

    def select_vert(self, index):
        """Select the given VERT index in the mesh"""
        self.b.verts.ensure_lookup_table()
        self.b.verts[index].select = True

    def select_edge(self, index):
        """Select the given EDGE index in the mesh and its VERTS"""
        self.b.edges.ensure_lookup_table()
        edge = self.b.edges[index]
        edge.select = True
        for each in edge.verts:
            self.select_vert(each.index)

    def select_face(self, index):
        """Select the given FACE index in the mesh and its EDGES"""
        self.b.faces.ensure_lookup_table()
        face = self.b.faces[index]
        face.select = True
        for each in face.edges:
            self.select_edge(each.index)

    def topology_counts(self):
        """Return object data and number of faces, edges & verts"""
        return {
            'data' : self.obj.data,
            'faces' : len(self.b.faces),
            'edges' : len(self.b.edges),
            'verts' : len(self.b.verts)
        }

    for lint in CHECKS:
        lint['count'] = TBD_STR
        lint['check_prop'] = 'meshlint_check_' + f"{lint['symbol']}"
        setattr(
            bpy.types.Scene,
            f"{lint['check_prop']}",
            bpy.props.BoolProperty(
                default=lint['default'],
                description=lint['definition']
            )
        )
        if hasattr(bpy.context, 'scene'):
            # At first startup then context does not have a scene attribute
            if hasattr(bpy.context.scene, f"{lint['check_prop']}"):
                # When reloading the check_prop attribute, it might not have been created
                # If it has, then proceed with defaulting the toggles settings.
                setattr(bpy.context.scene, f"{lint['check_prop']}", lint['default'])

