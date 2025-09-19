from MeshLint.addons.MeshLint.meshLint.MeshLintAnalyzer import MeshLintAnalyzer
from MeshLint.addons.MeshLint.meshLint.utilities import is_edit_mode, depluralize, COMPLAINT_TIMEOUT
import time
import bpy

@bpy.app.handlers.persistent
def meshlint_gbl_continuous_check(scene, depsgraph):
    MeshLintContinuousChecker.check()

class MeshLintContinuousChecker:
    current_message = ''
    time_complained = 0
    # previous_topology_counts = None
    previous_analysis = None
    previous_data_name = None

    @classmethod
    def check(cls):
        if not is_edit_mode():
            return
        analyzer = MeshLintAnalyzer()
        now_counts = analyzer.topology_counts()
        if hasattr(cls, 'previous_topology_counts'):
            previous_topology_counts = cls.previous_topology_counts
            if previous_topology_counts is not None:
                 try:
                     if 'data' not in previous_topology_counts:
                         print('no "data" in previous topology counts')
                     if not hasattr(previous_topology_counts['data'], 'name'):
                         print('no "name" attribute')
                 except ReferenceError:
                     print('Must be "data" that did not exist')
                     print(previous_topology_counts)
        else:
            previous_topology_counts = None

        # analyzer.find_problems() # putting this here makes it run more often
        if previous_topology_counts is None or now_counts != previous_topology_counts:
            analysis = analyzer.find_problems()
            diff_msg = cls.diff_analyses(cls.previous_analysis, analysis)
            if diff_msg is not None:
                cls.announce(diff_msg)
                cls.time_complained = time.time()
            cls.previous_topology_counts = now_counts
            cls.previous_analysis = analysis

        if cls.time_complained is not None and time.time() - cls.time_complained > COMPLAINT_TIMEOUT:
            cls.announce(None)
            cls.time_complained = None

    @classmethod
    def diff_analyses(cls, before, after):
        """
        Compare two analysis results (before and after) and generate a human-readable report.
        If certain checks contain more elements in 'after' than in 'before', the differences
        are summarized and returned as a report string like
        "Found Interior Faces: 2 faces, Non Manifold: 1 edge".
        Returns None if no new issues are found.
        """
        if before is None:
            before = MeshLintAnalyzer.none_analysis()
        report_strings = []
        dict_before = cls.make_labels_dict(before)
        dict_now = cls.make_labels_dict(after)
        for check in MeshLintAnalyzer.CHECKS:
            check_name = check['label']
            if check_name not in dict_now:
                continue
            report = dict_now[check_name]
            report_before = dict_before.get(check_name, {})
            check_elem_strings = []
            for elemtype, elem_list in report.items():
                elem_list_before = report_before.get(elemtype, [])
                if len(elem_list) > len(elem_list_before):
                    count_diff = len(elem_list) - len(elem_list_before)
                    check_elem_strings.append(str(count_diff) + ' ' + depluralize(count = count_diff, string = elemtype))
            if check_elem_strings:
                report_strings.append(check_name + ': ' + ', '.join(check_elem_strings))
        if report_strings:
            return 'Found ' + "; ".join(report_strings)
        return None

    @classmethod
    def make_labels_dict(cls, analysis):
        if analysis is None:
            return {}
        labels_dict = {}
        for check in analysis:
            label = check['lint']['label']
            new_val = check.copy()
            del new_val['lint']
            labels_dict[label] = new_val
        return labels_dict

    @classmethod
    def announce(cls, message):
        """If the INFO box is open then print a message to the header area
        This is way easier than writing into that confounded box"""
        for area in bpy.context.screen.areas:
            if "INFO" != area.type:
                continue
            if message is None:
                # Passing None clears the header text;
                # skipping would leave the previous message displayed
                area.header_text_set(None)
            else:
                area.header_text_set('[MeshLint] ' + message)