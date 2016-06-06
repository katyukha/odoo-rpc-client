import unittest

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2


# based on: https://gist.github.com/minrk/2620876
import os
import sys
import os.path
import nbformat
from nbformat.v4 import output_from_msg
from jupyter_client.manager import start_new_kernel


PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..',))


class CellExecuteError(Exception):
    """ Cell execution error
    """
    pass


class NBRunner(object):
    """ Runs test for a single notebook

        Tests each cell of type code
    """
    def __init__(self, nb, timeout=30, debug=False, name=None):
        self.nb = nb
        self.km = None
        self.kc = None
        self.timeout = timeout
        self.debug = debug
        self.failures = 0
        self.cells_processed = 0
        self.outputs = None
        self.name = name

    @property
    def ok(self):
        """ Return True if all cells processed successfully
        """
        return self.cells_processed > 0 and self.failures == 0

    @property
    def failed(self):
        """ Return True if at leas one cell failed
        """
        return self.failures > 0

    def start_kernel(self):
        """ Start IPython kernel
        """
        self.km, self.kc = start_new_kernel(
            # kernel_name=kernel_name,
            # extra_arguments=self.extra_arguments,
            stderr=open(os.devnull, 'w'),
            cwd=os.getcwd())
        self.kc.allow_stdin = False

    def stop_kernel(self):
        """ Stop IPython kernel
        """
        self.kc.stop_channels()
        self.km.shutdown_kernel(now=True)
        self.km = None
        self.kc = None

    def log(self, *args, **kwargs):
        """ Simply print all arga and keyword args
        """
        print(args, kwargs)

    def log_debug(self, *args, **kwargs):
        """ Same as *log*, but prints only if debug set to True
        """
        if self.debug:
            print(args, kwargs)

    def log_failure(self, cell, exc):
        """ Print's failure
            (including traceback)

            also increments failure count
        """
        self.failures += 1
        print("\nFAILURE:")
        print(cell.source)
        print('\n------------\n')
        print('raised:\n\t%s' % str(exc))

    def log_cell_processed(self, cell):
        """ Print that cell processed successfully

            just prints '.' to stdout
        """
        self.cells_processed += 1
        sys.stdout.write(' * ')

    def handle_iopub_for_msg(self, cell, msg_id):
        """ Process additional data sent by kernel
            (output, ...)
        """
        outs = []

        while True:
            try:
                msg = self.kc.iopub_channel.get_msg(timeout=self.timeout)
            except Empty:
                self.log("Timeout waiting for IOPub output")
                break
            if msg['parent_header'].get('msg_id') != msg_id:
                # not an output from our execution
                continue

            msg_type = msg['msg_type']
            content = msg['content']

            # set the prompt number for the input and the output
            if cell and 'execution_count' in content:
                cell['execution_count'] = content['execution_count']

            if msg_type == 'status':
                if content['execution_state'] == 'idle':
                    break
                else:
                    continue
            elif msg_type == 'execute_input':
                continue
            elif msg_type == 'clear_output':
                outs = []
                continue
            elif msg_type.startswith('comm'):
                continue

            try:
                out = output_from_msg(msg)
            except ValueError:
                self.log("unhandled iopub msg: " + msg_type)
            else:
                self.log_debug("output: %s" % out)
                outs.append(out)

        return outs

    def run_cell(self, cell):
        """ Run cell. Send cell's source to kernel, and process result
        """
        msg_id = self.kc.execute(cell.source)
        self.log_debug("Executing cell:\n%s", cell.source)
        # wait for finish, with timeout
        while True:
            try:
                msg = self.kc.get_shell_msg(timeout=self.timeout)
            except Empty:
                self.log("""Timeout waiting for execute reply (%is).
                """ % self.timeout)
                self.log("Interrupting kernel.\nCell:\n%s\n\n---\n\n)"
                         "" % cell.source)
                self.km.interrupt_kernel()
                raise

            if msg['parent_header'].get('msg_id') == msg_id:
                if msg['metadata']['status'] == 'error':
                    raise CellExecuteError(
                        '\n\n'.join(msg['content']['traceback']))
                else:
                    break
            else:
                # not our reply
                continue
        return self.handle_iopub_for_msg(cell, msg_id)

    def inspect_cell(self, cell):
        # inspect code
        msg_id = self.kc.inspect(cell.source)
        return self.handle_iopub_for_msg(cell, msg_id)

    def _prepare_run(self):
        # enable coverage:
        self.kc.execute(
            "import sys, os, coverage;\n"
            "_coverage = coverage.coverage("
            "    data_suffix='%s-ipython' % os.getpid());\n"
            "_coverage.start();\n"
        )

        reply = self.kc.get_shell_msg(timeout=20)['content']
        if reply['status'] == 'error':
            print("\nERROR: cannot run coverage support")
            print('-----')
            print("raised:")
            print('\n'.join(reply['traceback']))
            raise Exception("Cannot run coverage support",
                            reply['traceback'])

        self.failures = 0
        self.cells_processed = 0

    def _finish_run(self):
        # save coverage:
        self.kc.execute("_coverage.stop(); _coverage.save()\n")

        reply = self.kc.get_shell_msg(timeout=20)['content']
        if reply['status'] == 'error':
            print("\nERROR: cannot finish coverage support")
            print('-----')
            print("raised:")
            print('\n'.join(reply['traceback']))
            raise Exception("Cannot finish coverage support",
                            reply['traceback'])

    def run_notebook(self):
        """ Run tests for all cells
        """
        self._prepare_run()

        self.outputs = []
        for cell in self.nb.cells:
            if cell.cell_type != 'code':
                continue

            try:
                outs = self.run_cell(cell)
            except CellExecuteError as e:
                outs = False
                self.log_failure(cell, e)
                raise
            self.outputs.append(outs)

            self.log_cell_processed(cell)

        self._finish_run()
        return self

    def print_run_result(self):
        print()
        print("ran notebook %s" % self.name)
        print("    ran %3i cells" % self.cells_processed)
        if self.failures:
            print("    %3i cells raised exceptions" % self.failures)

        return self

    def run(self):
        """ start kernel, run tests and stop kernel after
        """
        self.start_kernel()
        res = self.run_notebook()
        self.stop_kernel()
        return res


class NBMultiRunner(object):
    """ Class to test multiple notebooks at same time
    """
    def __init__(self, notebook_paths, timeout=40, debug=False):
        self.notebook_paths = notebook_paths
        self.notebooks = []
        self.failures = 0
        self.processed = 0
        self.timeout = timeout
        self.debug = debug

    @property
    def ok(self):
        """ True all notebooks processed successfully
        """
        return self.processed > 0 and self.failures == 0

    @property
    def failed(self):
        """ Return True if atleast one notebook failed
        """
        return self.failures > 0

    def run(self):
        """ Run test all notebooks
        """
        for ipynb in self.notebook_paths:
            nb_name = os.path.split(ipynb)[-1]
            nb = nbformat.read(ipynb, 4)
            rnb = NBRunner(nb,
                           timeout=self.timeout,
                           debug=self.debug,
                           name=nb_name)
            rnb.run().print_run_result()

            # save results
            self.notebooks.append(rnb)
            self.failures += int(rnb.failed)
            self.processed += 1

        return self


@unittest.skipUnless(os.environ.get('TEST_WITH_EXTENSIONS', False),
                     'requires extensions enabled')
class Test_40_IPYNB(unittest.TestCase):

    # list of paths of notebooks to run
    notebooks_to_run = [
        os.path.join(PROJECT_DIR, 'examples', 'Examples & HTML tests.ipynb'),
        os.path.join(PROJECT_DIR, 'examples',
                     'RecordList Representation.ipynb'),
    ]

    def setUp(self):
        super(Test_40_IPYNB, self).setUp()

    def test_run_notebooks(self):
        runner = NBMultiRunner(self.notebooks_to_run)
        runner.run()

        if runner.failed:
            raise AssertionError("At least one of tested notebooks "
                                 "have some errors")


class Test_41_IPYNB(unittest.TestCase):

    # list of paths of notebooks to run
    notebooks_to_run = [
        os.path.join(PROJECT_DIR, 'examples', 'Basics.ipynb'),
    ]

    def setUp(self):
        super(Test_41_IPYNB, self).setUp()

    def test_run_notebooks(self):
        runner = NBMultiRunner(self.notebooks_to_run)
        runner.run()

        if runner.failed:
            raise AssertionError("At leas one of tested notebooks "
                                 "have some errors")
