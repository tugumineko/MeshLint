import copy
from MeshLint.addons.MeshLint.meshLint.utilities import TBD_STR, N_A_STR


class MeshLintStore:
    """
    Store MeshLintAnalyzer.CHECKS to display lint statistics across multiple objects.

    Aggregation semantics:
      - numeric counts are summed across objects
      - if no numeric contributions exist for a given symbol:
          * prefer TBD_STR if any TBD_STR seen
          * else prefer N_A_STR if any N_A_STR seen
          * else 0
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.results = []
            cls._instance._stats = {}
        return cls._instance

    def clear(self):
        self.results.clear()
        self._stats.clear()

    # ---------------- internal helpers ----------------
    @staticmethod
    def _is_int(v):
        return isinstance(v, int)

    @staticmethod
    def _is_na(v):
        return v == N_A_STR

    @staticmethod
    def _is_tbd(v):
        return v == TBD_STR

    @classmethod
    def _update_stats(cls, stats, value):
        """Update stats dict with a new value"""
        if cls._is_int(value):
            stats['sum'] += value
            stats['num'] += 1
        elif cls._is_na(value):
            stats['na'] += 1
        elif cls._is_tbd(value):
            stats['tbd'] += 1
        else:
            try:
                iv = int(value)
                stats['sum'] += iv
                stats['num'] += 1
            except Exception:
                pass  # ignore unknowns

    @staticmethod
    def _decide_display(stats):
        """Return the final count string/int based on stats"""
        if stats['num'] > 0:
            return stats['sum']
        if stats['tbd'] > 0:
            return TBD_STR
        if stats['na'] > 0:
            return N_A_STR
        return 0

    # ---------------- public API ----------------
    def add_counts(self, new_checks):
        if not isinstance(new_checks, list):
            raise TypeError("new_checks must be a list")

        if not self.results:  # first add
            self.results = copy.deepcopy(new_checks)
            for lint in self.results:
                s = {'sum': 0, 'num': 0, 'na': 0, 'tbd': 0}
                self._update_stats(s, lint.get('count', 0))
                lint['count'] = self._decide_display(s)
                self._stats[lint['symbol']] = s
            return

        for new_lint in new_checks:
            symbol, cnt = new_lint.get('symbol'), new_lint.get('count', 0)
            stats = self._stats.get(symbol)

            if stats is None:  # brand new symbol
                stats = {'sum': 0, 'num': 0, 'na': 0, 'tbd': 0}
                self._update_stats(stats, cnt)
                self._stats[symbol] = stats
                lint_copy = copy.deepcopy(new_lint)
                lint_copy['count'] = self._decide_display(stats)
                self.results.append(lint_copy)
                continue

            # update existing
            self._update_stats(stats, cnt)
            for lint in self.results:
                if lint.get('symbol') == symbol:
                    lint['count'] = self._decide_display(stats)
                    break
